"""Edge ingestion endpoints.

Auth model:
- Edge agent presents its X-Edge-Key on every call.
- The FastAPI is stateless w.r.t. the device — it forwards directly to
  Supabase RPCs (`claim_edge_device`, `ingest_edge_event`) which validate
  the key against the sha256 hash stored in `edge_devices.api_key_hash`.
- No service-role privileges held in the FastAPI process.

Two endpoints:
- POST /api/edge/claim   — first-boot pairing token swap → returns api_key
- POST /api/edge/events  — ongoing event ingestion (X-Edge-Key required)
"""
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from ..db import anon_rpc
from ..models import EdgeEventBatch

router = APIRouter(prefix="/api/edge", tags=["edge"])


class EdgeClaimRequest(BaseModel):
    pairing_token: str
    device_label: Optional[str] = None
    device_version: Optional[str] = None


class EdgeClaimResponse(BaseModel):
    device_id: str
    api_key: str
    store_id: str


@router.post("/claim", response_model=EdgeClaimResponse)
def claim_device(payload: EdgeClaimRequest) -> EdgeClaimResponse:
    """Swap a one-time pairing_token for a long-lived api_key.

    The owner provisions an `edge_devices` row with `pairing_token`. On first
    boot, the device calls this endpoint, the RPC validates the token, swaps
    it for an api_key, stores only the sha256 hash, and returns the raw
    api_key once. The device persists the api_key locally; the server can
    never recover it (only verify).
    """
    r = anon_rpc(
        "claim_edge_device",
        {
            "p_pairing_token": payload.pairing_token,
            "p_device_label": payload.device_label,
            "p_device_version": payload.device_version,
        },
    )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    data = r.json()
    # RPCs that return a single row are returned as a JSON object directly,
    # but PostgREST may wrap as a list — handle both.
    if isinstance(data, list):
        data = data[0] if data else {}
    if not data or "api_key" not in data:
        raise HTTPException(status_code=502, detail="claim RPC returned no api_key")
    return EdgeClaimResponse(
        device_id=str(data["device_id"]),
        api_key=str(data["api_key"]),
        store_id=str(data["store_id"]),
    )


@router.post("/events")
def post_edge_events(
    batch: EdgeEventBatch,
    x_edge_key: Optional[str] = Header(default=None, alias="X-Edge-Key"),
) -> dict:
    """Ingest up to 100 events from a paired edge device.

    The X-Edge-Key is forwarded to the `ingest_edge_events` RPC which
    verifies the sha256 hash, looks up the device's store_id, and inserts
    the events with that scope. The FastAPI never sees the device's
    store_id directly — the RPC enforces it.
    """
    if not x_edge_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing X-Edge-Key")

    payload_events = [
        {
            "camera_id": ev.camera_id,
            "type": ev.type,
            "started_at": ev.started_at.isoformat(),
            "ended_at": ev.ended_at.isoformat() if ev.ended_at else None,
            "confidence": ev.confidence,
            "severity": ev.severity,
            "metadata": ev.metadata,
        }
        for ev in batch.events
    ]

    r = anon_rpc("ingest_edge_events", {"p_api_key": x_edge_key, "p_events": payload_events})
    if r.status_code == 401 or r.status_code == 403:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid edge key")
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    data = r.json()
    return {"inserted": data if isinstance(data, int) else len(payload_events)}
