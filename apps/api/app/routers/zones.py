from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import CurrentUser, require_user
from ..db import admin_client
from ..models import ZoneCreate, ZoneOut
from .stores import _user_can_access_store

router = APIRouter(prefix="/api", tags=["zones"])


def _camera_store_id(camera_id: str) -> str | None:
    res = admin_client().table("cameras").select("store_id").eq("id", camera_id).limit(1).execute()
    return res.data[0]["store_id"] if res.data else None


@router.post("/zones", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
def create_zone(payload: ZoneCreate, user: CurrentUser = Depends(require_user)) -> ZoneOut:
    store_id = _camera_store_id(payload.camera_id)
    if store_id is None:
        raise HTTPException(status_code=404, detail="camera not found")
    if not _user_can_access_store(user.id, store_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not a member of this store")

    res = (
        admin_client()
        .table("zones")
        .insert(
            {
                "camera_id": payload.camera_id,
                "store_id": store_id,
                "type": payload.type,
                "label": payload.label,
                "polygon": payload.polygon,
            }
        )
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=500, detail="failed to create zone")
    return ZoneOut(**res.data[0])


@router.get("/cameras/{camera_id}/zones", response_model=list[ZoneOut])
def list_zones_for_camera(camera_id: str, user: CurrentUser = Depends(require_user)) -> list[ZoneOut]:
    store_id = _camera_store_id(camera_id)
    if store_id is None:
        raise HTTPException(status_code=404, detail="camera not found")
    if not _user_can_access_store(user.id, store_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not a member of this store")

    res = admin_client().table("zones").select("*").eq("camera_id", camera_id).execute()
    return [ZoneOut(**row) for row in (res.data or [])]
