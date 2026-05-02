# CounterIQ — Live Project Status

**Last updated:** 2026-05-02

## TL;DR — what's done, what's next

- ✅ **Backend (FastAPI)** — code complete, 15/15 tests pass. Ready to deploy.
  Not yet deployed to Fly.io.
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
| Cameras + LTS NVR | Already installed by dealer. Static IP on `192.168.4.X`. |
| **NVR local IP** | ⚠️ **OUTSTANDING** — need this before edge install can proceed |
| Edge box | iMac at the store. Retina 4K 21.5" 2019, Intel i3, 8 GB, Sonoma 14.2.1 |
| Backend deployed to Fly.io | Not yet — needs `fly auth login` (one-time) |
| Edge agent installed | Not yet — blocked on NVR IP and backend deploy |

## Resume prompt for any new Claude session

If you're starting a fresh Claude conversation (different machine, new
session, etc.), paste this to bootstrap context fast:

```
I'm continuing the CounterIQ install at the Vapor Planet vape shop. Repo:
https://github.com/oliverjames1998/counteriq. Read STATUS.md and docs/INSTALL_RUNBOOK_MACOS.md
for context. The pilot edge box is an iMac (Retina 4K 21.5" 2019, Intel i3,
Sonoma 14.2.1). The store WiFi is "Vapor Planet" on 192.168.4.0/24. The LTS
NVR has device serial FG5757437 and a static IP somewhere on 192.168.4.X.
Backend is already coded but not deployed; dashboard is live at
app.counteriq.us. Continue from where I am: I need to find the NVR's local
IP and get the edge agent running on the iMac.
```

## Phase log

- **Phase 1–3** (pre-build): pricing locked, privacy contract written, schema designed.
- **Phase 4A** (2026-05-01): GitHub repo created, pushed.
- **Phase 4B** (2026-05-01): Supabase schema applied, verified.
- **Phase 4C** (2026-05-01): FastAPI scaffolded with privacy-by-design endpoints. 15/15 tests pass.
- **Phase 4D** (2026-05-01): Lovable dashboard wired to Supabase. Signup persists. Zones edit + persist.
- **Custom domain** (2026-05-01): app.counteriq.us live with auto-Cloudflare DNS.
- **Phase 5+6** (2026-05-02): Schema consolidated to one Supabase, FastAPI refactored to anon+JWT pass-through, edge agent written, Fly.io config + macOS runbook.
- **Phase 7 (in progress)**: First-store install at Vapor Planet vape shop.

## Single biggest unblock right now

**Find the NVR's local IP on the Vapor Planet WiFi.** Three ways:

1. **LTS Connect mobile app** → tap device (FG5757437) → settings → IP
2. **Browser to `http://192.168.4.1`** → Connected Devices → "Hikvision"
3. **HDMI display on NVR** → right-click → Menu → Configuration → Network

Once the IP is known, Phase A (Fly.io deploy) + Phase B (provision device row)
+ Phase D (configure cameras) + Phase E (first boot) of `INSTALL_RUNBOOK_MACOS.md`
take ~60 minutes total to complete the pilot install.
