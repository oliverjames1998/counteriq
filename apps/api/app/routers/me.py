from fastapi import APIRouter, Depends
from ..auth import CurrentUser, require_user

router = APIRouter(prefix="/api", tags=["me"])


@router.get("/me")
def get_me(user: CurrentUser = Depends(require_user)) -> dict:
    return {"id": user.id, "email": user.email, "role": user.role}
