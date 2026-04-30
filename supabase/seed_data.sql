-- CounterIQ — Demo seed data
-- Run AFTER schema + rls. Creates one demo store + cameras + zones + events.
-- Replace OWNER_USER_ID with the auth.users id of your demo owner.

-- INSTRUCTIONS:
-- 1. Sign up in your Next.js app with email demo@counteriq.com via magic link.
-- 2. Find that user's id in Supabase Auth dashboard.
-- 3. Replace 'OWNER_USER_ID_HERE' below.
-- 4. Run this file.

do $$
declare
  v_owner uuid := 'OWNER_USER_ID_HERE'::uuid;
  v_store uuid;
  v_cam_counter uuid;
  v_cam_entrance uuid;
  v_cam_wall uuid;
  v_cam_back uuid;
  v_zone_counter uuid;
  v_zone_entrance uuid;
  v_zone_shelf uuid;
  v_zone_restricted uuid;
begin
  -- ensure user row exists
  insert into users (id, email, name)
  values (v_owner, 'demo@counteriq.com', 'Demo Owner')
  on conflict (id) do nothing;

  -- store (Starter plan, rate locked 12 months)
  insert into stores (
    owner_id, name, address, timezone, business_hours,
    retention_days, plan_tier, rate_locked_until
  )
  values (
    v_owner, 'Brownwood Mart', '123 Main St, Brownwood, TX',
    'America/Chicago',
    '{"mon":{"open":"09:00","close":"21:00","closed":false},
      "tue":{"open":"09:00","close":"21:00","closed":false},
      "wed":{"open":"09:00","close":"21:00","closed":false},
      "thu":{"open":"09:00","close":"21:00","closed":false},
      "fri":{"open":"09:00","close":"22:00","closed":false},
      "sat":{"open":"10:00","close":"22:00","closed":false},
      "sun":{"open":"11:00","close":"20:00","closed":false}}'::jsonb,
    30, 'starter', now() + interval '365 days'
  )
  returning id into v_store;

  insert into store_users (store_id, user_id, role)
  values (v_store, v_owner, 'owner');

  -- cameras (audio off everywhere)
  insert into cameras (store_id, label, location, rtsp_url_encrypted, status, audio_supported)
  values (v_store, 'Counter Overhead', 'counter', 'enc:placeholder', 'online', true)
  returning id into v_cam_counter;
  insert into cameras (store_id, label, location, rtsp_url_encrypted, status, audio_supported)
  values (v_store, 'Entrance Camera', 'entrance', 'enc:placeholder', 'online', true)
  returning id into v_cam_entrance;
  insert into cameras (store_id, label, location, rtsp_url_encrypted, status, audio_supported)
  values (v_store, 'High-Value Wall', 'aisle', 'enc:placeholder', 'online', false)
  returning id into v_cam_wall;
  insert into cameras (store_id, label, location, rtsp_url_encrypted, status, audio_supported, last_seen_at)
  values (v_store, 'Backroom Door', 'backroom', 'enc:placeholder', 'offline', false,
          (current_date - 1) + time '14:08')
  returning id into v_cam_back;

  -- zones (normalized polygon coords [0..1])
  insert into zones (camera_id, store_id, type, label, polygon)
  values (v_cam_counter, v_store, 'counter', 'Main register',
          '[[0.2,0.55],[0.8,0.55],[0.8,0.95],[0.2,0.95]]'::jsonb)
  returning id into v_zone_counter;

  insert into zones (camera_id, store_id, type, label, polygon)
  values (v_cam_entrance, v_store, 'entrance', 'Front door',
          '[[0.3,0.0],[0.7,0.0],[0.7,0.4],[0.3,0.4]]'::jsonb)
  returning id into v_zone_entrance;

  insert into zones (camera_id, store_id, type, label, polygon)
  values (v_cam_wall, v_store, 'shelf_high_value', 'Vape wall',
          '[[0.0,0.2],[1.0,0.2],[1.0,0.7],[0.0,0.7]]'::jsonb)
  returning id into v_zone_shelf;

  insert into zones (camera_id, store_id, type, label, polygon)
  values (v_cam_back, v_store, 'restricted', 'Backroom',
          '[[0.0,0.0],[1.0,0.0],[1.0,1.0],[0.0,1.0]]'::jsonb)
  returning id into v_zone_restricted;

  -- yesterday's events (8 total per master build pack)
  insert into events (store_id, camera_id, zone_id, type, started_at, ended_at,
                      confidence, severity, metadata, status)
  values
  (v_store, v_cam_counter, v_zone_counter, 'counter_unattended',
   (current_date - 1) + time '14:38', (current_date - 1) + time '14:46',
   0.87, 'medium', '{"elapsed_s":480}'::jsonb, 'new'),
  (v_store, v_cam_counter, v_zone_counter, 'counter_unattended',
   (current_date - 1) + time '17:12', (current_date - 1) + time '17:18',
   0.72, 'medium', '{"elapsed_s":360}'::jsonb, 'new'),
  (v_store, v_cam_entrance, v_zone_entrance, 'after_hours_motion',
   (current_date - 1) + time '02:14', null,
   0.78, 'high', '{}'::jsonb, 'new'),
  (v_store, v_cam_back, v_zone_restricted, 'restricted_zone_entry',
   (current_date - 1) + time '19:32', null,
   0.84, 'high', '{}'::jsonb, 'new'),
  (v_store, v_cam_wall, v_zone_shelf, 'possible_product_loss_exit',
   (current_date - 1) + time '17:14', null,
   0.71, 'medium', '{"package":"shelf+counter+exit"}'::jsonb, 'new'),
  (v_store, v_cam_counter, v_zone_counter, 'unmatched_cash_product_exchange',
   (current_date - 1) + time '14:38', null,
   0.62, 'medium', '{"pos_match_status":"unknown_no_pos"}'::jsonb, 'new'),
  (v_store, v_cam_counter, v_zone_counter, 'possible_glass_break',
   (current_date - 1) + time '19:08', null,
   0.71, 'high', '{"audio_demo":true,"note":"Audio currently OFF on this camera"}'::jsonb, 'new'),
  (v_store, v_cam_back, null, 'camera_offline',
   (current_date - 1) + time '14:08', null,
   1.00, 'medium', '{}'::jsonb, 'new');

  -- daily report
  insert into daily_reports (store_id, report_date, narrative_md, narrative_html, stats, sent_at)
  values (
    v_store,
    current_date - 1,
    '# Brownwood Mart — Yesterday' || E'\n\n' ||
    '**Summary**' || E'\n' ||
    'Steady day. 142 customer visits (+12% vs 30-day average). Two unattended-register events flagged for review. After-hours motion observed at 2:14am.' || E'\n\n' ||
    '**Traffic**' || E'\n' || '- Visits: 142' || E'\n\n' ||
    '**Counter Coverage & Operations**' || E'\n' ||
    '- Counter coverage: 92%.' || E'\n' ||
    '- Two unattended-register events at 14:38 (8 min) and 17:12 (6 min). [Review clip]' || E'\n\n' ||
    '**Flagged Events**' || E'\n' ||
    '1. **2:14am** — After-hours motion observed on Entrance camera. [Review clip]' || E'\n' ||
    '2. **7:32pm** — Person observed entering restricted backroom zone. [Review clip]' || E'\n\n' ||
    '---' || E'\n' ||
    '*Behavioral observations only. Events are flagged for human review. Confirm with footage and POS records before any action.*',
    '<h1>Brownwood Mart — Yesterday</h1>',
    '{"visits":142,"counter_coverage_pct":0.92,"flagged_events":4,"unattended_minutes_total":14}'::jsonb,
    now()
  );
end $$;
