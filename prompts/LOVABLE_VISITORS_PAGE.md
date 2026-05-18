# Lovable Prompt — Visitors Page

Paste this whole block into the Lovable AI builder for the CounterIQ dashboard.

---

Build a new dashboard route at `/visitors` (and add a "Visitors" item to the
left-nav, between "Incidents" and "Cameras"). It shows real-time and
historical foot-traffic data for the selected store.

## Data sources (Supabase project `ejriamgpvxrslfqsxkjp`, already wired)

All data must come from Supabase — no mock data. Use the existing session's
store context (same pattern as the Incidents and Cameras pages).

1. **Current occupancy** — call RPC `current_occupancy(p_store_id)` returns
   `int`. Poll every 10 seconds.

2. **Today's visitor log** — query view `v_visitor_log` filtered by
   `store_id = currentStoreId` and `local_date = today (America/Chicago)`,
   ordered by `occurred_at DESC`. Columns available: `id`, `event_type`
   ('entry'|'exit'), `occurred_at`, `local_time`, `media_url`,
   `thumbnail_url`, `description`, `occupancy_after`.

3. **Hourly chart** — query view `v_visitor_hourly` filtered by `store_id`
   and `local_date = today`. Returns `hour` (0-23), `entries`, `exits` per
   row.

4. **Daily summary** — query view `v_visitor_daily` filtered by `store_id`
   for last 14 days. Returns `local_date`, `total_entries`, `total_exits`,
   `first_entry_at`, `last_entry_at`.

## Page layout

### Top row (4 KPI cards)

- **In Store Now** — large number from `current_occupancy` RPC; subtitle
  "live, updates every 10s"
- **Today's Visitors** — `total_entries` from `v_visitor_daily` filtered to
  today; subtitle shows the delta vs same day last week
- **First Customer** — formatted time from `first_entry_at`
- **Peak Hour** — the hour with the highest `entries` from
  `v_visitor_hourly`; subtitle shows the count

### Second row — Hourly chart

Bar chart, 24 hourly buckets on x-axis (label "9a", "10a", "11a"…),
y-axis = entries. Use shadcn `recharts`. Color the current hour differently.

Below the chart: a date picker (defaults to today) that re-queries
`v_visitor_hourly` for the selected date.

### Third row — Live Visitor Log

Two-column responsive list, newest first. Each row is a card:

- **Left:** time in 12-hour format (HH:MM AM/PM), big and bold
- **Right top:** badge — green "ENTERED" for entry, gray "EXITED" for exit
- **Right body:** `description` ("Customer entered store" / "Customer
  exited store")
- **Right footer:** small text "In store after: N" (from `occupancy_after`)
- **Click-through:** if `media_url` is present, clicking the row opens a
  modal with the 10-second clip (use the existing video modal pattern from
  the incident detail page, public Supabase Storage URL).

Infinite scroll or "Load more" button.

### Fourth row — Last 14 days summary

A simple table:

| Date       | Visitors | First | Last  | vs Avg |
|------------|----------|-------|-------|--------|
| Today      | 47       | 9:02  | —     | +12%   |
| Yesterday  | 41       | 9:11  | 11:52p| +4%    |
| ...        |          |       |       |        |

`vs Avg` is the percent delta vs the trailing 7-day average for that day-of-week.

## Empty state

If there are zero visitor events yet for today, show: "No visitors counted
yet today. The entrance camera is watching — first entry will appear here
the moment someone walks in."

## Auto-refresh

The "In Store Now" card and the Live Visitor Log should auto-refresh every
10 seconds (no full page reload — just re-fetch those queries).

## Permissions / RLS

All views are already store-scoped via RLS. Use the authenticated user's
session. No service role on the client.

## Things to NOT include

- No customer identity / face / demographic columns (privacy contract)
- No conversation transcripts or audio
- No "who" — only "how many" and "when"

When done, send me the deployed preview URL and confirm:
1. Visitors page appears in the left nav
2. KPI cards render real numbers (will be 0/null until first crossing fires)
3. Hourly chart renders 24 buckets
4. Live log empty-state message shows correctly
5. Click on a row with a media_url opens the video modal
