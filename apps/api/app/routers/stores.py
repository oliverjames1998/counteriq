"""Stores router. Uses JWT pass-through — RLS scopes every query to the
caller's stores via the existing supabase.com policies on `stores` and
`store_users`.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import CurrentUser, require_user
from ..db import user_get, user_post
from ..models import StoreCreate, StoreOut

router = APIRouter(prefix="/api/stores", tags=["stores"])


@router.post("", response_model=StoreOut, status_code=status.HTTP_201_CREATED)
def create_store(payload: StoreCreate, user: CurrentUser = Depends(require_user)) -> StoreOut:
    body = {
        "owner_id": user.id,
        "name": payload.name,
        "address": payload.address,
        "timezone": payload.timezone,
        "business_hours": payload.business_hours,
    }
    r = user_post("stores", user.jwt, body)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    rows = r.json()
    if not rows:
        raise HTTPException(status_code=500, detail="store insert returned no rows")
    store = rows[0]
    membership = user_post(
        "store_users",
        user.jwt,
        {"store_id": store["id"], "user_id": user.id, "role": "owner"},
    )
    if membership.status_code >= 400:
        raise HTTPException(status_code=membership.status_code, detail=membership.text)
    return StoreOut(**store)


@router.get("", response_model=list[StoreOut])
def list_stores(user: CurrentUser = Depends(require_user)) -> list[StoreOut]:
    r = user_get(
        "stores",
        user.jwt,
        params={"select": "*", "deleted_at": "is.null"},
    )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return [StoreOut(**row) for row in r.json()]


@router.get("/{store_id}", response_model=StoreOut)
def get_store(store_id: str, user: CurrentUser = Depends(require_user)) -> StoreOut:
    r = user_get("stores", user.jwt, params={"id": f"eq.{store_id}", "select": "*", "limit": 1})
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    rows = r.json()
    if not rows:
        raise HTTPException(status_code=404, detail="store not found or not accessible")
    return StoreOut(**rows[0])
