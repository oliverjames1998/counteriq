# CounterIQ — MVP Scope

## Build Now (first 60 days)
- [ ] Owner signup (magic link)
- [ ] Single store creation + business hours
- [ ] Camera setup with RTSP test (probes audio-track presence; never enables)
- [ ] Encrypted RTSP credential storage
- [ ] Polygon zone editor (4 zone types)
- [ ] Edge device pairing (one edge box)
- [ ] Edge agent: video ingest, person detection, tracking, zones
- [ ] One detector: counter_unattended
- [ ] 30-second video clips → R2 with signed-URL playback
- [ ] Daily AI report (Claude Haiku 4.5) emailed at 06:00 local
- [ ] SMS + email alerts (P0 only initially)
- [ ] Mark events resolved / dismissed / important
- [ ] Privacy & Audio Settings page (audio OFF by default)
- [ ] Audit log
- [ ] Customer signage + employee notice PDFs (video-only)
- [ ] Marketing landing page

## Build Soon (post-pilot)
- after_hours_motion, restricted_zone_entry, long_dwell detectors
- possible_product_loss_exit (multi-zone composite)
- unmatched_cash_product_exchange (CV-only initial pass)
- POS integration framework (Clover + Square)
- Multi-clip "package" viewer
- Optional audio event detection (gated by compliance flow)

## Build Later
- Full POS-correlated theft scoring (refunds, voids, no-sales, manual price)
- Composite employee performance scoring
- ID-check posture detection
- Phone-on-shift pose detection
- Multi-store dashboard
- Native mobile apps
- Advanced audio classifiers (PANNs, custom models)

## Do Not Build
- Facial recognition (any form)
- Conversation transcription / speech-to-text
- Demographic detection
- Emotion / sentiment detection
- Voice fingerprinting / speaker identification
- Automatic disciplinary actions
- "Suspicious person" pre-flagging by appearance
- Hidden monitoring (no signage required)

## First demo target
A 90-second screen recording showing:
1. Live camera grid (4 thumbnails)
2. Zone editor (drawing the counter zone in 30 seconds)
3. Yesterday's daily report email
4. One counter-unattended incident with 30s clip playback
5. Privacy settings page showing audio OFF

If owners can't say "send me one" after that, nothing else matters.
