"""Edge agent config loader.

Reads JSON from --config <path>. Validates with pydantic. Persists the
device's api_key to a sibling file so subsequent boots skip pairing.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class CameraCfg(BaseModel):
    camera_id: str
    label: str
    rtsp_url: str
    counter_polygon: list[list[float]] = Field(
        default_factory=list,
        description="List of [x, y] pairs in 0..1 normalized image coordinates",
    )
    sample_every_n_frames: int = 6


class BusinessHoursCfg(BaseModel):
    mon: dict[str, Any] = Field(default_factory=lambda: {"open": "09:00", "close": "21:00", "closed": False})
    tue: dict[str, Any] = Field(default_factory=lambda: {"open": "09:00", "close": "21:00", "closed": False})
    wed: dict[str, Any] = Field(default_factory=lambda: {"open": "09:00", "close": "21:00", "closed": False})
    thu: dict[str, Any] = Field(default_factory=lambda: {"open": "09:00", "close": "21:00", "closed": False})
    fri: dict[str, Any] = Field(default_factory=lambda: {"open": "09:00", "close": "22:00", "closed": False})
    sat: dict[str, Any] = Field(default_factory=lambda: {"open": "10:00", "close": "22:00", "closed": False})
    sun: dict[str, Any] = Field(default_factory=lambda: {"open": "10:00", "close": "20:00", "closed": False})


class EdgeConfig(BaseModel):
    api_base_url: str = "https://counteriq-api.fly.dev"
    pairing_token: Optional[str] = None
    api_key_file: str = "./api_key.txt"
    state_db: str = "./events.sqlite"
    cameras: list[CameraCfg]
    business_hours: BusinessHoursCfg = Field(default_factory=BusinessHoursCfg)
    sim_mode: bool = Field(
        default=False,
        description="If true, use a webcam or video file instead of RTSP — useful for dev without a Jetson",
    )
    sim_source: str = "0"  # cv2.VideoCapture argument when sim_mode=true
    heartbeat_interval_s: int = 30
    sync_interval_s: int = 10

    @classmethod
    def load(cls, path: str) -> "EdgeConfig":
        text = Path(path).read_text()
        return cls.model_validate(json.loads(text))


def load_or_pair_api_key(cfg: EdgeConfig) -> str:
    """Read the persisted api_key, or perform a one-time pairing if absent."""
    p = Path(cfg.api_key_file)
    if p.exists():
        key = p.read_text().strip()
        if key:
            return key
    if not cfg.pairing_token:
        raise RuntimeError(
            "no api_key on disk and no pairing_token in config — provision an "
            "edge_devices row in Supabase, copy the pairing_token into config.json, "
            "and restart"
        )

    import httpx

    r = httpx.post(
        f"{cfg.api_base_url.rstrip('/')}/api/edge/claim",
        json={"pairing_token": cfg.pairing_token, "device_label": os.uname().nodename if hasattr(os, "uname") else None, "device_version": "edge-agent-0.1.0"},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    p.write_text(data["api_key"])
    p.chmod(0o600)
    return data["api_key"]
