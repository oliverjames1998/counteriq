"""Edge ingestion endpoints. Authed via X-Edge-Key (sha256-hashed in DB)."""
from fastapi import APIRouter, Depends, HTTPException

from ..db import admin_client
from ..edge_auth import EdgeDevice, require_edge
from ..models import EdgeEventBatch

router = APIRouter(prefix="/api/edge", tags=["edge"])


@router.post("/events")
def post_edge_events(batch: EdgeEventBatch, device: EdgeDevice = Depends(require_edge)) -> dict:
    """Accept up to 100 events from an edge device. All events are forced to
    the device's own store_id — the device cannot post into other stores."""
    sb = admin_client()
    rows = []
    for ev in batch.events:
        rows.append(
            {
                "store_id": device.store_id,
                "camera_id": ev.camera_id,
                "type": ev.type,
                "started_at": ev.started_at.isoformat(),
                "ended_at": ev.ended_at.isoformat() if ev.ended_at else None,
                "confidence": ev.confidence,
                "severity": ev.severity,
                "metadata": ev.metadata,
            }
        )
    res = sb.table("events").insert(rows).execute()
    if res.data is None:
        raise HTTPException(status_code=500, detail="event insert failed")
    return {"inserted": len(res.data)}
