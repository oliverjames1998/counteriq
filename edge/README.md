# CounterIQ Edge Agent — README

Runs on a Jetson Orin Nano 8GB (Ubuntu 22.04 + JetPack). At MVP this folder
contains two scripts:

- `rtsp_test.py` — connect to a single RTSP camera and verify the feed.
- `counter_unattended_prototype.py` — first event detector running locally.

Full async agent (ingest/detect/track/zones/events/clipper/sync/health/
config/storage/main) lives at `/edge/src/` and is built per
`prompts/CURSOR_EDGE_DEVICE_PROMPT.md`.

## Hardware needed (MVP)
- 1× Jetson Orin Nano 8GB Dev Kit ($499)
- 1× IP camera with RTSP (Reolink RLC-810A or your store's existing cam)
- Ethernet to the camera/NVR
- Power supply + microSD (32GB+)

## Setup (Linux/Jetson)

```bash
sudo apt update && sudo apt install -y ffmpeg python3.11 python3-venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Setup (Windows dev/test)

```powershell
# install ffmpeg via scoop or chocolatey first
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Test RTSP

```bash
python rtsp_test.py rtsp://USER:PASS@IP:554/Streaming/Channels/101
```

You should see the script connect, decode 30 frames, and print average FPS.

## Run counter-unattended prototype

```bash
# edit config.example.json -> config.json with your camera URL + counter polygon
python counter_unattended_prototype.py --config config.json
```

The script logs to stdout and writes events to `./events.sqlite`.

## Privacy guards (verified)

- ffmpeg is invoked with `-an` always (no audio).
- No face/STT libraries imported.
- No PCM written to disk anywhere.
- Track IDs reset every 4 hours.

## Next steps

After prototype works for 24 hours:
1. Add cloud sync (post events to `/api/edge/events`).
2. Add clip writer (rolling 60s buffer + 30s clip on event).
3. Add R2 upload via presigned URL.
4. Move to full async agent in `/edge/src/`.
