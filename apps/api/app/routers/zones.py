"""Zones router. JWT pass-through; RLS handles tenancy."""
from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import CurrentUser, require_user
from ..db import user_get, user_post
from ..models import ZoneCreate, ZoneOut

router = APIRouter(prefix="/api", tags=["zones"])


@router.post("/zones", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
def create_zone(payload: ZoneCreate, user: CurrentUser = Depends(require_user)) -> ZoneOut:
    cam = user_get("cameras", user.jwt, params={"id": f"eq.{payload.camera_id}", "select": "store_id", "limit": 1})
    if cam.status_code >= 400:
        raise HTTPException(status_code=cam.status_code, detail=cam.text)
    rows = cam.json()
    if not rows:
        raise HTTPException(status_code=404, detail="camera not found or not accessible")
    store_id = rows[0]["store_id"]

    r = user_post(
        "zones",
        user.jwt,
        {
            "camera_id": payload.camera_id,
            "store_id": store_id,
            "type": payload.type,
            "label": payload.label,
            "polygon": payload.polygon,
        },
    )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    out = r.json()
    if not out:
        raise HTTPException(status_code=500, detail="zone insert returned no rows")
    return ZoneOut(**out[0])


@router.get("/cameras/{camera_id}/zones", response_model=list[ZoneOut])
def list_zones_for_camera(camera_id: str, user: CurrentUser = Depends(require_user)) -> list[ZoneOut]:
    r = user_get("zones", user.jwt, params={"camera_id": f"eq.{camera_id}", "select": "*"})
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return [ZoneOut(**row) for row in r.json()]
