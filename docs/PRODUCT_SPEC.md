# CounterIQ — Product Spec

## What it is
AI-assisted loss prevention and store-operations monitoring for high-risk retail
(vape, smoke, gas station, c-store, liquor). Connects to existing cameras over
RTSP. A small in-store edge device runs computer vision, flags operational
events, saves short clips, and emails the owner a 1-page daily report.

## What it observes (not who)
- Customer behavior patterns: enter, exit, shelf interaction, dwell, exit-without-checkout.
- Employee behavior patterns: counter coverage, handoff, restricted-area access.
- Store operations: open/close, traffic, peak hours, camera/edge health.

## What it never does
- Facial recognition. Demographic detection. Emotion detection.
- Speech transcription. Conversation analysis. Voice fingerprinting.
- Customer identity tracking across visits.
- Automatic discipline. Automatic accusations.
- Private-area monitoring (bathrooms, break rooms, dressing rooms, offices).

## Owner experience
1. Plug edge box into store network.
2. Connect 1–4 RTSP cameras through dashboard.
3. Draw zones (Counter, Entrance, High-Value Shelf, Restricted) on a still frame.
4. Confirm privacy + signage.
5. Get SMS for urgent events; get a 1-page email at 6am every morning.

## Event language (always)
"observed," "possible," "flagged for review," "unmatched,"
"no matching POS transaction found," "review clip."

## Event language (never)
"stole," "thief," "guilty," "caught," "criminal," "confirmed theft,"
"fight confirmed," "argument confirmed," "said," "conversation."

## MVP scope (build target)
- Clickable dashboard (Lovable)
- Marketing landing page (Lovable)
- Supabase backend (auth + schema + RLS)
- RTSP test script (1 camera)
- Counter-unattended detector (edge prototype)
- 30-second clip capture
- Daily AI report (Claude Haiku 4.5 via cron)
- 1 pilot store live within 60 days

## Non-goals at MVP
POS integration. Audio detection. Multi-store. Native mobile. Employee scoring.
Phone detection. ID-check detection. Theft-risk composite scoring.

## Stack
Next.js 15 + Tailwind + shadcn/ui · Supabase (Postgres/Auth/Storage) ·
Cloudflare R2 (clips) · FastAPI (where useful) · Python edge agent on
Jetson Orin Nano · YOLOv8n + ByteTrack · Claude Haiku 4.5 · Twilio · Resend.

## Pricing
No setup fee. Monthly per-store, scaled by camera count and feature level.

**Starter — $299/month per store**
- Up to 4 cameras
- Daily AI reports
- Incident clips
- Counter unattended detection
- After-hours motion alerts
- Restricted-zone entry alerts
- Basic SMS/email alerts
- Privacy and audit logs
- 30-day clip retention

**Pro — $399/month per store**
- Up to 6 cameras
- Everything in Starter
- Possible product-loss exit review
- Unmatched cash/product exchange review
- Better alert routing
- Multi-clip incident package viewer

**Advanced — $499/month per store**
- Up to 8 cameras
- Everything in Pro
- Longer clip retention
- Priority support
- Advanced reporting
- Stronger multi-camera event review

**Add-ons (post-MVP)**
- Extra camera: $25–$39/month
- POS integration: +$99/month
- Optional audio event detection: +$49/month
- Extended clip retention: +$49/month
- Multi-store dashboard: custom

## Pilot
Paid pilot. Not a free trial.
- No setup fee.
- Starts at $299/month (Starter, up to 4 cameras).
- Cancel anytime after 60 days.
- First 10 stores lock their monthly rate for 12 months.
- CounterIQ helps configure cameras and zones as part of onboarding.

**Value statement:**
"If CounterIQ helps you catch one missed transaction, one product-loss
event, or one off-register cash exchange, it can pay for itself that month."
