-- CounterIQ — Postgres schema (run on Supabase project)
-- Idempotent where reasonable. Run once on a fresh project.

create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ============================================================
-- USERS
-- ============================================================
create table if not exists users (
  id uuid primary key default auth.uid(),
  email text unique not null,
  name text,
  phone text,
  created_at timestamptz not null default now()
);

-- ============================================================
-- STORES
-- ============================================================
create table if not exists stores (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references users(id) on delete restrict,
  name text not null,
  address text,
  timezone text not null default 'America/Chicago',
  business_hours jsonb not null default '{}',
  retention_days int not null default 30,
  audio_policy_confirmed boolean not null default false,
  audio_retention_days int not null default 7,
  customer_signage_confirmed boolean not null default false,
  customer_signage_confirmed_at timestamptz,
  customer_audio_signage_confirmed boolean not null default false,
  customer_audio_signage_confirmed_at timestamptz,
  employee_audio_notice_confirmed boolean not null default false,
  employee_audio_notice_confirmed_at timestamptz,
  jurisdiction_state text,
  plan_tier text not null default 'starter'
    check (plan_tier in ('starter','pro','advanced')),
  rate_locked_until timestamptz,
  created_at timestamptz not null default now(),
  deleted_at timestamptz,
  constraint audio_retention_le_video_retention
    check (audio_retention_days <= retention_days)
);
create index if not exists idx_stores_owner on stores(owner_id);

-- ============================================================
-- STORE_USERS (membership / RBAC)
-- ============================================================
create table if not exists store_users (
  store_id uuid not null references stores(id) on delete cascade,
  user_id uuid not null references users(id) on delete cascade,
  role text not null check (role in ('owner','manager','viewer')),
  created_at timestamptz not null default now(),
  primary key (store_id, user_id)
);
create index if not exists idx_store_users_user on store_users(user_id);

-- ============================================================
-- CAMERAS
-- ============================================================
create table if not exists cameras (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references stores(id) on delete cascade,
  label text not null,
  location text not null default 'other'
    check (location in ('counter','entrance','aisle','backroom','outside','pos','other')),
  rtsp_url_encrypted text not null,
  resolution text,
  status text not null default 'unknown'
    check (status in ('online','offline','error','unknown')),
  last_seen_at timestamptz,
  snapshot_url text,
  audio_supported boolean not null default false,
  audio_enabled boolean not null default false,
  audio_event_detection_enabled boolean not null default false,
  audio_enabled_at timestamptz,
  audio_enabled_by uuid references users(id),
  created_at timestamptz not null default now(),
  deleted_at timestamptz,
  constraint audio_detect_requires_capture
    check (audio_event_detection_enabled = false or audio_enabled = true)
);
create index if not exists idx_cameras_store on cameras(store_id, status);

-- ============================================================
-- ZONES
-- ============================================================
create table if not exists zones (
  id uuid primary key default gen_random_uuid(),
  camera_id uuid not null references cameras(id) on delete cascade,
  store_id uuid not null references stores(id) on delete cascade,
  type text not null check (type in
    ('counter','entrance','shelf_high_value','restricted','pos','backroom_door','outside')),
  label text,
  polygon jsonb not null,
  created_at timestamptz not null default now()
);
create index if not exists idx_zones_camera on zones(camera_id);

-- ============================================================
-- EVENTS
-- ============================================================
create table if not exists events (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references stores(id) on delete cascade,
  camera_id uuid not null references cameras(id) on delete cascade,
  zone_id uuid references zones(id) on delete set null,
  type text not null,
  media_type text not null default 'video'
    check (media_type in ('video','audio','video_audio')),
  started_at timestamptz not null,
  ended_at timestamptz,
  confidence numeric(3,2) not null default 0,
  severity text not null default 'info'
    check (severity in ('info','low','medium','high')),
  metadata jsonb not null default '{}',
  status text not null default 'new'
    check (status in ('new','resolved','dismissed','important')),
  resolved_by uuid references users(id),
  resolved_at timestamptz,
  linked_event_id uuid references events(id) on delete set null,
  pos_transaction_id uuid,
  pos_match_status text default 'not_applicable'
    check (pos_match_status in
           ('matched','no_match','pending','not_applicable','unknown_no_pos')),
  package_id uuid,
  created_at timestamptz not null default now()
);
create index if not exists idx_events_store_time on events(store_id, started_at desc);
create index if not exists idx_events_store_type on events(store_id, type, started_at desc);
create index if not exists idx_events_store_status on events(store_id, status, started_at desc);
create index if not exists idx_events_store_media on events(store_id, media_type, started_at desc);
create index if not exists idx_events_camera_time on events(camera_id, started_at desc);
create index if not exists idx_events_linked on events(linked_event_id);

-- ============================================================
-- CLIPS
-- ============================================================
create table if not exists clips (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references events(id) on delete cascade,
  store_id uuid not null references stores(id) on delete cascade,
  r2_key text not null,
  thumbnail_key text,
  duration_s int not null default 30,
  size_bytes bigint,
  media_type text not null default 'video'
    check (media_type in ('video','video_audio','audio')),
  has_audio boolean not null default false,
  audio_only boolean not null default false,
  audio_redacted boolean not null default false,
  role text,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null
);
create index if not exists idx_clips_event on clips(event_id);
create index if not exists idx_clips_expires on clips(expires_at);

-- ============================================================
-- ALERTS
-- ============================================================
create table if not exists alerts (
  id uuid primary key default gen_random_uuid(),
  event_id uuid references events(id) on delete set null,
  store_id uuid not null references stores(id) on delete cascade,
  channel text not null check (channel in ('sms','email','push')),
  recipient text not null,
  body text not null,
  sent_at timestamptz not null default now(),
  delivery_status text not null default 'pending',
  provider_message_id text
);
create index if not exists idx_alerts_store_time on alerts(store_id, sent_at desc);

-- ============================================================
-- ALERT_ROUTES
-- ============================================================
create table if not exists alert_routes (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references stores(id) on delete cascade,
  event_types text[] not null default '{}',
  channel text not null check (channel in ('sms','email')),
  recipient text not null,
  quiet_hours_start time,
  quiet_hours_end time,
  enabled boolean not null default true,
  created_at timestamptz not null default now()
);

-- ============================================================
-- DAILY_REPORTS
-- ============================================================
create table if not exists daily_reports (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references stores(id) on delete cascade,
  report_date date not null,
  narrative_md text not null,
  narrative_html text not null,
  stats jsonb not null default '{}',
  top_event_ids uuid[] not null default '{}',
  sent_at timestamptz,
  created_at timestamptz not null default now(),
  unique (store_id, report_date)
);

-- ============================================================
-- SETTINGS
-- ============================================================
create table if not exists settings (
  store_id uuid not null references stores(id) on delete cascade,
  key text not null,
  value jsonb not null,
  updated_at timestamptz not null default now(),
  primary key (store_id, key)
);

-- ============================================================
-- AUDIT_LOGS
-- ============================================================
create table if not exists audit_logs (
  id uuid primary key default gen_random_uuid(),
  store_id uuid references stores(id) on delete set null,
  user_id uuid references users(id) on delete set null,
  action text not null,
  target_type text,
  target_id uuid,
  metadata jsonb not null default '{}',
  ip_address inet,
  created_at timestamptz not null default now()
);
create index if not exists idx_audit_store_time on audit_logs(store_id, created_at desc);

-- ============================================================
-- EDGE_DEVICES
-- ============================================================
create table if not exists edge_devices (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references stores(id) on delete cascade,
  name text,
  pairing_token text not null,
  api_key_hash text,
  last_heartbeat_at timestamptz,
  version text,
  status text not null default 'unpaired'
    check (status in ('unpaired','online','offline')),
  created_at timestamptz not null default now()
);
create index if not exists idx_edge_store on edge_devices(store_id);

-- ============================================================
-- AUDIO_COMPLIANCE_CONFIRMATIONS
-- ============================================================
create table if not exists audio_compliance_confirmations (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references stores(id) on delete cascade,
  confirmed_by uuid not null references users(id),
  confirmed_at timestamptz not null default now(),
  jurisdiction_state text not null,
  jurisdiction_country text not null default 'US',
  customer_signage_confirmed boolean not null,
  employee_notice_confirmed boolean not null,
  audio_use_case text not null default 'security_only'
    check (audio_use_case = 'security_only'),
  acknowledged_no_transcription boolean not null,
  acknowledged_two_party_consent_review boolean not null,
  typed_confirmation text not null check (typed_confirmation = 'ENABLE AUDIO'),
  notes text,
  ip_address inet,
  user_agent text,
  check (customer_signage_confirmed and employee_notice_confirmed
         and acknowledged_no_transcription and acknowledged_two_party_consent_review)
);
create index if not exists idx_audio_compl_store on audio_compliance_confirmations(store_id, confirmed_at desc);

-- Trigger: enabling audio requires fresh compliance row + audio_policy_confirmed
create or replace function check_audio_enable_requires_compliance()
returns trigger language plpgsql as $$
begin
  if NEW.audio_event_detection_enabled = true
     and (OLD.audio_event_detection_enabled is null or OLD.audio_event_detection_enabled = false) then
    if not exists (select 1 from audio_compliance_confirmations
                   where store_id = NEW.store_id) then
      raise exception 'audio compliance confirmation required';
    end if;
    if not (select audio_policy_confirmed from stores where id = NEW.store_id) then
      raise exception 'store audio policy not confirmed';
    end if;
  end if;
  return NEW;
end$$;

drop trigger if exists cameras_audio_enable_check on cameras;
create trigger cameras_audio_enable_check
  before update on cameras
  for each row execute function check_audio_enable_requires_compliance();

-- ============================================================
-- POS (post-MVP, schema-ready now)
-- ============================================================
create table if not exists pos_integrations (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references stores(id) on delete cascade,
  vendor text not null check (vendor in ('clover','square','lightspeed','shopify','korona')),
  status text not null default 'connecting'
    check (status in ('connecting','active','paused','error')),
  oauth_credentials_encrypted text,
  webhook_secret_hash text,
  last_sync_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists pos_transactions (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references stores(id) on delete cascade,
  pos_integration_id uuid not null references pos_integrations(id) on delete cascade,
  vendor_transaction_id text not null,
  started_at timestamptz not null,
  ended_at timestamptz,
  total_cents int,
  tender_type text,
  register_id text,
  employee_id_external text,
  line_items jsonb not null default '[]',
  voided boolean not null default false,
  refunded boolean not null default false,
  no_sale boolean not null default false,
  manual_price_entry boolean not null default false,
  discount_total_cents int not null default 0,
  raw_payload jsonb not null default '{}',
  unique (pos_integration_id, vendor_transaction_id)
);
create index if not exists idx_pos_tx_store_time on pos_transactions(store_id, started_at desc);

create table if not exists pos_events (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references stores(id) on delete cascade,
  pos_transaction_id uuid references pos_transactions(id) on delete cascade,
  type text not null,
  flagged_at timestamptz not null default now(),
  metadata jsonb not null default '{}',
  linked_event_id uuid references events(id) on delete set null
);

-- FK from events.pos_transaction_id once pos_transactions exists
do $$ begin
  alter table events
    add constraint fk_events_pos_tx
    foreign key (pos_transaction_id) references pos_transactions(id) on delete set null;
exception when duplicate_object then null;
end $$;
