# CounterIQ — Live Project Status

**Last updated:** 2026-05-02 (NVR IP captured)

## TL;DR — what's done, what's next

- ✅ **Backend (FastAPI)** — code complete, 15/15 tests pass. **Not yet deployed.**
- ✅ **Database** — single Supabase (`ejriamgpvxrslfqsxkjp`, Lovable Cloud).
  17 tables, RLS, RPCs (`claim_edge_device`, `ingest_edge_events`).
- ✅ **Dashboard** — live at https://app.counteriq.us. Signup, auth, camera
  list, incidents, zones all wired to the DB. Demo-mode badge for unauth
  visitors.
- ✅ **Marketing site** — live at https://counteriq.us. All CTAs link to
  app.counteriq.us/signup.
- ✅ **Edge agent** — code at `edge/src/`. Multi-camera, pairing flow, sync,
  heartbeat. Tested config loader.
- ✅ **Install runbooks** — Linux/Jetson at `docs/INSTALL_RUNBOOK.md`,
  macOS at `docs/INSTALL_RUNBOOK_MACOS.md`.

## First pilot install — Vapor Planet vape shop

| Item | State |
|---|---|
| Cameras + LTS NVR | Already installed by dealer. Static IP. |
| **NVR local IP** | ✅ **`192.168.4.23`** (confirmed 2026-05-02) |
| Network layout | Router `192.168.4.1` · iMac `192.168.4.22` · NVR `192.168.4.23` |
| WiFi SSID | `Vapor Planet` |
| Edge box (TEMPORARY, weeks 1–4) | iMac at the store. Retina 4K 21.5" 2019, Intel i3 4-core 3.6 GHz, 8 GB, Sonoma 14.2.1. **CPU-only inference.** Realistic capacity: 1–2 cameras at sub-stream resolution. |
| Edge box (production, week 4+) | TBD — likely Beelink Mini PC N100 (~$200) OR Jetson Orin Nano 8GB (~$499). iMac will be retired/repurposed. |
| Backend deployed to Fly.io | ⏳ Not yet — needs `fly auth login` (one-time) |
| Edge agent installed | ⏳ Not yet — RTSP test + Phase A→F of macOS runbook still to do |

## Pilot phase week-by-week

| Week | Goal |
|---|---|
| 1 (now) | Install runs end-to-end. First counter_unattended event lands on dashboard. Daily report email arrives at 6 AM next day. |
| 2 | Watch real footage. Adjust `EMPTY_THRESHOLD_S`, `counter_polygon`, `business_hours`. Goal: ≤ 1 false positive/day. |
| 3 | Demo to store team. Capture feedback on daily report content. |
| 4 | Order production hardware (Beelink N100 ~$200 or Jetson Orin Nano ~$499). Swap iMac → mini PC at the store. |
| 5+ | Scale to second store, then external paid pilots. |

## Resume prompt for any new Claude session

Paste this into a fresh Claude conversation to bootstrap context fast:

```
I'm continuing the CounterIQ install at the Vapor Planet vape shop. Repo
is PUBLIC at https://github.com/oliverjames1998/counteriq. Read STATUS.md
and docs/INSTALL_RUNBOOK_MACOS.md for full context.

Key facts:
- Edge box: iMac at the store (Retina 4K 21.5" 2019, Intel i3, Sonoma 14.2.1).
  Temporary for proof-of-concept; will swap to mini PC or Jetson at week 4+.
- Network: Vapor Planet WiFi, 192.168.4.0/24. iMac = .22, router = .1,
  NVR = .23 (confirmed). LTS NVR cloud serial = FG5757437.
- Backend (apps/api/) coded but NOT deployed to Fly.io yet.
- Dashboard live at app.counteriq.us. Database is Lovable Cloud Supabase
  (ref ejriamgpvxrslfqsxkjp). Anon-key + JWT pass-through architecture, no
  service-role key needed.

Next steps in order:
1. RTSP test from iMac Terminal:
   ffmpeg -an -rtsp_transport tcp -i "rtsp://USER:PASS@192.168.4.23:554/Streaming/Channels/102" -frames:v 1 -y /tmp/probe.jpg && open /tmp/probe.jpg
2. Phase A of INSTALL_RUNBOOK_MACOS.md — fly auth login + fly deploy.
3. Phase B — INSERT into edge_devices in Supabase SQL editor, copy pairing_token.
4. Phase D — configure /etc/counteriq/config.json with NVR IP, RTSP URL, pairing_token.
5. Phase E — run agent foreground, verify "paired" log line + dashboard online.
6. Phase F — install launchd plist for unattended 24/7 operation.

I'm at the iMac in Terminal. Walk me through the next blocker. macOS only —
no systemd or apt commands.
```

## Phase log

- **Phase 1–3** (pre-build): pricing locked, privacy contract written, schema designed.
- **Phase 4A** (2026-05-01): GitHub repo created, pushed.
- **Phase 4B** (2026-05-01): Supabase schema applied, verified.
- **Phase 4C** (2026-05-01): FastAPI scaffolded. 15/15 tests pass.
- **Phase 4D** (2026-05-01): Lovable dashboard wired to Supabase. Signup persists. Zones edit + persist.
- **Custom domain** (2026-05-01): app.counteriq.us live with auto-Cloudflare DNS.
- **Phase 5+6** (2026-05-02): Schema consolidated, FastAPI refactored to anon+JWT pass-through, edge agent written, Fly.io config + macOS runbook.
- **Phase 7 (in progress)**: First-store install at Vapor Planet vape shop.
  - 2026-05-02: NVR IP found at `192.168.4.23`. Next: RTSP test, then deploy + pair.

## Post-install cleanup (after pilot is verified running)

- [ ] `gh repo edit oliverjames1998/counteriq --visibility private --accept-visibility-change-consequences`
- [ ] Verify launchd auto-restart after iMac reboot
- [ ] Confirm 6 AM daily report email arrives
- [ ] Add missing tables to Lovable Supabase (pos_*, audio_compliance_confirmations) if pursuing Phase 2
- [ ] Set up Cloudflare R2 bucket + wire clip upload (currently event metadata only)
