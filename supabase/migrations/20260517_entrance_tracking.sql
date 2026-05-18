-- ============================================================
-- CounterIQ — Entrance Tracking migration
-- Run in Supabase SQL Editor against project ejriamgpvxrslfqsxkjp
-- ============================================================

-- 1. Add new event types to enum
ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'entry';
ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'exit';

COMMIT;

-- 2. Visitor log view — flat list of entries/exits with running occupancy
CREATE OR REPLACE VIEW v_visitor_log AS
SELECT
  e.id,
  e.store_id,
  e.camera_id,
  e.event_type,
  e.occurred_at,
  (e.occurred_at AT TIME ZONE 'America/Chicago')::time AS local_time,
  (e.occurred_at AT TIME ZONE 'America/Chicago')::date AS local_date,
  e.media_url,
  e.thumbnail_url,
  e.description,
  e.metadata,
  SUM(
    CASE
      WHEN e.event_type = 'entry' THEN 1
      WHEN e.event_type = 'exit' THEN -1
      ELSE 0
    END
  ) OVER (
    PARTITION BY e.store_id, (e.occurred_at AT TIME ZONE 'America/Chicago')::date
    ORDER BY e.occurred_at
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS occupancy_after
FROM events e
WHERE e.event_type IN ('entry', 'exit')
ORDER BY e.occurred_at DESC;

-- 3. Hourly visitor bucket view (today + history)
CREATE OR REPLACE VIEW v_visitor_hourly AS
SELECT
  store_id,
  (occurred_at AT TIME ZONE 'America/Chicago')::date AS local_date,
  EXTRACT(HOUR FROM (occurred_at AT TIME ZONE 'America/Chicago'))::int AS hour,
  COUNT(*) FILTER (WHERE event_type = 'entry') AS entries,
  COUNT(*) FILTER (WHERE event_type = 'exit')  AS exits
FROM events
WHERE event_type IN ('entry','exit')
GROUP BY 1,2,3;

-- 4. Daily visitor summary view (for the 6 AM email)
CREATE OR REPLACE VIEW v_visitor_daily AS
SELECT
  store_id,
  (occurred_at AT TIME ZONE 'America/Chicago')::date AS local_date,
  COUNT(*) FILTER (WHERE event_type = 'entry') AS total_entries,
  COUNT(*) FILTER (WHERE event_type = 'exit')  AS total_exits,
  MIN(occurred_at) FILTER (WHERE event_type = 'entry') AS first_entry_at,
  MAX(occurred_at) FILTER (WHERE event_type = 'entry') AS last_entry_at
FROM events
WHERE event_type IN ('entry','exit')
GROUP BY 1,2;

-- 5. RPC: current_occupancy(store_id)  → integer "people in store right now"
CREATE OR REPLACE FUNCTION current_occupancy(p_store_id uuid)
RETURNS int
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT GREATEST(0, COALESCE(SUM(
    CASE
      WHEN event_type = 'entry' THEN 1
      WHEN event_type = 'exit'  THEN -1
      ELSE 0
    END
  ), 0))::int
  FROM events
  WHERE store_id = p_store_id
    AND event_type IN ('entry','exit')
    AND (occurred_at AT TIME ZONE 'America/Chicago')::date
        = (now() AT TIME ZONE 'America/Chicago')::date;
$$;

GRANT EXECUTE ON FUNCTION current_occupancy(uuid) TO authenticated, anon;

-- 6. Indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_visitor_lookup
  ON events (store_id, event_type, occurred_at DESC)
  WHERE event_type IN ('entry','exit');

-- 7. Camera role + tripwire columns (optional storage of config in DB)
ALTER TABLE cameras
  ADD COLUMN IF NOT EXISTS role text DEFAULT 'counter',
  ADD COLUMN IF NOT EXISTS tripwire_line jsonb;

COMMENT ON COLUMN cameras.role IS 'counter | entrance | shelf | restricted';
COMMENT ON COLUMN cameras.tripwire_line IS 'Two normalized points [[x1,y1],[x2,y2]] for entrance tripwire';

-- Done.
