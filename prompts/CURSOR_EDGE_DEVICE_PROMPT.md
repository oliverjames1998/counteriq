# Cursor Prompt — CounterIQ Edge Device Agent

Paste into Cursor in a fresh /counteriq/edge directory.

---

Build the CounterIQ edge device agent. Runs on NVIDIA Jetson Orin Nano 8GB
(Ubuntu 22.04 + JetPack). Python 3.11.

CONTEXT
- Connects to existing store cameras over RTSP.
- Detects persons with YOLOv8n + ByteTrack.
- Evaluates polygon zones.
- Detects 1 event type at MVP: counter_unattended.
- Saves 30s clip on event.
- Posts events + clips to CounterIQ cloud API.
- NO AUDIO at MVP. audio_*.py modules NOT created.
- NO face recognition. NO STT. NO demographic / emotion inference.
- ffmpeg invoked with -an (no audio) explicitly.

FILE STRUCTURE
/edge
  /src
    ingest.py
    detect.py
    track.py
    zones.py
    events.py
    clipper.py
    sync.py
    health.py
    config.py
    storage.py
    main.py
  /models
    yolov8n.pt   (downloaded on first run via Ultralytics)
  requirements.txt
  Dockerfile
  systemd/counteriq-edge.service
  README.md

REQUIREMENTS.txt
ultralytics==8.3.*
supervision==0.25.*
opencv-python-headless==4.10.*
av==13.*
shapely==2.*
httpx==0.27.*
pydantic==2.*
aiosqlite==0.20.*
numpy>=1.24

FILE PURPOSES

ingest.py — Pull RTSP video. ffmpeg subprocess per camera with -an flag
explicit. Decode to BGR ndarray. Push to per-camera asyncio queue at 5fps
for inference, 30fps for clip buffer. Auto-respawn ffmpeg with exponential
backoff (1s → 60s capped).

detect.py — YOLOv8n inference. Persons only (cls=0). Use TensorRT export
on Jetson (yolov8n.engine) for 2–3x speedup. Half precision.

track.py — ByteTrack via supervision. Track lifetime cap 4 hours; IDs
regenerate after.

zones.py — Polygon hit-testing via Shapely. Foot-point (bbox bottom-center)
is the reference.

events.py — One detector at MVP: counter_unattended. Logic:
  state: empty_since[camera] = None
  each tick (5s):
    if not in_business_hours: empty_since[camera] = None; continue
    inside = any tracked person inside counter polygon
    if inside: empty_since[camera] = None
    else:
      empty_since[camera] = empty_since[camera] or now()
      elapsed = now() - empty_since[camera]
      if elapsed >= 5 min and not emitted_this_window:
        emit_event(type='counter_unattended', severity='medium',
                   started_at=empty_since[camera], ended_at=now(),
                   confidence=min(1, elapsed_min/5),
                   metadata={'elapsed_s': elapsed.seconds})
        clipper.request_clip(start=empty_since+4min, duration=30s)
        emitted = True
      if elapsed >= 8 min:
        severity = 'high'
        trigger_alert(P1)
  False-positive guards: ignore first/last 10 min of business window.
  Per-camera 15-min cooldown after emission.

clipper.py — RollingBuffer per camera (deque of 60s frames at 30fps).
On request_clip: wait post seconds, slice, encode H.264 MP4 via PyAV
(crf=23, ~720p), write JPG thumbnail of trigger frame, queue for upload.

sync.py — Two loops:
- sync_events_loop (every 60s): batch up to 100 events from SQLite outbox
  → POST /api/edge/events.
- sync_clips_loop (every 30s): GET R2 presigned URL via /api/edge/clips/presign,
  PUT clip, POST /api/edge/clips with metadata.
Retry: exponential backoff. Persistent SQLite queue. Never drop.

health.py — Heartbeat loop every 60s POST /api/edge/heartbeat with
{version, cameras_fps, disk_free_gb, cpu_pct, gpu_temp_c, queue_depth}.

config.py — Poll /api/edge/config every 5 min. On config change (hash diff),
signal main.py to reload zones/cameras gracefully. Persist to config.json
for offline restart.

storage.py — Local SQLite WAL. Tables: events_outbox, clips_outbox.
Vacuum old uploaded rows after 7 days.

main.py — Orchestrator. Spawns asyncio tasks per camera (ingest → detect
→ track → zones → events) and shared workers (sync, health, config).
Handles SIGTERM gracefully.

DOCKERFILE
- Base: nvcr.io/nvidia/l4t-pytorch:r36.2.0-pth2.2-py3 (Jetson)
- Install ffmpeg (audio codecs NOT needed at MVP)
- Copy src + models
- ENTRYPOINT python -m src.main

SYSTEMD UNIT
[Unit] Description=CounterIQ Edge Agent After=network-online.target docker.service
[Service] Restart=always RestartSec=10
ExecStart=/usr/bin/docker run --rm --gpus all --network host \
  -v /opt/counteriq:/data --env-file /etc/counteriq/edge.env counteriq/edge:latest
[Install] WantedBy=multi-user.target

ACCEPTANCE
- Connects to a single RTSP camera and runs 24h continuous without crash.
- counter_unattended fires within 30s of crossing 5-min empty threshold.
- 30s clip arrives in cloud R2 within 60s of event.
- Heartbeat posts every 60s.
- Config reload picks up new zone within 5 min.
- ffmpeg processes contain "-an" flag in process list (no audio path).
- No face/STT libraries in dependency tree (CI verifies).
