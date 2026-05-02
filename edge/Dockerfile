# Runs the CounterIQ edge agent on any x86_64 Linux box.
# For Jetson Orin Nano: build using the JetPack-compatible base instead
# (nvcr.io/nvidia/l4t-pytorch:r36.2.0-pth2.2-py3) and install ultralytics
# at runtime — see edge/JETSON.md for the full Jetson recipe.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    OPENCV_FFMPEG_CAPTURE_OPTIONS="rtsp_transport;tcp|an;1"

RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg ca-certificates libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY src ./src
COPY config.example.json ./

# Read config from /etc/counteriq/config.json by default. Mount it.
ENV COUNTERIQ_CONFIG=/etc/counteriq/config.json

CMD ["python", "-m", "src.main", "--config", "/etc/counteriq/config.json"]
