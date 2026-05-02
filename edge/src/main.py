"""CounterIQ edge agent entry point.

Usage:
    python -m edge.src.main --config /etc/counteriq/config.json

Lifecycle:
1. Load config.json (cameras, business hours, api_base_url, pairing_token).
2. If api_key.txt missing: POST /api/edge/claim with pairing_token, save key.
3. Start one detection thread per camera + one sync thread + one heartbeat.
4. On SIGINT / SIGTERM: stop all threads cleanly, flush sync buffer, exit 0.

Privacy:
- ffmpeg invocations include `an;1` via OPENCV_FFMPEG_CAPTURE_OPTIONS.
- 4h tracker reset enforced inside detector.py.
- No facial recognition, no STT, no demographic/emotion inference.
- Audio modules NOT imported at all in this build.
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
from pathlib import Path

from .config import EdgeConfig, load_or_pair_api_key
from .detector import run_camera
from .sync import heartbeat_thread, sync_thread

log = logging.getLogger("counteriq.edge")


def main() -> int:
    ap = argparse.ArgumentParser(prog="counteriq-edge")
    ap.add_argument("--config", required=True, help="Path to config.json")
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)-7s %(name)s %(message)s",
    )

    cfg = EdgeConfig.load(args.config)
    log.info("config loaded: %d cameras, sim_mode=%s", len(cfg.cameras), cfg.sim_mode)

    api_key = load_or_pair_api_key(cfg)
    log.info("paired (api_key length %d)", len(api_key))

    Path(cfg.state_db).parent.mkdir(parents=True, exist_ok=True)

    stop_event = threading.Event()

    def _shutdown(signum: int, _frame: object) -> None:
        log.info("signal %d — shutting down", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _shutdown)

    threads: list[threading.Thread] = []

    for cam in cfg.cameras:
        t = threading.Thread(
            target=run_camera,
            name=f"cam-{cam.camera_id}",
            args=(cam, cfg, cfg.state_db, stop_event),
            daemon=True,
        )
        t.start()
        threads.append(t)

    sync_t = threading.Thread(
        target=sync_thread,
        name="sync",
        args=(cfg.api_base_url, api_key, cfg.state_db, cfg.sync_interval_s, stop_event),
        daemon=True,
    )
    sync_t.start()
    threads.append(sync_t)

    hb_t = threading.Thread(
        target=heartbeat_thread,
        name="heartbeat",
        args=(cfg.api_base_url, api_key, cfg.heartbeat_interval_s, stop_event),
        daemon=True,
    )
    hb_t.start()
    threads.append(hb_t)

    stop_event.wait()
    log.info("waiting for threads to exit (up to 30s)")
    for t in threads:
        t.join(timeout=30)
    log.info("clean exit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
