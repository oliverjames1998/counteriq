# Phase 4D — Lovable dashboard wired to Supabase

**Status:** Complete with caveats.
**Date:** 2026-05-01

## What was wired

The Store Guardian Lovable project (UUID `97b46b57-0933-4dd3-be25-c8e105554b8f`) now reads
and writes to a real Supabase database for:

- Auth (email + password signup/login, session persistence)
- `stores`, `cameras`, `events`, `zones` (live reads + writes)
- Audit-log entries on incident resolve / dismiss / clip-viewed
- `useStore()` + `data-api.ts` hook with mock-fallback for every table
- Demo-mode badge in the topbar when env vars are missing
- Auto-seed on first signup: 1 store + 4 cameras + 8 events + 8 zones (counter + entrance per camera)

**Verified end-to-end:**
- Anonymous visitor → mock dashboard renders, no console errors
- Signup at `/signup` with `phase4d-test-20260501@counteriq.us` succeeded
- Dashboard, Cameras, Incidents render live data scoped to the new user
- Zone display and persistence verified across browser refresh

## ⚠️ Critical architectural caveat — TWO Supabase projects exist

The dashboard talks to **Lovable Cloud's auto-provisioned Supabase project**, not the
project we built our schema in.

| | Project ref | Owned by | Schema | Use today |
|---|---|---|---|---|
| **Lovable's DB** | `ejriamgpvxrslfqsxkjp` | Lovable Cloud (auto-provisioned) | 9 tables, Lovable-generated names (`plan`, `starts_at`, `rate_lock_until`) | Frontend dashboard reads/writes |
| **Our DB** | `oszjbuzqiavegyfwxkif` | Direct Supabase project | 17 tables per `supabase/schema.sql` (`plan_tier`, `started_at`, `rate_locked_until`, plus `audit_logs`, `edge_devices`, `audio_compliance_confirmations`, `pos_*`, `daily_reports`) | Phase 4C FastAPI points here. Currently empty. |

### Why this happened

Lovable Cloud (the "Cloud" tab in its editor) defaults to its own managed Supabase
when no foreign project is linked. The OAuth flow to link `oszjbuzqiavegyfwxkif`
looped on 2026-05-01 and was abandoned in favor of getting the dashboard wired to
*a* real DB. Lovable's chat then provisioned schema directly into its Cloud DB.

### Schema deltas vs our spec

Lovable's schema is missing tables that are required for the full edge-agent /
backend pipeline:

- `audit_logs` — exists conceptually inside Lovable; verify columns
- `edge_devices` — **missing**
- `audio_compliance_confirmations` — **missing** (privacy contract requires this for any audio enable)
- `pos_integrations`, `pos_transactions`, `pos_events` — **missing**
- `daily_reports` — **missing as a table** (Lovable inlines the daily report copy in another store)
- The `cameras_audio_enable_check` trigger that blocks audio enable without a compliance row — **not present**

Column-name divergence (Lovable → ours):
- `stores.plan` → `stores.plan_tier`
- `stores.rate_lock_until` → `stores.rate_locked_until`
- `events.starts_at` → `events.started_at`

## Phase 5A (next): Consolidation

Two viable paths, decide before installing the first real store:

**Path A — Make Lovable's DB canonical.** Tell Lovable to add the missing tables,
triggers, and RLS policies via a chat instruction that pastes the relevant
sections from `supabase/schema.sql` and `supabase/rls_policies.sql`. Repoint
`apps/api/.env.local` at `ejriamgpvxrslfqsxkjp` (need to retrieve service-role
key from Lovable Cloud panel). Decommission `oszjbuzqiavegyfwxkif`.

**Path B — Make our DB canonical.** Re-attempt the OAuth link from Lovable Cloud
to `oszjbuzqiavegyfwxkif`. Tell Lovable to switch its Supabase client to read
`VITE_SUPABASE_URL` from env, regenerate types from our schema, and rewrite
queries to match our column names. Heavier but better long-term ownership.

### Recommended: **Path A** for speed, with the understanding that we don't fully own Lovable Cloud's project
- Lovable Cloud is still real Supabase; export/migration is possible if we ever leave the platform
- Faster path to a working pilot
- Privacy triggers and missing tables can be added in one focused chat session

## Files NOT changed in Phase 4D

The repo state from Phase 4C is untouched. No new commits required for the wiring
(Lovable manages its own code and schema in the Lovable Cloud workspace, not our
repo). This `PHASE_4D_NOTES.md` is the only artifact added.

## Open items

- [ ] Retrieve `ejriamg...` publishable + service-role keys from Lovable Cloud panel and store in `apps/api/.env.local` (replacing `oszjbuzqiavegyfwxkif` keys) when starting Phase 5A
- [ ] Add the 7 missing tables + the `cameras_audio_enable_check` trigger + RLS policies to Lovable's Supabase via a Phase 5A chat instruction
- [ ] Disable email confirmation in Lovable's Supabase Auth settings if it's currently off (Lovable's signup completed without an email click — confirmation is likely already off; verify)
- [ ] Decide whether to keep `oszjbuzqiavegyfwxkif` as the canonical and migrate Lovable to it instead, before Phase 5A locks in the dual-DB direction
