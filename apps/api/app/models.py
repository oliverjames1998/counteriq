from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class StoreCreate(BaseModel):
    name: str
    address: Optional[str] = None
    timezone: str = "America/Chicago"
    business_hours: dict[str, Any] = Field(default_factory=dict)


class StoreOut(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    timezone: str
    plan_tier: str
    created_at: datetime


class CameraTestRequest(BaseModel):
    rtsp_url: str


class CameraTestResponse(BaseModel):
    ok: bool
    audio_supported: bool
    resolution: Optional[str] = None
    frame_jpeg_b64: Optional[str] = None
    error: Optional[str] = None


class CameraCreate(BaseModel):
    store_id: str
    label: str
    location: str = "other"
    rtsp_url: str


class CameraOut(BaseModel):
    id: str
    store_id: str
    label: str
    location: str
    status: str
    audio_supported: bool
    audio_enabled: bool


class ZoneCreate(BaseModel):
    camera_id: str
    type: str
    label: Optional[str] = None
    polygon: list[list[float]]


class ZoneOut(BaseModel):
    id: str
    camera_id: str
    type: str
    label: Optional[str]
    polygon: Any


class EventIn(BaseModel):
    camera_id: str
    type: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    confidence: float = 0.0
    severity: str = "info"
    metadata: dict[str, Any] = Field(default_factory=dict)


class EdgeEventBatch(BaseModel):
    events: list[EventIn] = Field(min_length=1, max_length=100)


class EventOut(BaseModel):
    id: str
    store_id: str
    camera_id: str
    type: str
    started_at: datetime
    severity: str
    status: str
    media_type: str
    confidence: float
