from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth import CurrentUser, require_user
from ..db import admin_client
from ..models import EventOut
from .stores import _user_can_access_store

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[EventOut])
def list_events(
    store_id: str = Query(...),
    type: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    media_type: Optional[str] = Query(default=None),
    camera_id: Optional[str] = Query(default=None),
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    user: CurrentUser = Depends(require_user),
) -> list[EventOut]:
    if not _user_can_access_store(user.id, store_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not a member of this store")

    q = admin_client().table("events").select("*").eq("store_id", store_id)
    if type:
        q = q.eq("type", type)
    if status_filter:
        q = q.eq("status", status_filter)
    if media_type:
        q = q.eq("media_type", media_type)
    if camera_id:
        q = q.eq("camera_id", camera_id)
    if from_:
        q = q.gte("started_at", from_.isoformat())
    if to:
        q = q.lte("started_at", to.isoformat())

    res = q.order("started_at", desc=True).limit(limit).execute()
    return [EventOut(**row) for row in (res.data or [])]
