# CounterIQ

AI-assisted loss prevention and store operations monitoring for high-risk
retail. Existing cameras. One email every morning. Privacy-first.

**Pricing:** $299 / $399 / $499 per store per month. No setup fee.
First 10 stores lock their rate for 12 months.

## Repo structure

```
counteriq/
  CLAUDE.md           — project context for AI assistants
  docs/               — product spec, MVP scope, privacy rules, roadmap
  prompts/            — Lovable + Cursor + Claude review prompts
  supabase/           — schema.sql, rls_policies.sql, seed_data.sql
  edge/               — Python edge agent (RTSP + counter-unattended prototype)
  web/                — Next.js dashboard (built from Lovable prompt)
  sales/              — cold texts, emails, demo script, pilot agreement
```

## Quickstart

1. Read `docs/ROADMAP.md` for phase order
2. Read `CLAUDE.md` for the privacy + pricing contract
3. Phase 1: paste `prompts/LOVABLE_DASHBOARD_PROMPT.md` into lovable.dev
4. Phase 4: paste `supabase/schema.sql` then `rls_policies.sql` into Supabase SQL editor
5. Phase 5: `cd edge && python rtsp_test.py rtsp://USER:PASS@IP:554/...`

## Privacy contract

CounterIQ does not do facial recognition, speech transcription, demographic
detection, or emotion inference. Audio is OFF by default. See
`docs/PRIVACY_RULES.md` and `docs/AUDIO_PRIVACY_RULES.md`.
