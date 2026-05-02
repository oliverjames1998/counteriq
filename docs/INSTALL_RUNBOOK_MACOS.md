# CounterIQ — macOS Edge Install (iMac at the Store)

Use this runbook when the edge box is a Mac (iMac, Mac mini, MacBook left at
the store). For Linux + Jetson installs, use [INSTALL_RUNBOOK.md](INSTALL_RUNBOOK.md)
instead.

## Tested target

- **iMac Retina 4K, 21.5-inch, 2019** — Intel Core i3 quad-core 3.6 GHz, 8 GB
  RAM, AMD Radeon Pro 555X (unused for AI; CPU-only), macOS Sonoma 14.2.1.
- Realistic capacity: **1–2 cameras at sub-stream resolution**. 4 cameras is
  pushing it on this hardware — bump `sample_every_n_frames` to 12 if you go
  there.

Apple Silicon Macs (M1/M2/M3) will be 5–10× faster and can run all 4 cameras
comfortably. Same install path, just faster.

---

## Pre-flight (5 minutes)

Before you touch the iMac, you need:

1. **NVR's local IP** on the store's WiFi. Find it via:
   - LTS Connect mobile app → device → settings → "IP Address"
   - Browser to `http://192.168.4.1` (your router) → Connected Devices → look for "Hikvision"
   - The NVR's HDMI display: right-click → Menu → Configuration → Network
2. **NVR ONVIF user + password** (recommended over the admin user). Set these
   up in the NVR web UI: Configuration → User → ONVIF Users → Add. Give it
   "Operator" permission.
3. **Camera channel numbers** on the NVR. Camera 1 = channel 1, etc.

---

## Phase A — Backend deploy (15 minutes, once per pilot)

If `https://counteriq-api.fly.dev/healthz` already returns `{"ok": true}`,
skip this phase.

```bash
# On any Mac with admin
brew install flyctl
fly auth login                     # opens browser
cd /path/to/counteriq/apps/api
fly launch --no-deploy --copy-config
fly secrets set EDGE_KEY_PEPPER="$(openssl rand -hex 32)"
fly deploy
curl https://counteriq-api.fly.dev/healthz   # → {"ok":true}
```

---

## Phase B — Provision the device row (5 minutes)

In Lovable's SQL editor:
https://lovable.dev/projects/97b46b57-0933-4dd3-be25-c8e105554b8f?view=cloud&section=sql_editor

```sql
-- Find your store_id first
SELECT id, name FROM stores;

-- Then create a device row (replace the store id)
INSERT INTO edge_devices (store_id, name, pairing_token)
VALUES (
  '<your-store-uuid>',
  'iMac Edge — Vapor Planet',
  encode(gen_random_bytes(16), 'hex')
)
RETURNING id, pairing_token;
```

**Copy the `pairing_token`** — you'll paste it into the iMac's config.json.
The token is single-use; the device claims it on first boot and exchanges it
for a long-lived `api_key` that only the device knows.

---

## Phase C — Install on the iMac (20 minutes)

### C.1 Open Terminal on the iMac (Cmd+Space → "Terminal")

### C.2 Install Xcode command-line tools (one-time, includes git)

```bash
xcode-select --install
```

A dialog pops up. Click **Install**. Wait ~5 minutes.

### C.3 Install Homebrew (one-time)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the on-screen prompts. After install, run the two commands it tells
you to add Homebrew to your PATH (something like `eval "$(/opt/homebrew/bin/brew shellenv)"`).

### C.4 Install Python 3.11 + ffmpeg

```bash
brew install python@3.11 ffmpeg
```

### C.5 Clone the CounterIQ repo

```bash
sudo mkdir -p /opt/counteriq
sudo chown $(whoami) /opt/counteriq
cd /opt/counteriq
git clone https://github.com/oliverjames1998/counteriq.git .
cd edge
```

### C.6 Set up the Python environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This downloads ~1.2 GB (PyTorch + ultralytics). Takes 3–5 minutes on
typical store WiFi.

---

## Phase D — Configure cameras (15 minutes)

### D.1 Test the RTSP URL works

Build the URL using your NVR IP + ONVIF user:

```
rtsp://counteriq:YOUR_PASSWORD@192.168.4.???:554/Streaming/Channels/102
```

(That's Camera 1 sub-stream. Channel 1 main = `/101`, Channel 1 sub = `/102`,
Channel 2 main = `/201`, etc. Sub-streams are lower resolution and ideal for
the iMac.)

Test it from Terminal:

```bash
ffmpeg -an -rtsp_transport tcp -i "rtsp://counteriq:PASS@192.168.4.???:554/Streaming/Channels/102" \
  -frames:v 1 -y /tmp/probe.jpg && open /tmp/probe.jpg
```

If a still frame opens in Preview → RTSP works. If you get errors:
- "401 Unauthorized" → wrong username or password
- "Connection refused" → wrong IP or RTSP port disabled
- "404 Not Found" → wrong channel number

### D.2 Add the camera in the dashboard

1. Open https://app.counteriq.us/cameras (sign in)
2. Click **Add camera** (or use the "Test connection" flow)
3. Paste the RTSP URL
4. Save the camera, copy its UUID from the URL bar

### D.3 Draw the counter zone

1. From the camera list, click **Edit zones**
2. Drag a polygon over the till/counter area
3. Save

### D.4 Build /etc/counteriq/config.json

```bash
sudo mkdir -p /etc/counteriq
sudo chown $(whoami) /etc/counteriq
cp /opt/counteriq/edge/config.example.json /etc/counteriq/config.json
chmod 600 /etc/counteriq/config.json
nano /etc/counteriq/config.json
```

Edit values:
- `pairing_token` → from Phase B
- `cameras[0].camera_id` → camera UUID from D.2
- `cameras[0].rtsp_url` → the working RTSP URL from D.1
- `cameras[0].counter_polygon` → either keep the example, or paste the
  polygon coordinates from the dashboard's audit log
- `business_hours` → your store's actual hours

---

## Phase E — First boot (foreground sanity check)

```bash
cd /opt/counteriq/edge
source venv/bin/activate
python -m src.main --config /etc/counteriq/config.json --log-level INFO
```

Expected log lines in order:
```
INFO  config loaded: 1 cameras, sim_mode=False
INFO  paired (api_key length 64)
INFO  [Counter Overhead] starting capture (sim_mode=False)
INFO  [Counter Overhead] resolution: 1280x720
```

YOLOv8n weights download to `./yolov8n.pt` on first run (~6 MB).

Verify in the dashboard at https://app.counteriq.us/cameras — Counter
Overhead should show **Online** within 30 seconds. Walk away from the
counter for 5 minutes during business hours and watch for a counter_unattended
event.

Press **Ctrl+C** to stop the foreground run once you've verified it works.

---

## Phase F — Run as a launchd service (auto-start, survives reboots)

macOS uses launchd instead of systemd. Create the service plist:

```bash
sudo tee /Library/LaunchDaemons/us.counteriq.edge.plist > /dev/null <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>us.counteriq.edge</string>

  <key>ProgramArguments</key>
  <array>
    <string>/opt/counteriq/edge/venv/bin/python</string>
    <string>-m</string>
    <string>src.main</string>
    <string>--config</string>
    <string>/etc/counteriq/config.json</string>
  </array>

  <key>WorkingDirectory</key>
  <string>/opt/counteriq/edge</string>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>/var/log/counteriq-edge.log</string>

  <key>StandardErrorPath</key>
  <string>/var/log/counteriq-edge.err.log</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>OPENCV_FFMPEG_CAPTURE_OPTIONS</key>
    <string>rtsp_transport;tcp|an;1</string>
  </dict>

  <key>ProcessType</key>
  <string>Background</string>
</dict>
</plist>
EOF

sudo chmod 644 /Library/LaunchDaemons/us.counteriq.edge.plist
sudo launchctl load -w /Library/LaunchDaemons/us.counteriq.edge.plist

# Watch the log
tail -f /var/log/counteriq-edge.log
```

To stop / restart later:

```bash
sudo launchctl unload /Library/LaunchDaemons/us.counteriq.edge.plist
sudo launchctl load -w /Library/LaunchDaemons/us.counteriq.edge.plist
```

---

## Phase G — macOS-specific gotchas

### G.1 Disable App Nap so macOS doesn't suspend the agent

App Nap can pause processes that look idle. Disable it for our Python venv:

```bash
defaults write NSGlobalDomain NSAppSleepDisabled -bool YES
```

### G.2 Disable system + display sleep

System Settings → Energy → set **Prevent automatic sleeping when display is
off** to ON. Or:

```bash
sudo systemsetup -setcomputersleep Never
sudo systemsetup -setdisplaysleep 5      # display can sleep, system stays awake
sudo pmset -a disablesleep 1
```

### G.3 Auto-start after power outage

System Settings → Energy → **Start up automatically after a power failure**:
ON.

### G.4 First-time CPU warning

You'll see a security/privacy prompt the first time the agent reads from the
network. Click **Allow** for "Python" or "Terminal".

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `paired (api_key length 64)` then nothing for 5 min | RTSP URL wrong. Re-test in Phase D.1 |
| `read failed; reconnecting in 2s` repeating | NVR rebooted or network dropped. Wait — agent reconnects. |
| iMac fans spinning hard, agent slow | Drop to 1 camera at sub-stream. Bump `sample_every_n_frames` to 12 in config.json. Restart with `sudo launchctl unload && sudo launchctl load`. |
| YOLOv8n download fails | Pre-download `yolov8n.pt` from another machine, scp it to `/opt/counteriq/edge/yolov8n.pt`, restart |
| `claim RPC returned no api_key` | Pairing token already used. Run a new INSERT in Phase B and replace token in config.json |
| Dashboard shows camera as offline | Check `tail -f /var/log/counteriq-edge.log` for last error |
| Agent stops after closing Terminal | Phase F (launchd) wasn't loaded. The foreground run only lasts as long as the Terminal stays open. |
