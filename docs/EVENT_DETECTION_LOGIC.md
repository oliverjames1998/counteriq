# CounterIQ — Event Detection Logic

Common: MIN_TRACK_AGE_FRAMES=6 (~1.2s @ 5fps), MIN_CONFIDENCE=0.4,
per-(camera, type) cooldowns. All language observational.

## MVP detector — counter_unattended

Build this first. It's the highest-signal, lowest-FP detector and it sells
the demo.

```
state: empty_since[camera] = None

each tick (every 5 seconds):
  if not in_business_hours:
    empty_since[camera] = None
    return

  inside = any tracked person currently inside `counter` polygon

  if inside:
    empty_since[camera] = None
  else:
    empty_since[camera] = empty_since[camera] or now()
    elapsed = now() - empty_since[camera]

    if elapsed >= 5 minutes and not already_emitted_this_window:
      emit_event(
        type='counter_unattended',
        severity='medium',
        started_at=empty_since[camera],
        ended_at=now(),
        confidence=min(1.0, elapsed_minutes / 5),
        metadata={'elapsed_s': elapsed_seconds})
      request_clip(start=empty_since[camera] + 4min, duration=30s)
      already_emitted_this_window = True

    if elapsed >= 8 minutes:
      severity = 'high'
      trigger_alert(P1)
```

False-positive guards:
- Ignore first 10 min after open and last 10 min before close.
- Per-camera cooldown 15 min.
- Owner can override "owner_present" toggle later.
- Track lifetime ≥600 ms required.

Database payload:
```json
{
  "store_id": "...",
  "camera_id": "...",
  "zone_id": "...",
  "type": "counter_unattended",
  "media_type": "video",
  "started_at": "2026-04-30T19:42:08Z",
  "ended_at":   "2026-04-30T19:47:08Z",
  "confidence": 0.87,
  "severity": "medium",
  "metadata": {"elapsed_s": 300}
}
```

Dashboard wording:
"Counter unattended for X minutes during business hours."

Daily report wording:
"Counter unattended for X minutes from {start} to {end}. [Review clip]"

SMS wording (P1, after 8 min):
"CounterIQ — {Store}. Counter unattended {N} min on {camera}.
 Review: {url}. Reply STOP to mute 1h."

## Soon (post-pilot, in order of value)
1. after_hours_motion
2. restricted_zone_entry
3. long_dwell_high_value_shelf
4. possible_product_loss_exit (multi-zone composite)
5. unmatched_cash_product_exchange (CV-only)
