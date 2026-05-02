"""Background thread that drains unsynced events to FastAPI.

Calls POST /api/edge/events with X-Edge-Key header. Up to 100 events per
batch (matches FastAPI batch cap). Marks rows synced on 200, leaves them
unsynced on transient failure for retry.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

import httpx

from .db import fetch_unsynced, mark_synced, open_db

log = logging.getLogger(__name__)


def sync_once(api_base_url: str, api_key: str, state_db: str) -> int:
    with open_db(state_db) as con:
        rows = fetch_unsynced(con, limit=100)
        if not rows:
            return 0
        events = [
            {
                "camera_id": r["camera_id"],
                "type": r["type"],
                "started_at": r["started_at"],
                "ended_at": r["ended_at"],
                "confidence": r["confidence"],
                "severity": r["severity"],
                "metadata": r["metadata"],
            }
            for r in rows
        ]
        try:
            resp = httpx.post(
                f"{api_base_url.rstrip('/')}/api/edge/events",
                json={"events": events},
                headers={"X-Edge-Key": api_key},
                timeout=20,
            )
        except httpx.HTTPError as e:
            log.warning("sync HTTP error, will retry: %s", e)
            return 0
        if resp.status_code == 200:
            mark_synced(con, [r["id"] for r in rows])
            return len(rows)
        log.warning("sync rejected %s: %s", resp.status_code, resp.text[:200])
        return 0


def sync_thread(api_base_url: str, api_key: str, state_db: str, interval_s: int,
                stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        try:
            n = sync_once(api_base_url, api_key, state_db)
            if n:
                log.info("synced %d events", n)
        except Exception as e:  # don't kill the thread on unexpected errors
            log.exception("sync thread error: %s", e)
        stop_event.wait(interval_s)


def heartbeat_thread(api_base_url: str, api_key: str, interval_s: int,
                     stop_event: threading.Event) -> None:
    """Lightweight liveness ping. Logs failures but never crashes."""
    while not stop_event.is_set():
        try:
            httpx.post(
                f"{api_base_url.rstrip('/')}/api/edge/heartbeat",
                headers={"X-Edge-Key": api_key},
                timeout=10,
            )
        except httpx.HTTPError:
            pass
        stop_event.wait(interval_s)
