"""
CounterIQ - Counter Unattended Prototype
Single-camera, single-detector. Logs events to local SQLite.

Usage:
    python counter_unattended_prototype.py --config config.json

Privacy:
- ffmpeg invoked with -an (no audio).
- No face/STT libraries.
- Track IDs reset every 4 hours.
- Event language is observational only.
"""

import argparse
import json
import sqlite3
import time
import uuid
from datetime import datetime, time as dtime, timezone
from pathlib import Path

import cv2
from shapely.geometry import Polygon, Point
from ultralytics import YOLO
import supervision as sv

DB_PATH = Path("./events.sqlite")
COOLDOWN_SECONDS = 15 * 60      # 15 min per camera
EMPTY_THRESHOLD_S = 5 * 60      # 5 min
HIGH_SEVERITY_S = 8 * 60        # 8 min


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        create table if not exists events (
          id text primary key,
          camera_id text,
          type text,
          severity text,
          started_at text,
          ended_at text,
          confidence real,
          metadata text,
          synced int default 0,
          created_at text default current_timestamp
        )
    """)
    con.commit()
    return con


def log_event(con, camera_id, severity, started_at, ended_at, confidence, metadata):
    eid = str(uuid.uuid4())
    con.execute(
        "insert into events (id, camera_id, type, severity, started_at, "
        "ended_at, confidence, metadata) values (?,?,?,?,?,?,?,?)",
        (eid, camera_id, "counter_unattended", severity,
         started_at.isoformat(), ended_at.isoformat(),
         confidence, json.dumps(metadata)),
    )
    con.commit()
    print(f"[event] {eid[:8]} counter_unattended severity={severity} "
          f"elapsed={metadata.get('elapsed_s')}s")
    return eid


def in_business_hours(now: datetime, hours_cfg: dict) -> bool:
    """hours_cfg = {"mon":{"open":"09:00","close":"21:00","closed":false}, ...}"""
    day = ["mon","tue","wed","thu","fri","sat","sun"][now.weekday()]
    cfg = hours_cfg.get(day, {})
    if cfg.get("closed", False):
        return False
    open_t  = dtime.fromisoformat(cfg.get("open", "09:00"))
    close_t = dtime.fromisoformat(cfg.get("close", "21:00"))
    return open_t <= now.time() <= close_t


def in_open_close_buffer(now: datetime, hours_cfg: dict, buffer_min: int = 10) -> bool:
    """First/last 10 min of business window - suppress events."""
    day = ["mon","tue","wed","thu","fri","sat","sun"][now.weekday()]
    cfg = hours_cfg.get(day, {})
    if cfg.get("closed", False):
        return False
    open_t  = datetime.combine(now.date(), dtime.fromisoformat(cfg.get("open","09:00")))
    close_t = datetime.combine(now.date(), dtime.fromisoformat(cfg.get("close","21:00")))
    return (
        abs((now - open_t).total_seconds())  < buffer_min * 60 or
        abs((close_t - now).total_seconds()) < buffer_min * 60
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    rtsp_url     = cfg["rtsp_url"]
    camera_id    = cfg.get("camera_id", "cam-local-1")
    counter_poly = cfg["counter_polygon"]
    hours_cfg    = cfg["business_hours"]

    print(f"[start] camera_id={camera_id}")
    print(f"[start] connecting RTSP (audio: NEVER captured)...")
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print("[fatal] could not open RTSP")
        return

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[start] resolution: {w}x{h}")

    poly_px = Polygon([(x*w, y*h) for x,y in counter_poly])

    print("[start] loading YOLOv8n...")
    model = YOLO("yolov8n.pt")
    tracker = sv.ByteTrack()

    con = init_db()

    empty_since = None
    last_emit = None
    emitted_high = False
    last_track_reset = time.time()

    frame_idx = 0
    SAMPLE_EVERY = 6  # ~5fps when source is 30fps

    print("[start] entering main loop. Ctrl+C to stop.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[warn] read failed; sleeping 1s and retrying")
            time.sleep(1.0)
            continue

        frame_idx += 1
        if frame_idx % SAMPLE_EVERY != 0:
            continue

        now = datetime.now(timezone.utc)

        # Reset trackers every 4 hours (privacy safeguard).
        if time.time() - last_track_reset > 4*3600:
            tracker = sv.ByteTrack()
            last_track_reset = time.time()
            print("[privacy] tracker reset (4h cap)")

        # Detect persons.
        results = model.predict(frame, classes=[0], verbose=False, conf=0.4)[0]
        detections = sv.Detections.from_ultralytics(results)
        detections = tracker.update_with_detections(detections)

        # Foot-point inside counter polygon?
        inside_count = 0
        for xyxy in detections.xyxy:
            x1, y1, x2, y2 = xyxy
            foot = Point(((x1+x2)/2.0), y2)
            if poly_px.contains(foot):
                inside_count += 1

        in_hours  = in_business_hours(now, hours_cfg)
        in_buffer = in_open_close_buffer(now, hours_cfg)

        if not in_hours or in_buffer:
            empty_since = None
            emitted_high = False
            continue

        if inside_count > 0:
            empty_since = None
            emitted_high = False
        else:
            empty_since = empty_since or now
            elapsed_s = (now - empty_since).total_seconds()

            on_cooldown = (last_emit and
                           (now - last_emit).total_seconds() < COOLDOWN_SECONDS)

            if elapsed_s >= EMPTY_THRESHOLD_S and not on_cooldown:
                severity = "high" if elapsed_s >= HIGH_SEVERITY_S else "medium"
                if severity == "high" and not emitted_high:
                    log_event(con, camera_id, "high",
                              empty_since, now,
                              confidence=min(1.0, elapsed_s / EMPTY_THRESHOLD_S),
                              metadata={"elapsed_s": int(elapsed_s)})
                    last_emit = now
                    emitted_high = True
                elif severity == "medium" and last_emit is None:
                    log_event(con, camera_id, "medium",
                              empty_since, now,
                              confidence=min(1.0, elapsed_s / EMPTY_THRESHOLD_S),
                              metadata={"elapsed_s": int(elapsed_s)})
                    last_emit = now


if __name__ == "__main__":
    main()
