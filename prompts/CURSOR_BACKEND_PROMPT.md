# Cursor Prompt — CounterIQ Backend (Supabase + FastAPI)

Paste into Cursor in a fresh /counteriq repo with /apps/api scaffolded.

---

Build the CounterIQ backend. Stack: Supabase (Postgres + Auth + Storage),
FastAPI (Python 3.11) for ffmpeg-heavy endpoints, Cloudflare R2 for clip
storage, Resend for email, Twilio for SMS.

CONTEXT
- Privacy rules (NEVER violate): no facial recognition, no STT, no audio
  by default, no demographic/emotion inference. Block these at dependency
  level. CI fails if any are added: face_recognition, dlib face APIs,
  whisper, vosk, deepspeech, speech_recognition, insightface, deepface.
- Banned words in any LLM output or alert copy: stole, theft, thief,
  guilty, caught, criminal, confirmed theft, said, conversation,
  fight/argument confirmed.
- Approved words: observed, possible, flagged for review, unmatched,
  review clip, behavioral observation.

TASKS

1. /supabase/schema.sql is already written. Apply it. Add indexes.
2. /supabase/rls_policies.sql is already written. Apply it. Verify with
   pgTAP tests that user A cannot select/update/delete user B's data.
3. Build FastAPI app at /apps/api/app/main.py with these endpoints (all
   JSON, all Zod/Pydantic-validated):

   AUTH
   - GET  /api/me
   - PATCH /api/me

   STORES
   - POST /api/stores            (create)
   - GET  /api/stores            (list user's)
   - GET  /api/stores/:id
   - PATCH /api/stores/:id
   - DELETE /api/stores/:id      (soft delete + 30-day purge schedule)

   CAMERAS
   - POST /api/cameras/test      (probes RTSP via ffmpeg, returns frame
                                  base64 + audio_supported boolean; never
                                  enables audio)
   - POST /api/cameras
   - GET  /api/cameras/:id
   - PATCH /api/cameras/:id      (audio fields owner-only)
   - DELETE /api/cameras/:id
   - POST /api/cameras/:id/snapshot
   - GET  /api/cameras/:id/snapshot/latest

   ZONES
   - POST/PATCH/DELETE /api/zones, GET /api/cameras/:id/zones

   EVENTS
   - POST /api/edge/events       (X-Edge-Key auth; batch up to 100)
   - GET  /api/events            (filter: store_id, from, to, type,
                                  media_type, status, camera_id, cursor, limit)
   - GET  /api/events/:id
   - PATCH /api/events/:id       (status update; manager+)

   CLIPS
   - POST /api/edge/clips/presign (X-Edge-Key; returns R2 PUT URL)
   - POST /api/edge/clips
   - GET  /api/clips/:id/url     (signed URL 15-min; logs audit_logs)
   - GET  /api/clips/:id/thumbnail

   ALERTS
   - POST/PATCH/DELETE /api/alert_routes
   - GET /api/alerts
   - POST /api/internal/alerts/dispatch (worker)

   REPORTS
   - POST /api/internal/reports/generate (cron)
   - GET  /api/reports?store_id=
   - GET  /api/reports/:store_id/:date

   EDGE
   - POST /api/edge/pair (one-time)
   - GET  /api/edge/config (X-Edge-Key)
   - POST /api/edge/heartbeat (X-Edge-Key)

4. RTSP credentials encrypted with pgcrypto + per-store key.
5. Edge auth: per-device API key (sha256 hashed in DB).
6. Implement /api/internal/reports/generate:
   - Pull yesterday's events for store
   - Compute stats (visits, peak_hours, counter_coverage_pct, opened_at,
     closed_at, unattended_minutes_total)
   - Send to Claude Haiku 4.5 with the system prompt below
   - Run sanitizer (banned-words regex; if violation, regenerate twice;
     if still violates, deterministic fallback template)
   - Save daily_reports row, send via Resend
7. Sanitizer is in /packages/shared-types/banned-words.ts (TS) and
   /apps/api/app/util/sanitizer.py (Py). Same regex source.

LLM SYSTEM PROMPT for daily report (verbatim):

You are CounterIQ's daily store-operations analyst. You write concise,
professional, factually restrained daily reports for retail business
owners. HARD RULES: Use neutral, observational language only. Phrase
loss-related events as "possible," "observed," "unmatched," "flagged for
review." NEVER describe people by race, ethnicity, gender, age, or
assumed identity. NEVER name employees — use "Shift A," "the closer,"
"register attendant." Do not invent events. Total length under 450 words.
End every report with this exact line: "Behavioral observations only.
Events are flagged for human review. Confirm with footage and POS records
before any action."

Output sections: Summary, Traffic, Counter Coverage & Operations, Flagged
Events, Recommended Actions for Tomorrow.

8. Tests (pytest):
   - Unit: polygon hit, cooldown, business-hours timezone math, sanitizer.
   - Integration: auth flow, camera test (against mediamtx), event
     ingestion 200/422, clip URL signing + audit log, report generation.
9. CI workflow .github/workflows/dep-policy.yml fails build if any banned
   library is in requirements.txt.
10. Deploy: Fly.io for FastAPI, Vercel for Next.js. Env vars in Vercel
    dashboard + Fly secrets.

Run instructions in /apps/api/README.md.

Acceptance:
- New user can sign up, create store, add a real camera by RTSP URL,
  draw zones, all persisted.
- Edge can pair, fetch config, post heartbeat, post events, post clips.
- Daily report generates and emails successfully on a seeded events set.
- Sanitizer rejects 100% of fixtures with banned words.
- Cross-tenant RLS verified.
