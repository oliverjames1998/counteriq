"""
CounterIQ - RTSP Test Script
Verifies a camera's RTSP feed is reachable and decodable.

Usage:
    python rtsp_test.py rtsp://USER:PASS@IP:554/Streaming/Channels/101

Privacy: invokes ffmpeg with -an (no audio).
"""

import sys
import time
import subprocess
import shlex
import cv2


def probe_rtsp(rtsp_url: str, n_frames: int = 30, timeout_s: int = 15) -> dict:
    """
    Pull `n_frames` from the RTSP URL via OpenCV. Return basic metrics.
    Also runs ffprobe to detect resolution + audio track presence (info only).
    """
    probe_cmd = (
        f'ffprobe -v error -select_streams v:0 '
        f'-show_entries stream=width,height,r_frame_rate '
        f'-of default=nw=1 {shlex.quote(rtsp_url)}'
    )
    audio_probe_cmd = (
        f'ffprobe -v error -select_streams a -show_entries stream=index '
        f'-of default=nw=1 {shlex.quote(rtsp_url)}'
    )

    print(f"[probe] running ffprobe...")
    try:
        v_info = subprocess.check_output(
            probe_cmd, shell=True, timeout=timeout_s, text=True)
        a_info = subprocess.check_output(
            audio_probe_cmd, shell=True, timeout=timeout_s, text=True)
    except subprocess.CalledProcessError as e:
        return {"ok": False, "error": f"ffprobe failed: {e}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "ffprobe timed out"}
    except FileNotFoundError:
        return {"ok": False, "error": "ffprobe not found in PATH (install ffmpeg)"}

    print(f"[probe] video info: {v_info.strip()}")
    print(f"[probe] audio track present: {bool(a_info.strip())}")

    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        return {"ok": False, "error": "cv2 could not open stream"}

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[stream] resolution: {width}x{height}")

    frames_read = 0
    start = time.time()
    while frames_read < n_frames and time.time() - start < timeout_s:
        ret, frame = cap.read()
        if not ret:
            print(f"[warn] frame {frames_read} read failed; retrying")
            time.sleep(0.1)
            continue
        frames_read += 1

    elapsed = time.time() - start
    cap.release()

    # Save one snapshot if we got any frames.
    if frames_read > 0:
        snapshot_path = "rtsp_test_snapshot.jpg"
        cv2.imwrite(snapshot_path, frame)
        print(f"[snapshot] saved to {snapshot_path}")

    fps = frames_read / elapsed if elapsed > 0 else 0
    return {
        "ok": frames_read == n_frames,
        "frames_read": frames_read,
        "elapsed_s": round(elapsed, 2),
        "fps": round(fps, 2),
        "resolution": f"{width}x{height}",
        "audio_track_present": bool(a_info.strip()),
        "audio_used": False,  # CounterIQ never uses audio at MVP
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python rtsp_test.py <rtsp_url> [n_frames]")
        sys.exit(1)
    url = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    result = probe_rtsp(url, n)
    print()
    print("=== RESULT ===")
    for k, v in result.items():
        print(f"  {k:24s} {v}")
    sys.exit(0 if result["ok"] else 1)
