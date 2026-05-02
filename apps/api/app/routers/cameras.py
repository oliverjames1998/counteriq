"""Cameras router. JWT pass-through; RLS controls access."""
from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import CurrentUser, require_user
from ..db import user_post
from ..models import CameraCreate, CameraOut, CameraTestRequest, CameraTestResponse
from ..util.rtsp_probe import probe_rtsp

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


@router.post("/test", response_model=CameraTestResponse)
def test_camera(payload: CameraTestRequest, user: CurrentUser = Depends(require_user)) -> CameraTestResponse:
    """Probe an RTSP URL. ffmpeg is invoked with `-an` (audio disabled),
    enforced inside util/rtsp_probe.probe_rtsp."""
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
    body = {
        "store_id": payload.store_id,
        "label": payload.label,
        "location": payload.location,
        # NOTE: rtsp_url stored as-is in this scaffold. Production: pgcrypto
        # column-level encryption via a dedicated `set_camera_rtsp` RPC.
        "rtsp_url_encrypted": payload.rtsp_url,
    }
    r = user_post("cameras", user.jwt, body)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    rows = r.json()
    if not rows:
        raise HTTPException(status_code=500, detail="camera insert returned no rows")
    return CameraOut(**rows[0])
