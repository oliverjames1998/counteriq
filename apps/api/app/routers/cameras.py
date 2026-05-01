"""Cameras: RTSP probe + create.

RTSP credentials are encrypted at rest with pgcrypto + a per-store key.
We invoke `crypt_using_pgcrypto()` via a Postgres RPC named `encrypt_rtsp_url`
that the schema migration provides. Until that RPC is wired, we store the
URL verbatim in the encrypted column as a placeholder — TODO before pilot.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import CurrentUser, require_user
from ..db import admin_client
from ..models import CameraCreate, CameraOut, CameraTestRequest, CameraTestResponse
from ..util.rtsp_probe import probe_rtsp
from .stores import _user_can_access_store

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


@router.post("/test", response_model=CameraTestResponse)
def test_camera(payload: CameraTestRequest, user: CurrentUser = Depends(require_user)) -> CameraTestResponse:
    """Probe an RTSP URL. Audio is never opened (-an enforced in probe_rtsp).
    Returns one still frame as base64 plus audio_supported (informational)."""
    result = probe_rtsp(payload.rtsp_url)
    return CameraTestResponse(
        ok=result.ok,
        audio_supported=result.audio_supported,
        resolution=result.resolution,
        frame_jpeg_b64=result.frame_jpeg_b64,
        error=result.error,
    )


@router.post("", response_model=CameraOut, status_code=status.HTTP_201_CREATED)
def create_camera(payload: CameraCreate, user: CurrentUser = Depends(require_user)) -> CameraOut:
    if not _user_can_access_store(user.id, payload.store_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not a member of this store")

    res = (
        admin_client()
        .table("cameras")
        .insert(
            {
                "store_id": payload.store_id,
                "label": payload.label,
                "location": payload.location,
                "rtsp_url_encrypted": payload.rtsp_url,
            }
        )
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=500, detail="failed to create camera")
    return CameraOut(**res.data[0])
