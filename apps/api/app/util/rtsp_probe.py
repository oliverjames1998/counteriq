"""RTSP probe via ffmpeg/ffprobe.

CRITICAL: every ffmpeg invocation passes `-an` (audio disabled). Audio is OFF
by default at every layer per docs/PRIVACY_RULES.md.
"""
from __future__ import annotations

import base64
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProbeResult:
    ok: bool
    audio_supported: bool
    resolution: Optional[str]
    frame_jpeg_b64: Optional[str]
    error: Optional[str]


def probe_rtsp(rtsp_url: str, timeout_s: int = 10) -> ProbeResult:
    """Probe an RTSP stream. Returns one still frame as base64 JPEG.

    Never opens audio. Never persists audio. ffmpeg is invoked with -an.
    """
    try:
        ffprobe = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-rtsp_transport", "tcp",
                "-timeout", str(timeout_s * 1_000_000),
                "-show_streams", "-of", "json", rtsp_url,
            ],
            capture_output=True, timeout=timeout_s + 2, text=True,
        )
        if ffprobe.returncode != 0:
            return ProbeResult(False, False, None, None, ffprobe.stderr.strip()[:500])
        info = json.loads(ffprobe.stdout or "{}")
        streams = info.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_supported = any(s.get("codec_type") == "audio" for s in streams)
        resolution = f"{video['width']}x{video['height']}" if video and "width" in video else None
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        return ProbeResult(False, False, None, None, f"probe failed: {e}")

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "frame.jpg"
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-v", "error",
                    "-rtsp_transport", "tcp",
                    "-an",
                    "-i", rtsp_url,
                    "-frames:v", "1", "-q:v", "5",
                    str(out),
                ],
                capture_output=True, timeout=timeout_s + 2, check=True,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            return ProbeResult(False, audio_supported, resolution, None, f"frame capture failed: {e}")

        b64 = base64.b64encode(out.read_bytes()).decode("ascii") if out.exists() else None

    return ProbeResult(
        ok=b64 is not None,
        audio_supported=audio_supported,
        resolution=resolution,
        frame_jpeg_b64=b64,
        error=None if b64 else "no frame captured",
    )
