"""Person detection + tracking + counter-unattended detector.

Privacy contract:
- ffmpeg invoked with -an (audio disabled). Inherited from cv2/RTSP open.
- Person detection only (YOLOv8n, class=0). No facial recognition.
- ByteTrack reset every 4 hours (track-lifetime cap).
- No PCM persisted anywhere.

Banned imports — DO NOT add: face_recognition, dlib face APIs, whisper,
vosk, deepspeech, speech_recognition, insightface, deepface.
"""
from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, time as dtime, timezone
from typing import Any

import cv2
from shapely.geometry import Polygon, Point

from .config import CameraCfg, EdgeConfig
from .db import insert_event

log = logging.getLogger(__name__)

# ---- detection thresholds (per docs/EVENT_DETECTION_LOGIC.md) ----
EMPTY_THRESHOLD_S = 5 * 60
HIGH_SEVERITY_S = 8 * 60
COOLDOWN_S = 15 * 60
TRACK_RESET_S = 4 * 3600


def _in_business_hours(now: datetime, hours_cfg: dict[str, Any]) -> bool:
    day_key = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][now.weekday()]
    cfg = hours_cfg.get(day_key, {})
    if cfg.get("closed", False):
        return False
    open_t = dtime.fromisoformat(cfg.get("open", "09:00"))
    close_t = dtime.fromisoformat(cfg.get("close", "21:00"))
    return open_t <= now.time() <= close_t


def _in_open_close_buffer(now: datetime, hours_cfg: dict[str, Any], buffer_min: int = 10) -> bool:
    day_key = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][now.weekday()]
    cfg = hours_cfg.get(day_key, {})
    if cfg.get("closed", False):
        return False
    open_t = datetime.combine(now.date(), dtime.fromisoformat(cfg.get("open", "09:00")), tzinfo=now.tzinfo)
    close_t = datetime.combine(now.date(), dtime.fromisoformat(cfg.get("close", "21:00")), tzinfo=now.tzinfo)
    return abs((now - open_t).total_seconds()) < buffer_min * 60 or abs((close_t - now).total_seconds()) < buffer_min * 60


def _open_capture(cam: CameraCfg, sim_mode: bool, sim_source: str) -> cv2.VideoCapture:
    if sim_mode:
        # Webcam ("0") or video file path. Useful for dev without a Jetson.
        try:
            return cv2.VideoCapture(int(sim_source))
        except ValueError:
            return cv2.VideoCapture(sim_source)
    # Real RTSP. Note: cv2 opens RTSP without exposing audio by default.
    # We additionally guarantee no audio by setting FFMPEG opts.
    os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp|an;1")
    return cv2.VideoCapture(cam.rtsp_url)


def run_camera(
    cam: CameraCfg,
    cfg: EdgeConfig,
    db_path: str,
    stop_event: threading.Event,
) -> None:
    """One thread per camera. Detects counter_unattended events and writes
    them to the local SQLite buffer. The sync thread later drains them up."""
    log.info("[%s] starting capture (sim_mode=%s)", cam.label, cfg.sim_mode)
    cap = _open_capture(cam, cfg.sim_mode, cfg.sim_source)
    if not cap.isOpened():
        log.error("[%s] could not open source", cam.label)
        return

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
    log.info("[%s] resolution: %dx%d", cam.label, w, h)

    poly_px = None
    if cam.counter_polygon:
        poly_px = Polygon([(x * w, y * h) for x, y in cam.counter_polygon])

    # Lazy import so the agent can run without ultralytics installed (sim
    # mode without detection still streams frames). YOLOv8n weights cached
    # to ./yolov8n.pt on first run.
    try:
        from ultralytics import YOLO
        import supervision as sv
        model: Any = YOLO("yolov8n.pt")
        tracker: Any = sv.ByteTrack()
    except Exception as e:
        log.error("[%s] detection libraries unavailable (%s) — running in passive mode", cam.label, e)
        model = None
        tracker = None

    empty_since: datetime | None = None
    last_emit: datetime | None = None
    emitted_high = False
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
        if frame_idx % cam.sample_every_n_frames != 0:
            continue

        now = datetime.now(timezone.utc)

        # 4-hour tracker reset (privacy guarantee).
        if tracker is not None and time.time() - last_track_reset > TRACK_RESET_S:
            import supervision as sv
            tracker = sv.ByteTrack()
            last_track_reset = time.time()
            log.info("[%s] tracker reset (4h cap)", cam.label)

        if model is not None and poly_px is not None:
            results = model.predict(frame, classes=[0], verbose=False, conf=0.4)[0]
            import supervision as sv
            detections = sv.Detections.from_ultralytics(results)
            detections = tracker.update_with_detections(detections)

            inside_count = 0
            for xyxy in detections.xyxy:
                x1, y1, x2, y2 = xyxy
                foot = Point(((x1 + x2) / 2.0), y2)
                if poly_px.contains(foot):
                    inside_count += 1
        else:
            inside_count = 0

        if not _in_business_hours(now, cfg.business_hours.model_dump()) or _in_open_close_buffer(now, cfg.business_hours.model_dump()):
            empty_since = None
            emitted_high = False
            continue

        if inside_count > 0:
            empty_since = None
            emitted_high = False
            continue

        empty_since = empty_since or now
        elapsed_s = (now - empty_since).total_seconds()
        on_cooldown = last_emit is not None and (now - last_emit).total_seconds() < COOLDOWN_S
        if elapsed_s < EMPTY_THRESHOLD_S or on_cooldown:
            continue

        severity = "high" if elapsed_s >= HIGH_SEVERITY_S else "medium"
        if severity == "high" and not emitted_high:
            _emit(db_path, cam, severity, empty_since, now, elapsed_s)
            last_emit, emitted_high = now, True
        elif severity == "medium" and last_emit is None:
            _emit(db_path, cam, severity, empty_since, now, elapsed_s)
            last_emit = now

    cap.release()
    log.info("[%s] capture stopped", cam.label)


def _emit(db_path: str, cam: CameraCfg, severity: str, started_at: datetime,
          ended_at: datetime, elapsed_s: float) -> None:
    eid = str(uuid.uuid4())
    log.info("[%s] event counter_unattended severity=%s elapsed=%ds", cam.label, severity, int(elapsed_s))
    with sqlite3.connect(db_path) as con:
        from .db import insert_event as _insert
        _insert(
            con,
            event_id=eid,
            camera_id=cam.camera_id,
            event_type="counter_unattended",
            severity=severity,
            started_at=started_at,
            ended_at=ended_at,
            confidence=min(1.0, elapsed_s / EMPTY_THRESHOLD_S),
            metadata={"elapsed_s": int(elapsed_s), "camera_label": cam.label},
        )
