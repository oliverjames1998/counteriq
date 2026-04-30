# CounterIQ — Audio Privacy Rules

## Default state
- `cameras.audio_supported` set from RTSP probe at camera-add time.
- `cameras.audio_enabled` = false.
- `cameras.audio_event_detection_enabled` = false.
- `stores.audio_policy_confirmed` = false.
- Edge agent: `audio_*` modules NOT imported.

## To enable (per camera, owner only)
1. Owner navigates to `/settings/privacy`.
2. Toggles audio on a specific camera.
3. AudioComplianceModal opens (5 steps):
   - Step 1: Select state.
   - Step 2: Acknowledge legal review or one-party-consent jurisdiction.
   - Step 3: Confirm signage updated to mention audio monitoring.
   - Step 4: Confirm employee notice updated and acknowledged.
   - Step 5: Acknowledge "no transcription / no conversation analysis" +
            type "ENABLE AUDIO" to confirm.
4. POST `/api/stores/:id/audio_compliance` writes a row.
5. PATCH camera flips both audio_enabled + audio_event_detection_enabled.
6. DB trigger refuses the flip without a fresh compliance row.
7. Edge picks up new config within 5 min.

## Allowed audio event types
- loud_audio_event
- possible_glass_break
- alarm_sound_detected
- after_hours_sound
- impact_sound_detected
- raised_volume_event

## Forbidden (codified in classifier wrapper)
Speech, Conversation, Narration, Babbling, Chatter, Music, Singing,
Whistling, Children shouting, Cheering — all DROPPED before reaching the
event engine. Hard-coded deny-list constant SPEECH_CLASSES.

## Recommended model
YAMNet (TFLite) for MVP. Apache 2.0. Real-time on Jetson. Filtered allow-list.

## Retention
audio_retention_days defaults to 7. CHECK constraint:
audio_retention_days <= retention_days. Daily purge cron.

## Disable
One-click master switch on /settings/privacy. Edge picks up within 60s.
ffmpeg audio process killed within 5s of disable. Buffers zero-filled.
stores.audio_policy_confirmed reset to false until re-confirmed.

## Audit logs
Every action audio-touching:
- audio.enabled / audio.disabled
- audio.compliance_confirmed
- audio.settings_changed / audio.retention_changed
- audio_clip.viewed / audio_clip.exported
- audio.enable_attempted_unauthorized

## Neutral wording (never deviate)
"Loud audio event observed near {camera}."
"Possible glass-break sound flagged for review at {camera}."
"Alarm-like sound observed at {camera}."
"Impact sound observed at {camera}."
"After-hours sound detected at {camera}."
"Raised-volume audio event flagged for review at {camera}."
