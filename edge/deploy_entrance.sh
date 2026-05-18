#!/usr/bin/env bash
# deploy_entrance.sh — one-command deploy for the entrance counter at 420 Vapor.
#
# Run this ON THE IMAC at the store:
#   cd ~/counteriq && git pull && bash edge/deploy_entrance.sh
#
# What it does:
#   1. Backs up the current config.json
#   2. Adds the channel-2 entrance camera to config.json (idempotent)
#   3. Restarts the launchd agent
#   4. Tails the log so you can verify both cameras boot
#
# Pre-reqs:
#   - Channel 2 is the front-door RTSP feed
#   - NVR credentials already known: cqi / oliver2026 @ 192.168.4.66
#   - Edge agent already installed and paired (api_key.txt present)
#
# After this runs, walk through the door and watch the log for:
#   [Front Door] ENTRY tid=N

set -euo pipefail

REPO="$HOME/counteriq"
CONFIG="$REPO/edge/config.json"
BACKUP="$CONFIG.bak.$(date +%Y%m%d-%H%M%S)"
PLIST_LABEL="us.counteriq.edge"
LOG_FILE="$HOME/Library/Logs/counteriq-edge.log"

echo "==> CounterIQ entrance deploy starting"
echo "    Repo:   $REPO"
echo "    Config: $CONFIG"

if [[ ! -f "$CONFIG" ]]; then
  echo "ERROR: $CONFIG not found. Are you on the iMac?" >&2
  exit 1
fi

# --- 1. Backup
cp "$CONFIG" "$BACKUP"
echo "==> Backed up config to $BACKUP"

# --- 2. Patch config (Python — already available in venv or system python3)
PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "ERROR: python3 not found in PATH" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import json, os, sys, pathlib
cfg_path = pathlib.Path(os.path.expanduser("~/counteriq/edge/config.json"))
cfg = json.loads(cfg_path.read_text())

cams = cfg.setdefault("cameras", [])

ENTRANCE = {
    "camera_id": "ENTRANCE_CAMERA_UUID_REPLACE_ME",
    "label": "Front Door",
    "role": "entrance",
    "rtsp_url": "rtsp://cqi:oliver2026@192.168.4.66:8554/Streaming/Channels/202",
    "tripwire_line": [[0.05, 0.55], [0.95, 0.55]],
    "tripwire_inside_side": "below",
    "sample_every_n_frames": 4
}

# Ensure existing register cam has role
for c in cams:
    c.setdefault("role", "counter")

# Idempotent: replace existing entrance entry by label, else append
replaced = False
for i, c in enumerate(cams):
    if c.get("role") == "entrance" or c.get("label") == "Front Door":
        # Preserve camera_id if it's already a real UUID (not the placeholder)
        if c.get("camera_id") and "REPLACE_ME" not in c["camera_id"]:
            ENTRANCE["camera_id"] = c["camera_id"]
        cams[i] = ENTRANCE
        replaced = True
        break

if not replaced:
    cams.append(ENTRANCE)

cfg_path.write_text(json.dumps(cfg, indent=2))
print(f"==> Patched config. Total cameras: {len(cams)}")
print("    Roles:", [c.get("role", "counter") for c in cams])
if "REPLACE_ME" in ENTRANCE["camera_id"]:
    print()
    print("!!  ACTION REQUIRED: replace ENTRANCE_CAMERA_UUID_REPLACE_ME in")
    print(f"    {cfg_path}")
    print("    with the camera UUID for 'Front Door' from the Supabase cameras table.")
    print("    (You can also just add the row via the dashboard and copy the UUID.)")
PY

# --- 3. Restart launchd
echo "==> Restarting launchd agent: $PLIST_LABEL"
launchctl kickstart -k "gui/$(id -u)/$PLIST_LABEL" || {
  echo "WARN: kickstart failed — trying load/unload"
  launchctl unload "$HOME/Library/LaunchAgents/$PLIST_LABEL.plist" 2>/dev/null || true
  launchctl load   "$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"
}

sleep 2

# --- 4. Tail log
echo "==> Tailing $LOG_FILE for 20 seconds (Ctrl-C to stop)"
echo "    Look for:  'started entrance thread for camera Front Door'"
echo "    Look for:  'resolution: WxH'  (proves RTSP ch.2 opened)"
echo
timeout 20 tail -f "$LOG_FILE" 2>/dev/null || tail -n 60 "$LOG_FILE"

echo
echo "==> Deploy complete. Walk through the front door and watch for:"
echo "    [Front Door] ENTRY tid=N"
echo "==> Rollback if needed:  cp $BACKUP $CONFIG && launchctl kickstart -k gui/\$(id -u)/$PLIST_LABEL"
