-- CounterIQ — Row Level Security policies
-- Run after schema.sql.

-- Helper functions ----------------------------------------------------
create or replace function public.user_has_store_access(p_store_id uuid)
returns boolean language sql stable as $$
  select exists(
    select 1 from store_users
    where store_id = p_store_id and user_id = auth.uid()
  );
$$;

create or replace function public.is_store_owner(p_store_id uuid)
returns boolean language sql stable as $$
  select exists(
    select 1 from store_users
    where store_id = p_store_id and user_id = auth.uid() and role = 'owner'
  );
$$;

create or replace function public.is_store_manager_or_owner(p_store_id uuid)
returns boolean language sql stable as $$
  select exists(
    select 1 from store_users
    where store_id = p_store_id and user_id = auth.uid()
      and role in ('owner','manager')
  );
$$;

-- USERS ---------------------------------------------------------------
alter table users enable row level security;
create policy users_self_read on users for select using (id = auth.uid());
create policy users_self_update on users for update using (id = auth.uid());

-- STORES --------------------------------------------------------------
alter table stores enable row level security;
create policy stores_read on stores for select
  using (user_has_store_access(id));
create policy stores_owner_update on stores for update
  using (owner_id = auth.uid());
create policy stores_owner_delete on stores for delete
  using (owner_id = auth.uid());
create policy stores_insert_self on stores for insert
  with check (owner_id = auth.uid());

-- STORE_USERS ---------------------------------------------------------
alter table store_users enable row level security;
create policy store_users_read on store_users for select
  using (user_id = auth.uid() or is_store_owner(store_id));
create policy store_users_owner_write on store_users for all
  using (is_store_owner(store_id))
  with check (is_store_owner(store_id));

-- CAMERAS -------------------------------------------------------------
alter table cameras enable row level security;
create policy cameras_read on cameras for select
  using (user_has_store_access(store_id));
create policy cameras_manager_write on cameras for all
  using (is_store_manager_or_owner(store_id))
  with check (is_store_manager_or_owner(store_id));

-- ZONES ---------------------------------------------------------------
alter table zones enable row level security;
create policy zones_read on zones for select
  using (user_has_store_access(store_id));
create policy zones_manager_write on zones for all
  using (is_store_manager_or_owner(store_id))
  with check (is_store_manager_or_owner(store_id));

-- EVENTS --------------------------------------------------------------
-- inserts come from edge service-role; bypassing RLS via service key.
alter table events enable row level security;
create policy events_read on events for select
  using (user_has_store_access(store_id));
create policy events_update_managers on events for update
  using (is_store_manager_or_owner(store_id))
  with check (is_store_manager_or_owner(store_id));

-- CLIPS ---------------------------------------------------------------
alter table clips enable row level security;
create policy clips_read on clips for select
  using (user_has_store_access(store_id));
-- writes only via service-role from edge

-- ALERTS / ALERT_ROUTES -----------------------------------------------
alter table alerts enable row level security;
create policy alerts_read on alerts for select
  using (user_has_store_access(store_id));

alter table alert_routes enable row level security;
create policy alert_routes_read on alert_routes for select
  using (user_has_store_access(store_id));
create policy alert_routes_manager_write on alert_routes for all
  using (is_store_manager_or_owner(store_id))
  with check (is_store_manager_or_owner(store_id));

-- DAILY_REPORTS -------------------------------------------------------
alter table daily_reports enable row level security;
create policy daily_reports_read on daily_reports for select
  using (user_has_store_access(store_id));

-- SETTINGS ------------------------------------------------------------
alter table settings enable row level security;
create policy settings_read on settings for select
  using (user_has_store_access(store_id));
create policy settings_owner_write on settings for all
  using (is_store_owner(store_id))
  with check (is_store_owner(store_id));

-- AUDIT_LOGS — owner read only ---------------------------------------
alter table audit_logs enable row level security;
create policy audit_owner_read on audit_logs for select using (
  exists(select 1 from stores
         where stores.id = audit_logs.store_id and stores.owner_id = auth.uid())
);
-- writes only via service-role

-- EDGE_DEVICES --------------------------------------------------------
alter table edge_devices enable row level security;
create policy edge_devices_read on edge_devices for select
  using (user_has_store_access(store_id));
create policy edge_devices_owner_write on edge_devices for all
  using (is_store_owner(store_id))
  with check (is_store_owner(store_id));

-- AUDIO_COMPLIANCE_CONFIRMATIONS -------------------------------------
alter table audio_compliance_confirmations enable row level security;
create policy compliance_insert_owner on audio_compliance_confirmations
  for insert with check (is_store_owner(store_id) and confirmed_by = auth.uid());
create policy compliance_read on audio_compliance_confirmations for select
  using (is_store_manager_or_owner(store_id));

-- POS tables — owner write, manager read -----------------------------
alter table pos_integrations enable row level security;
create policy pos_int_read on pos_integrations for select
  using (user_has_store_access(store_id));
create policy pos_int_owner_write on pos_integrations for all
  using (is_store_owner(store_id))
  with check (is_store_owner(store_id));

alter table pos_transactions enable row level security;
create policy pos_tx_read on pos_transactions for select
  using (user_has_store_access(store_id));

alter table pos_events enable row level security;
create policy pos_events_read on pos_events for select
  using (user_has_store_access(store_id));
