from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import CurrentUser, require_user
from ..db import user_get
from ..models import EventOut

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
    params: dict[str, str] = {
        "store_id": f"eq.{store_id}",
        "select": "*",
        "order": "started_at.desc",
        "limit": str(limit),
    }
    if type:
        params["type"] = f"eq.{type}"
    if status_filter:
        params["status"] = f"eq.{status_filter}"
    if media_type:
        params["media_type"] = f"eq.{media_type}"
    if camera_id:
        params["camera_id"] = f"eq.{camera_id}"
    if from_:
        params["started_at"] = f"gte.{from_.isoformat()}"
    if to:
        params.setdefault("started_at", f"lte.{to.isoformat()}")

    r = user_get("events", user.jwt, params=params)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return [EventOut(**row) for row in r.json()]
