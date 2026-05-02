# CounterIQ — First-Store Install Runbook

Step-by-step procedure to bring up the **first real CounterIQ install** at a
single store. Designed so an operator (you) can complete every step in
roughly 90 minutes with a working Jetson Orin Nano in hand and at least one
RTSP-capable camera on the store network.

## Architecture (one diagram, then the steps)

```
[Store cameras] --(RTSP/TCP, AUDIO STRIPPED)--> [Jetson edge agent]
                                                       |
                                                       | HTTPS POST /api/edge/events  (X-Edge-Key)
                                                       v
                                              [counteriq-api on Fly.io]
                                                       |
                                                       | RPC ingest_edge_events  (anon key)
                                                       v
                                              [Lovable Cloud / Supabase
                                               ejriamgpvxrslfqsxkjp]
                                                       |
                                                       | RLS-scoped reads
                                                       v
                                              [app.counteriq.us dashboard]
```

**Privacy contract (verified in code):**
- ffmpeg invoked with `-an`. No audio path exists in this build.
- 4-hour tracker reset. No identity persisted across visits.
- No facial recognition, no STT, no demographic/emotion inference, ever.
- Banned-words sanitizer runs on every alert string before send.
- CI fails the build if any banned ML library appears in `requirements.txt`.

---

## Phase A — Backend deployment (one-time, 15 minutes)

### A.1 Create your Fly.io account + install flyctl

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh
```

Sign up at https://fly.io/app/sign-up if you don't already have an account.
Free tier covers our usage at the pilot stage.

### A.2 Authenticate

```bash
fly auth login
```

This opens a browser → returns a token to your terminal.

### A.3 Deploy the API

```bash
cd apps/api
fly launch --no-deploy --copy-config       # accepts the existing fly.toml
fly secrets set EDGE_KEY_PEPPER="$(openssl rand -hex 32)"
fly deploy
```

Expected output ends with:
```
Visit your newly deployed app at https://counteriq-api.fly.dev/
```

### A.4 Smoke-test the deployed API

```bash
curl https://counteriq-api.fly.dev/healthz
# → {"ok":true}

curl -i https://counteriq-api.fly.dev/api/me
# → HTTP/1.1 401 Unauthorized
```

If both work, the API is live.

---

## Phase B — Provision the device row (5 minutes)

We need an `edge_devices` row in Lovable's Supabase BEFORE the Jetson boots,
so the Jetson has a `pairing_token` to swap on first boot.

### B.1 Open the Supabase SQL editor in Lovable

1. https://lovable.dev/projects/97b46b57-0933-4dd3-be25-c8e105554b8f?view=cloud&section=sql_editor
2. Run this SQL, replacing `<store-uuid>` with your real store's UUID
   (find it via `select id, name from stores;`):

```sql
INSERT INTO edge_devices (store_id, name, pairing_token)
VALUES (
  '<store-uuid>',
  'Brownwood Jetson 01',
  encode(gen_random_bytes(16), 'hex')
)
RETURNING id, pairing_token;
```

### B.2 Copy the `pairing_token` somewhere safe

You'll paste it into the Jetson config in the next step. The token is
single-use — once the device claims it, it can't be used again.

---

## Phase C — Prep the Jetson Orin Nano (30 minutes if first time)

### C.1 Flash JetPack 6 to the microSD

Follow Nvidia's instructions: https://developer.nvidia.com/embedded/learn/get-started-jetson-orin-nano-devkit

After first boot, complete the Ubuntu setup wizard, set hostname to
`counteriq-edge-01` or similar.

### C.2 Install dependencies

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv ffmpeg git
```

### C.3 Clone the repo and prepare a venv

```bash
sudo mkdir -p /opt/counteriq
sudo chown $(whoami) /opt/counteriq
cd /opt/counteriq
git clone https://github.com/oliverjames1998/counteriq.git .
cd edge
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

YOLOv8n weights download automatically on first detection run (~6 MB).

---

## Phase D — Configure cameras + business hours (20 minutes per store)

### D.1 Get RTSP credentials from your camera/NVR

For Hikvision / generic ONVIF:
```
rtsp://USER:PASS@192.168.1.50:554/Streaming/Channels/101
```

For Reolink:
```
rtsp://USER:PASS@192.168.1.50:554/h264Preview_01_main
```

Test the URL works:
```bash
ffmpeg -an -rtsp_transport tcp -i "rtsp://..." -frames:v 1 -y /tmp/probe.jpg
```
You should see a frame written to `/tmp/probe.jpg`.

### D.2 Add the camera in the dashboard

1. Go to https://app.counteriq.us/cameras
2. Click "Add camera"
3. Paste the RTSP URL → click "Test connection"
4. Once it shows a still frame → save
5. Copy the new camera's UUID from the URL bar (`/cameras/<uuid>`)

### D.3 Draw zones

1. From the cameras list, click **Edit zones** on Counter Overhead
2. Click and drag to draw the **Counter Zone** polygon (covers the till area)
3. Save

### D.4 Build `/opt/counteriq/edge/config.json`

Copy `config.example.json` and edit with real values:

```bash
cp /opt/counteriq/edge/config.example.json /etc/counteriq/config.json
sudo chmod 600 /etc/counteriq/config.json
sudo nano /etc/counteriq/config.json
```

Set:
- `pairing_token` → from Phase B.2
- `cameras[].camera_id` → camera UUID from D.2
- `cameras[].rtsp_url` → real RTSP URL
- `cameras[].counter_polygon` → if you saved zones in the dashboard, you can
  copy the polygon from the **Settings → Audit log** detail view, OR leave
  the example default which assumes the till is in the lower-left third
  of frame
- `business_hours` → your store's actual hours

---

## Phase E — First boot (5 minutes)

### E.1 Run the agent in foreground first (sanity check)

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
INFO  [Counter Overhead] resolution: 1920x1080
```

If you see "paired" — the Jetson successfully claimed the pairing_token,
got an api_key, and saved it to `./api_key.txt`.

### E.2 Verify the dashboard shows the device

1. https://app.counteriq.us/cameras
2. Counter Overhead should show **Online** within 30 seconds
3. https://app.counteriq.us/incidents — events will land here as they fire

### E.3 Trigger a synthetic event (optional)

Walk away from the counter for 5+ minutes during business hours. Watch the
Jetson logs:
```
INFO  [Counter Overhead] event counter_unattended severity=medium elapsed=305s
INFO  synced 1 events
```

The dashboard's Recent Alerts section should refresh with the new event.

### E.4 Install as a systemd service (for unattended operation)

```bash
sudo tee /etc/systemd/system/counteriq-edge.service > /dev/null <<'EOF'
[Unit]
Description=CounterIQ Edge Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/counteriq/edge
ExecStart=/opt/counteriq/edge/venv/bin/python -m src.main --config /etc/counteriq/config.json --log-level INFO
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now counteriq-edge
sudo systemctl status counteriq-edge
journalctl -u counteriq-edge -f
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `paired (api_key length 64)` then nothing for 5 min | RTSP URL wrong or unreachable | Verify with `ffmpeg -an -rtsp_transport tcp -i "$URL" -frames:v 1 /tmp/p.jpg` from the Jetson |
| `read failed; reconnecting in 2s` repeating | Camera dropped the stream OR network flap | Check the camera's web UI; check the Jetson's network |
| Events fire but dashboard is empty | API not deployed OR `api_base_url` wrong | `curl https://counteriq-api.fly.dev/healthz` and verify config.json |
| `claim RPC returned no api_key` on first boot | pairing_token already used or wrong | Run a new INSERT in Phase B and use the fresh token |
| YOLOv8n download fails behind firewall | Pre-download `yolov8n.pt` on a machine that has internet, scp to Jetson, place at `/opt/counteriq/edge/yolov8n.pt` |
| Jetson runs hot under load | Default JetPack power mode is conservative | `sudo nvpmodel -m 0 && sudo jetson_clocks` |

---

## Privacy verification before opening for business

- [ ] Customer-facing signage at every entrance (plain-language: "video monitored")
- [ ] Counter signage at every till
- [ ] Employee acknowledgment signed by every employee
- [ ] `audio_policy_confirmed = false` in the `stores` row (default — should NOT be true unless you've completed the 5-step audio modal)
- [ ] No `audio_compliance_confirmations` row exists for this store (verify with `select count(*) from audio_compliance_confirmations where store_id = '<store-uuid>'` → expect 0)
- [ ] Edge agent log shows zero `audio_*` references

If any of those fail, halt the install. The privacy contract is non-negotiable.

---

## Day-1 ops checklist

- [ ] Edge agent is running (`systemctl is-active counteriq-edge`)
- [ ] Camera is online in dashboard
- [ ] At least one zone is drawn
- [ ] First synthetic event has fired and appears on the dashboard
- [ ] Daily report email arrives at 06:00 local the next morning
- [ ] No errors in `journalctl -u counteriq-edge --since '24h ago'`

When all six checks pass, the store is live.
