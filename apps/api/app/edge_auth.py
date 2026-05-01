"""Edge device authentication via X-Edge-Key header.

Edge devices are issued an opaque API key at pairing time. Only its sha256
hash (peppered) is stored in `edge_devices.api_key_hash`. On each request we
hash the presented header and look it up.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from .config import Settings, get_settings
from .db import admin_client


@dataclass
class EdgeDevice:
    id: str
    store_id: str


def hash_edge_key(raw: str, pepper: str) -> str:
    return hashlib.sha256(f"{pepper}::{raw}".encode("utf-8")).hexdigest()


def require_edge(
    x_edge_key: Optional[str] = Header(default=None, alias="X-Edge-Key"),
    settings: Settings = Depends(get_settings),
) -> EdgeDevice:
    if not x_edge_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing X-Edge-Key")

    h = hash_edge_key(x_edge_key, settings.EDGE_KEY_PEPPER)
    res = admin_client().table("edge_devices").select("id,store_id").eq("api_key_hash", h).limit(1).execute()
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid edge key")
    return EdgeDevice(id=rows[0]["id"], store_id=rows[0]["store_id"])
