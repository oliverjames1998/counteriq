from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import CurrentUser, require_user
from ..db import admin_client
from ..models import StoreCreate, StoreOut

router = APIRouter(prefix="/api/stores", tags=["stores"])


def _user_can_access_store(user_id: str, store_id: str) -> bool:
    res = (
        admin_client()
        .table("store_users")
        .select("role")
        .eq("store_id", store_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return bool(res.data)


@router.post("", response_model=StoreOut, status_code=status.HTTP_201_CREATED)
def create_store(payload: StoreCreate, user: CurrentUser = Depends(require_user)) -> StoreOut:
    sb = admin_client()
    store_res = (
        sb.table("stores")
        .insert(
            {
                "owner_id": user.id,
                "name": payload.name,
                "address": payload.address,
                "timezone": payload.timezone,
                "business_hours": payload.business_hours,
            }
        )
        .execute()
    )
    if not store_res.data:
        raise HTTPException(status_code=500, detail="failed to create store")
    store = store_res.data[0]
    sb.table("store_users").insert(
        {"store_id": store["id"], "user_id": user.id, "role": "owner"}
    ).execute()
    return StoreOut(**store)


@router.get("", response_model=list[StoreOut])
def list_stores(user: CurrentUser = Depends(require_user)) -> list[StoreOut]:
    sb = admin_client()
    memberships = sb.table("store_users").select("store_id").eq("user_id", user.id).execute()
    ids = [m["store_id"] for m in (memberships.data or [])]
    if not ids:
        return []
    res = sb.table("stores").select("*").in_("id", ids).is_("deleted_at", "null").execute()
    return [StoreOut(**row) for row in (res.data or [])]


@router.get("/{store_id}", response_model=StoreOut)
def get_store(store_id: str, user: CurrentUser = Depends(require_user)) -> StoreOut:
    if not _user_can_access_store(user.id, store_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not a member of this store")
    res = admin_client().table("stores").select("*").eq("id", store_id).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="store not found")
    return StoreOut(**res.data[0])
