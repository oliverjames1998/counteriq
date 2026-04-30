# CounterIQ - Mock Data Structure

For the Lovable clickable prototype. Use this shape until Supabase is wired.

## stores
```ts
const store = {
  id: "store-1",
  name: "Brownwood Mart",
  address: "123 Main St, Brownwood, TX",
  timezone: "America/Chicago",
  business_hours: {
    mon: { open: "09:00", close: "21:00", closed: false },
    /* ... */
  },
  retention_days: 30,
  audio_policy_confirmed: false,
  audio_retention_days: 7,
  plan_tier: "starter",
  plan_price: 299,
  rate_locked_until: "2027-04-30",  // 12 months from install
};
```

## cameras
```ts
const cameras = [
  { id:"c1", store_id:"store-1", label:"Counter Overhead",
    location:"counter", status:"online", audio_supported:true,
    audio_event_detection_enabled:false, snapshot_url:"/mock/cam1.jpg" },
  { id:"c2", store_id:"store-1", label:"Entrance Camera",
    location:"entrance", status:"online", audio_supported:true,
    audio_event_detection_enabled:false, snapshot_url:"/mock/cam2.jpg" },
  { id:"c3", store_id:"store-1", label:"High-Value Wall",
    location:"aisle", status:"online", audio_supported:false,
    audio_event_detection_enabled:false, snapshot_url:"/mock/cam3.jpg" },
  { id:"c4", store_id:"store-1", label:"Backroom Door",
    location:"backroom", status:"offline", audio_supported:false,
    audio_event_detection_enabled:false, snapshot_url:"/mock/cam4.jpg",
    last_seen_at:"yesterday 14:08" },
];
```

## zones
```ts
const zones = [
  { id:"z1", camera_id:"c1", type:"counter",
    polygon:[[0.2,0.55],[0.8,0.55],[0.8,0.95],[0.2,0.95]] },
  { id:"z2", camera_id:"c2", type:"entrance",
    polygon:[[0.3,0.0],[0.7,0.0],[0.7,0.4],[0.3,0.4]] },
  { id:"z3", camera_id:"c3", type:"shelf_high_value",
    polygon:[[0.0,0.2],[1.0,0.2],[1.0,0.7],[0.0,0.7]] },
  { id:"z4", camera_id:"c4", type:"restricted",
    polygon:[[0.0,0.0],[1.0,0.0],[1.0,1.0],[0.0,1.0]] },
];
```

## events (yesterday) - all 8
```ts
const events = [
  { id:"e1", camera_id:"c1", type:"counter_unattended", severity:"medium",
    started_at:"yesterday 14:38", ended_at:"yesterday 14:46",
    confidence:0.87, status:"new", media_type:"video",
    description:"Counter unattended for 8 minutes during business hours.",
    clip_thumbnail:"/mock/clip1.jpg" },
  { id:"e2", camera_id:"c1", type:"counter_unattended", severity:"medium",
    started_at:"yesterday 17:12", ended_at:"yesterday 17:18",
    confidence:0.72, status:"new", media_type:"video",
    description:"Counter unattended for 6 minutes during business hours.",
    clip_thumbnail:"/mock/clip2.jpg" },
  { id:"e3", camera_id:"c2", type:"after_hours_motion", severity:"high",
    started_at:"yesterday 02:14", confidence:0.78, status:"new",
    media_type:"video",
    description:"After-hours motion observed on Entrance camera.",
    clip_thumbnail:"/mock/clip3.jpg" },
  { id:"e4", camera_id:"c4", type:"restricted_zone_entry", severity:"high",
    started_at:"yesterday 19:32", confidence:0.84, status:"new",
    media_type:"video",
    description:"Person observed entering restricted backroom zone.",
    clip_thumbnail:"/mock/clip4.jpg" },
  { id:"e5", camera_id:"c3", type:"possible_product_loss_exit", severity:"medium",
    started_at:"yesterday 17:14", confidence:0.71, status:"new",
    media_type:"video", package: ["shelf","counter","exit"],
    description:"Possible product-loss exit flagged for review. High-value shelf interaction was followed by store exit with no matching checkout event found.",
    clip_thumbnail:"/mock/clip5.jpg" },
  { id:"e6", camera_id:"c1", type:"unmatched_cash_product_exchange", severity:"medium",
    started_at:"yesterday 14:38", confidence:0.62, status:"new",
    media_type:"video", pos_match_status:"unknown_no_pos",
    description:"Unmatched cash/product exchange observed at counter. No POS integration configured at this store.",
    clip_thumbnail:"/mock/clip6.jpg" },
  { id:"e7", camera_id:"c1", type:"possible_glass_break", severity:"high",
    started_at:"yesterday 19:08", confidence:0.71, status:"new",
    media_type:"audio", note:"Audio currently OFF on this camera - shown for demo",
    description:"Possible glass-break sound flagged for review at Counter Overhead.",
    waveform_thumbnail:"/mock/wave1.png" },
  { id:"e8", camera_id:"c4", type:"camera_offline", severity:"medium",
    started_at:"yesterday 14:08", confidence:1.0, status:"new",
    media_type:"video",
    description:"Backroom Door camera offline since 14:08." },
];
```

## kpi_yesterday
```ts
const kpi = {
  visits: 142,
  flagged_events: 7,
  counter_coverage_pct: 0.92,
  open_on_time: true,
};
```

## daily_report (yesterday)
Use the markdown content from `prompts/LOVABLE_DASHBOARD_PROMPT.md` (the
"MOCK DAILY REPORT" section).

## audit_log (recent)
```ts
const audit = [
  { id:"a1", action:"clip.viewed", target_id:"e1",
    user:"demo@counteriq.com", at:"today 09:14", ip:"73.x.x.x" },
  { id:"a2", action:"event.resolved", target_id:"e3",
    user:"demo@counteriq.com", at:"today 09:18" },
  { id:"a3", action:"store.created", target_id:"store-1",
    user:"demo@counteriq.com", at:"yesterday 09:00" },
];
```

## billing
```ts
const billing = {
  plan: "Starter",
  price_monthly: 299,
  rate_locked: true,
  rate_locked_until: "2027-04-30",
  next_invoice_date: "next month 1st",
  payment_method_last4: "4242",
  upgrade_options: [
    { plan: "Pro", price: 399, cameras: 6 },
    { plan: "Advanced", price: 499, cameras: 8 },
  ],
};
```
