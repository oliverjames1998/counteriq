"""Entrance tripwire counter — counts people entering and exiting.

Watches a single RTSP stream pointed at the storefront door. Each detected
person is tracked across frames. When a person's foot-point crosses the
configured tripwire line, an 'entry' or 'exit' event is emitted (direction
determined by which side of the line they came from).

Config shape (per camera, in config.json):
{
  "camera_id": "...",
  "label": "Front Door",
  "role": "entrance",
  "rtsp_url": "rtsp://...",
  "tripwire_line": [[0.05, 0.50], [0.95, 0.55]],
  "tripwire_inside_side": "below",   // "above" | "below" — which side = inside the store
  "sample_every_n_frames": 4
}

Privacy contract is identical to detector.py:
- ffmpeg `an;1` audio disabled
- Person detection only
- ByteTrack reset every 4 hours
- No FR, no STT, no demographic, no emotion
"""
from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import cv2

from .config import CameraCfg, EdgeConfig
from .db import insert_event

log = logging.getLogger(__name__)

TRACK_RESET_S = 4 * 3600
PER_TRACK_COOLDOWN_S = 6.0          # don't double-fire the same track
MIN_TRACK_FRAMES_BEFORE_FIRE = 3    # avoid spurious one-frame detections
CLIP_DURATION_S = 10


# ---------- geometry ----------

def _side_of_line(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> int:
    """Return +1, -1, or 0 indicating which side of the line (x1,y1)-(x2,y2)
    the point (px, py) is on. 0 == on the line."""
    cross = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
    if cross > 0:
        return 1
    if cross < 0:
        return -1
    return 0


def _inside_sign(inside_side: str, line: list[list[float]]) -> int:
    """Map 'above'/'below'/'left'/'right' to a sign for the cross product.
    Image coordinates: y increases downward, x increases rightward.

    For a roughly-horizontal tripwire (x1<x2), points "above" (smaller y)
    have negative cross when the line goes left-to-right. Mapping:
      above  -> -1
      below  -> +1
    For a roughly-vertical tripwire (y1<y2):
      left   -> -1
      right  -> +1
    """
    s = inside_side.lower()
    if s in ("above", "left"):
        return -1
    return 1  # below / right / anything else defaults to +1


# ---------- capture (mirrors detector.py) ----------

def _open_capture(cam: CameraCfg, sim_mode: bool, sim_source: str) -> cv2.VideoCapture:
    if sim_mode:
        try:
            return cv2.VideoCapture(int(sim_source))
        except ValueError:
            return cv2.VideoCapture(sim_source)
    os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp|an;1")
    return cv2.VideoCapture(cam.rtsp_url)


# ---------- main loop ----------

def run_entrance_camera(
    cam: CameraCfg,
    cfg: EdgeConfig,
    db_path: str,
    stop_event: threading.Event,
) -> None:
    if not cam.tripwire_line or len(cam.tripwire_line) != 2:
        log.error("[%s] entrance camera missing tripwire_line — skipping", cam.label)
        return

    log.info("[%s] starting ENTRANCE capture (sim_mode=%s)", cam.label, cfg.sim_mode)
    cap = _open_capture(cam, cfg.sim_mode, cfg.sim_source)
    if not cap.isOpened():
        log.error("[%s] could not open source", cam.label)
        return

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
    log.info("[%s] resolution: %dx%d", cam.label, w, h)

    (nx1, ny1), (nx2, ny2) = cam.tripwire_line[0], cam.tripwire_line[1]
    x1, y1 = nx1 * w, ny1 * h
    x2, y2 = nx2 * w, ny2 * h
    inside_sign = _inside_sign(cam.tripwire_inside_side or "below", cam.tripwire_line)

    log.info(
        "[%s] tripwire pixels: (%.0f,%.0f)->(%.0f,%.0f) inside_sign=%+d",
        cam.label, x1, y1, x2, y2, inside_sign,
    )

    # Lazy import.
    try:
        from ultralytics import YOLO
        import supervision as sv
        model: Any = YOLO("yolov8n.pt")
        tracker: Any = sv.ByteTrack()
    except Exception as e:
        log.error("[%s] detection libs unavailable (%s) — passive", cam.label, e)
        model = None
        tracker = None

    # Per-track state.
    last_side: dict[int, int] = {}           # tracker_id -> last side sign (-1/+1)
    frame_counts: dict[int, int] = {}        # tracker_id -> frames seen
    last_fire: dict[int, float] = {}         # tracker_id -> last fire monotonic time
    last_track_reset = time.time()
    frame_idx = 0

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            log.warning("[%s] read failed; reconnecting in 2s", cam.label)
            cap.release()
            time.sleep(2.0)
            cap = _open_capture(cam, cfg.sim_mode, cfg.sim_source)
            continue

        frame_idx += 1
        if frame_idx % max(1, cam.sample_every_n_frames) != 0:
            continue

        now = datetime.now(timezone.utc)

        # 4-hour tracker reset.
        if tracker is not None and time.time() - last_track_reset > TRACK_RESET_S:
            import supervision as sv
            tracker = sv.ByteTrack()
            last_side.clear()
            frame_counts.clear()
            last_fire.clear()
            last_track_reset = time.time()
            log.info("[%s] tracker reset (4h cap)", cam.label)

        if model is None:
            continue

        results = model.predict(frame, classes=[0], verbose=False, conf=0.4)[0]
        import supervision as sv
        detections = sv.Detections.from_ultralytics(results)
        detections = tracker.update_with_detections(detections)

        if detections.tracker_id is None:
            continue

        seen_now: set[int] = set()
        for xyxy, tid in zip(detections.xyxy, detections.tracker_id):
            if tid is None:
                continue
            tid = int(tid)
            seen_now.add(tid)

            x1b, y1b, x2b, y2b = xyxy
            # Use foot-point (mid-x, bottom-y) — robust for doorway cams.
            fx = (x1b + x2b) / 2.0
            fy = y2b
            side = _side_of_line(fx, fy, x1, y1, x2, y2)
            if side == 0:
                continue  # exactly on the line — skip

            frame_counts[tid] = frame_counts.get(tid, 0) + 1
            prev = last_side.get(tid)
            last_side[tid] = side

            if prev is None or prev == side:
                continue
            if frame_counts[tid] < MIN_TRACK_FRAMES_BEFORE_FIRE:
                continue
            if (time.monotonic() - last_fire.get(tid, 0.0)) < PER_TRACK_COOLDOWN_S:
                continue

            # Crossed!
            #   side == inside_sign  → entered the store
            #   side == -inside_sign → exited the store
            event_type = "entry" if side == inside_sign else "exit"
            last_fire[tid] = time.monotonic()
            _emit_visitor(db_path, cam, event_type, now, tid)
            _fire_clip_safe(cam.rtsp_url, cam.camera_id, event_type)

        # Garbage-collect tracks not seen recently (every 600 frames).
        if frame_idx % 600 == 0:
            stale = [t for t in last_side if t not in seen_now]
            for t in stale:
                last_side.pop(t, None)
                frame_counts.pop(t, None)
                last_fire.pop(t, None)

    cap.release()
    log.info("[%s] entrance capture stopped", cam.label)


# ---------- event emit ----------

def _emit_visitor(
    db_path: str,
    cam: CameraCfg,
    event_type: str,
    when: datetime,
    track_id: int,
) -> None:
    eid = str(uuid.uuid4())
    log.info("[%s] %s tid=%d", cam.label, event_type.upper(), track_id)
    desc = "Customer entered store" if event_type == "entry" else "Customer exited store"
    with sqlite3.connect(db_path) as con:
        insert_event(
            con,
            event_id=eid,
            camera_id=cam.camera_id,
            event_type=event_type,
            severity="info",
            started_at=when,
            ended_at=when,
            confidence=0.9,
            metadata={
                "track_id": track_id,
                "camera_label": cam.label,
                "description": desc,
            },
        )


def _fire_clip_safe(rtsp_url: str, camera_id: str, event_type: str) -> None:
    """Best-effort clip capture. Imports clip_uploader lazily so missing
    module doesn't break the detector."""
    try:
        from .clip_uploader import fire_clip  # type: ignore
        fire_clip(rtsp_url, camera_id, duration_s=CLIP_DURATION_S, tag=event_type)
    except Exception as e:
        log.debug("clip skipped (%s)", e)
