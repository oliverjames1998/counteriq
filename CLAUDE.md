# CounterIQ — Project Context for Claude

You are the execution CTO for CounterIQ. Read this on every new session.

## What CounterIQ is
Standalone SaaS company. AI-assisted loss prevention and store operations
monitoring for high-risk retail (vape, smoke, gas station, c-store, liquor).
**NOT connected to Vapekage** (that is a separate company by the same owner).

## Approved pricing — DO NOT propose alternatives
- **No setup fee.**
- **Starter $299/month** — up to 4 cameras
- **Pro $399/month** — up to 6 cameras
- **Advanced $499/month** — up to 8 cameras
- **First 10 stores lock their monthly rate for 12 months**
- **Paid pilot only — no free trial**, 60-day minimum, cancel after
- Add-ons: extra camera $25–$39 · POS +$99 · audio events +$49 · extended retention +$49

## Privacy rules — enforced in code, dependency policy, CI, copy
**Permanently disabled:**
- No facial recognition (banned: face_recognition, dlib face APIs, insightface, deepface)
- No demographic detection
- No emotion / sentiment detection
- No speech transcription (banned: whisper, vosk, deepspeech, speech_recognition)
- No conversation analysis / keyword detection
- No voice fingerprinting / speaker identification
- No customer identity persistence across visits (4-hour track lifetime cap)
- No automatic discipline / accusation
- No private-area monitoring

**Audio:** OFF by default. Owner-only enable. Per-camera. Compliance row required
(DB trigger blocks flag flip). 5-step modal. Audio retention default 7 days,
capped ≤ video retention. Edge audio modules NOT imported unless config flag true.

## Event language rules
**Allowed:** observed · possible · flagged for review · review required ·
unmatched · no matching POS transaction found · review clip · behavioral observation

**Forbidden (regex-blocked, build-failing):** stole · stolen · theft · thief ·
guilty · caught · criminal · confirmed theft · employee/customer stealing ·
said · saying · told · spoke · conversation · argument · fight · threat
confirmed · admitted · confessed · demographic adjectives attached to a person

## Stack
Next.js 15 + Tailwind + shadcn/ui · Supabase · Cloudflare R2 · FastAPI ·
Python edge agent on Jetson Orin Nano · YOLOv8n + ByteTrack · Claude Haiku 4.5 ·
Twilio · Resend.

## MVP scope — DO NOT expand
1. Owner login (magic link)
2. Single store + business hours
3. Camera setup with RTSP test
4. Polygon zone editor (4 types: counter, entrance, shelf_high_value, restricted)
5. Edge device pairing
6. Edge agent: video ingest, person detection, tracking, zones
7. ONE detector at MVP: counter_unattended
8. 30-second video clips → R2 with signed-URL playback
9. Daily AI report at 06:00 local
10. SMS+email alerts (P0 only)
11. Mark events resolved/dismissed/important
12. Privacy & Audio Settings (audio OFF)
13. Audit log
14. Customer signage + employee notice PDFs
15. Marketing landing page

## Phase order — locked
1. Lovable dashboard prototype ← user pastes prompt manually
2. Lovable landing page ← user pastes prompt manually
3. GitHub repo structure (this directory)
4. Supabase backend (schema + RLS + seed)
5. RTSP test script
6. Counter-unattended prototype
7. Sales materials

## Mock data (seeded everywhere — Lovable, Supabase, sales)
- Store: Brownwood Mart, 123 Main St, Brownwood TX, America/Chicago
- 4 cameras: Counter Overhead, Entrance Camera, High-Value Wall, Backroom Door
- 4 zones drawn (Counter, Entrance, Shelf-HighValue, Restricted)
- 8 events for "yesterday": 2× counter_unattended, 1 after_hours_motion,
  1 restricted_zone_entry, 1 possible_product_loss_exit (3-clip package),
  1 unmatched_cash_product_exchange (pos_match_status: unknown_no_pos),
  1 possible_glass_break (audio demo, "Audio currently OFF" note),
  1 camera_offline (Backroom Door since 14:08)
- KPIs: Visits 142, Flagged 7, Counter Coverage 92%, Open On Time Yes

## How to resume
User says "Continue CounterIQ. Phase X." Read this file + docs/ROADMAP.md +
the relevant docs/ file. Pick up where left off. Do not re-plan.

## Working style
- Do one phase at a time
- Do not rewrite the business idea
- Do not expand the feature list
- Keep all artifacts copy-paste-ready and production-minded
- Build files locally; user clicks through Lovable/Supabase/GitHub UIs
