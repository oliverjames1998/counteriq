# CounterIQ — 60-Day Roadmap

## Week 1 (Days 1–4) — Clickable Prototype
Tasks:
- Lovable: build clickable dashboard from prompts/LOVABLE_DASHBOARD_PROMPT.md
- Lovable: build landing page from prompts/LOVABLE_LANDING_PAGE_PROMPT.md
- Domain: counteriq.com on Cloudflare DNS
- Deploy both to Vercel

Deliverable: working URLs you can show on a tablet.
Acceptance: all 14 routes navigable; banned-words linter wired in IncidentCard.

## Week 2 (Days 5–9) — Supabase Backend
Tasks:
- Run supabase/schema.sql + supabase/rls_policies.sql
- Run supabase/seed_data.sql for one demo store
- Wire Next.js to Supabase: magic-link auth, store CRUD, camera CRUD
- Encrypted RTSP creds (pgcrypto)

Deliverable: signup → onboard → add camera → draw zones with persistence.
Acceptance: cross-tenant isolation verified.

## Week 3 (Days 10–14) — Edge Prototype
Tasks:
- Order Jetson Orin Nano 8GB Dev Kit ($499)
- Run edge/rtsp_test.py against your test camera
- Run edge/counter_unattended_prototype.py for 24 hours
- Verify event posts to local SQLite, then to /api/edge/events

Deliverable: edge box detects counter_unattended events on real footage.
Acceptance: event fires within 30s of 5-min empty threshold.

## Week 4 (Days 15–18) — Clip Capture + Sync
Tasks:
- Rolling 60s frame buffer per camera
- 30s clip generation (10s pre, 20s post)
- R2 upload via presigned URL
- ClipPlayer integration in dashboard
- Audit log on view

Deliverable: click incident → clip plays in <2s.
Acceptance: 30s clips ≤8MB at 720p.

## Week 5 (Days 19–22) — Daily AI Report
Tasks:
- Vercel Cron at 06:00 local
- Claude Haiku 4.5 with prompt caching
- Sanitizer (banned-words regex) + deterministic fallback
- HTML email template via Resend

Deliverable: real report at 06:00 every day.
Acceptance: 7 consecutive days no forbidden language.

## Week 6 (Days 23–26) — Alerts
Tasks:
- Twilio SMS + Resend email
- Alert routes UI
- Quiet hours + rate limits + STOP keyword
- Copy sanitizer

Deliverable: counter-unattended ≥8 min triggers SMS within 60s.
Acceptance: rate-limit verified; STOP works.

## Week 7 (Days 27–34) — Pilot Hunt
Tasks:
- Build target list of 30 stores within 30 miles
- 5 walk-ins/day
- Demo from sales/demo_script.md
- Sign 3 paid pilots at $299/month (rate-locked 12 months)

Deliverable: 3 signed pilot agreements.
Acceptance: at least 1 install scheduled.

## Week 8 (Days 35–42) — Pilot Polish + First Paid Install
Tasks:
- Onboarding flow polish
- Install playbook (camera placement diagrams)
- Help docs (5 pages)
- Sentry + Logtail wired
- Stripe integration: $299 Starter / $399 Pro / $499 Advanced
- Pricing-lock workflow for first 10 stores (12-month rate lock)
- Tech E&O + Cyber + GL bound
- Lawyer review of TOS, Privacy Policy, signage, employee notice,
  pilot agreement (paid pilot)

Deliverable: pilot store #1 installed, billed $299/month, live.
Acceptance: first invoice paid; owner opens dashboard ≥5 of 7 days week 1.

## Week 9 (Days 43–60) — Pilot Iteration + Recruit 10
Tasks:
- Daily review of pilot store events
- Tune thresholds based on FP rate
- Capture testimonial moments
- Add detector #2 (after_hours_motion) and #3 (restricted_zone_entry)
- Bi-weekly feedback calls
- Recruit pilots #2–#10 with rate-lock close

Deliverable: 3+ paying stores at $299/month with 12-month rate lock.
Acceptance: ≥1 "I would not have known" moment from each pilot owner;
no cancellations through day 60.
