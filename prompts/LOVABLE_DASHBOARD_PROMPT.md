# Lovable Prompt — CounterIQ Dashboard

Paste this into Lovable to build the clickable frontend prototype.

---

Build a premium B2B SaaS dashboard called "CounterIQ — AI-assisted loss
prevention and store operations monitoring for high-risk retail."

STACK
Next.js 15 App Router, TypeScript, Tailwind CSS, shadcn/ui, Lucide icons.
Light + dark mode (default light). Inter sans, JetBrains Mono mono.
Operations-software aesthetic (Linear / Datadog / Verkada). Not consumer.
Not flashy. No emojis in copy. Rounded-xl cards, subtle shadow-sm, slate
neutrals, indigo-600 primary. Mobile responsive: sidebar → bottom nav, KPI
tiles 2x2, modals → full-screen sheets.

ROUTES (build all with rich mock data)

/login — centered card, magic-link email field, "Send link" button, success toast.

/onboarding/store — stepper (Store → Hours → Cameras → Zones → Privacy).
Form: name (default "Brownwood Mart"), address, timezone (default America/Chicago).

/onboarding/hours — 7-day editor + holiday overrides. Per row: open, close, Closed toggle, 24h toggle.

/onboarding/cameras — "Add camera" opens CameraTestModal. Mock RTSP test
→ frame preview + "Audio track detected: yes/no" badge. Save adds to list.

/onboarding/zones/:cameraId — polygon zone editor, type selector
(Counter, Entrance, High-Value Shelf, Restricted). Click-to-draw polygon, save/undo/delete.

/onboarding/privacy — Privacy summary card: "Facial recognition: Permanently disabled" /
"Speech transcription: Permanently disabled" / "Audio recording: OFF (default)".
Download buttons for customer signage PDF and employee notice PDF.
Acknowledge → /dashboard.

/dashboard — Top: 4 KPI tiles (Visits Yesterday: 142, Flagged Events: 7,
Counter Coverage: 92%, Open On Time: Yes). Below: yesterday's report
preview card (first 2 paragraphs + "Read full report"). Below: 4-camera
live grid with placeholder thumbnails + status dots. Below: "Recent
Alerts" strip with 3 mock alerts.

/cameras — list of 4 cameras with status dots, snapshot thumbs,
CameraAudioStatusBadge. Cameras: Counter Overhead (online, audio
supported, OFF), Entrance Camera (online, audio supported, OFF),
High-Value Wall (online, no audio track), Backroom Door (offline since
14:08, no audio track). "Add camera" button.

/cameras/:id/zones — zone editor with still-frame canvas + type selector.

/cameras/:id/live — big frame placeholder, zone overlay toggle,
CameraAudioStatusBadge, "Bookmark this moment" button.

/incidents — filter bar (date, type, camera, status, media type, severity).
Virtualized list of IncidentCards for the events listed below. Each card:
thumbnail, time, severity dot, status badge, media-type icon, neutral
1-line description, Open + Resolve/Dismiss/Mark important quick actions.

/incidents/:id — Hero ClipPlayer (or AudioClipPlayer with waveform for
audio). Metadata table (type, time, camera, zone, confidence, severity,
status). AI summary card with 2–4 sentences of NEUTRAL wording. Disclaimer
banner: "Behavioral observation only. Confirm with footage and POS records
before any action." Audit-log entry: "You viewed this clip at {time}.
Logged." Action bar: Resolve / Dismiss / Mark important / Share signed
link / Export (Owner only) / Back.

/reports — list of daily reports (last 14 days, only yesterday seeded with full content).

/reports/:date — full daily report with sections in order: Summary,
Traffic, Counter Coverage & Operations, Flagged Events, Product-Loss Risk
Events, Employee Transaction Review Events, Audio Events (only if any),
Camera/System Health, Recommended Actions for Tomorrow. End with:
"Behavioral observations only. Events are flagged for human review.
Confirm with footage and POS records before any action."

/settings/alerts — table of alert routes (event types × channel × recipient
× quiet hours × enabled). Add/Edit/Delete/Test buttons.

/settings/hours — 7-day editor + holiday overrides.

/settings/privacy — TOP: PrivacyStatusCard with three rows (shield icons):
"Facial recognition: Permanently disabled" / "Speech transcription:
Permanently disabled" / "Audio recording: OFF (default)". Below: per-camera
audio toggle list with CameraAudioStatusBadge ("Audio OFF — no audio
recorded" on all cameras). Toggle ON opens AudioComplianceModal — 5 steps:
(1) state selector, (2) legal-review checkbox, (3) signage-updated
checkbox, (4) employee-notice-acknowledged checkbox, (5) "no transcription
/ no conversation analysis" acknowledgment + type "ENABLE AUDIO" to confirm.
Submit disabled until all complete. Audio retention slider (7/14/30, default 7).
Video retention slider (14/30/60/90, default 30). Master "Disable audio on
all cameras" red button. Downloads: customer signage PDF, employee notice
PDF, audio addendum PDF. "View audio access log" link. "Delete all data"
red button (double-confirm).

/settings/team — tabs: Users / Profile / Billing / Privacy & Data. Users
tab: list with role + invite button. Billing tab: shows current plan
("Starter — $299/month, 12-month rate lock active until April 30, 2027"),
upgrade buttons (Pro $399/mo, Advanced $499/mo), payment method, invoice history.

/settings/audit — audit log table. Filters: All / Audio / Clip access /
Settings / Admin. Columns: date, user, action, target, IP. Mock entries:
clip.viewed, event.resolved, audit_logs.viewed, store.created, camera.created, zone.created.

PRICING DATA (used on Billing tab and any pricing reference)
- Starter: $299/month per store, up to 4 cameras
- Pro: $399/month per store, up to 6 cameras
- Advanced: $499/month per store, up to 8 cameras
- No setup fee
- First 10 stores lock their monthly rate for 12 months
- Add-ons: extra camera $25–$39/mo · POS integration +$99/mo · audio events +$49/mo · extended retention +$49/mo

DESIGN RULES
- Use ONLY neutral observational language anywhere. Banned words anywhere
  in copy: stole, theft, thief, guilty, caught, criminal, confirmed theft,
  employee stealing, customer stealing, employee said, customer said,
  conversation, fight confirmed, argument confirmed.
- Approved language: observed, possible, flagged for review, unmatched,
  no matching POS transaction found, review clip, behavioral observation.
- Footer line on every incident page and report: "Behavioral observations
  only. Confirm with footage and POS records before any action."
- Sidebar: Home / Cameras / Incidents / Reports / Settings (Alerts, Hours,
  Privacy & Audio, Team, Audit Log).
- Topbar: store switcher, notifications bell with badge, profile menu.

MOCK STORE
Brownwood Mart, 123 Main St, Brownwood TX, America/Chicago. Mon–Thu
09:00–21:00, Fri 09:00–22:00, Sat 10:00–22:00, Sun 11:00–20:00. Plan:
Starter $299/mo, rate locked through April 30, 2027.

MOCK CAMERAS
1. Counter Overhead — counter, online, audio supported, audio OFF.
2. Entrance Camera — entrance, online, audio supported, audio OFF.
3. High-Value Wall — aisle, online, no audio track, audio OFF.
4. Backroom Door — backroom, offline since 14:08 yesterday, no audio track.

MOCK ZONES
- Counter polygon on Counter Overhead.
- Entrance polygon on Entrance Camera.
- Shelf-High-Value polygon on High-Value Wall.
- Restricted polygon on Backroom Door.

MOCK EVENTS for "yesterday"
1. counter_unattended — Counter Overhead, 14:38–14:46, severity medium,
   confidence 0.87, status new. "Counter unattended for 8 minutes during business hours."
2. counter_unattended — Counter Overhead, 17:12–17:18, severity medium,
   confidence 0.72. "Counter unattended for 6 minutes during business hours."
3. after_hours_motion — Entrance Camera, 02:14, severity high, confidence 0.78.
   "After-hours motion observed on Entrance camera."
4. restricted_zone_entry — Backroom Door, 19:32, severity high, confidence 0.84.
   "Person observed entering restricted backroom zone."
5. possible_product_loss_exit — High-Value Wall + Entrance Camera, 17:14,
   severity medium, confidence 0.71, 3-clip package (shelf interaction /
   counter window / exit). "Possible product-loss exit flagged for review.
   High-value shelf interaction was followed by store exit with no matching
   checkout event found."
6. unmatched_cash_product_exchange — Counter Overhead, 14:38, severity
   medium, confidence 0.62, pos_match_status "unknown_no_pos". "Unmatched
   cash/product exchange observed at counter. No POS integration configured at this store."
7. possible_glass_break — Counter Overhead, 19:08, severity high,
   confidence 0.71, media_type audio (note: "Audio currently OFF on this
   camera — shown for demo"). "Possible glass-break sound flagged for review at Counter Overhead."
8. camera_offline — Backroom Door, 14:08, severity medium, confidence 1.0.
   "Backroom Door camera offline since 14:08."

MOCK DAILY REPORT (markdown for /reports/yesterday)

# Brownwood Mart — Yesterday

**Summary**
Steady day. 142 customer visits (+12% vs 30-day average). Two unattended-register events flagged for review. After-hours motion observed at 2:14am on the Entrance camera. One possible product-loss exit at 5:14pm and one unmatched cash/product exchange at 2:38pm flagged for review.

**Traffic**
- Visits: 142 (vs 30-day average of 127)
- Peak hours: 4–6pm

**Counter Coverage & Operations**
- Opened at 9:06 (scheduled 9:00) — 6 minutes late.
- Closed at 9:00 — on time.
- Counter coverage: 92%.
- Two unattended-register events at 14:38 (8 min) and 17:12 (6 min). [Review clip]

**Flagged Events**
1. **2:14am** — After-hours motion observed on Entrance camera. [Review clip]
2. **7:32pm** — Person observed entering restricted backroom zone. [Review clip]
3. **2:38pm** — Counter unattended for 8 minutes during business hours. [Review clip]

**Product-Loss Risk Events**
1. **5:14pm** — Possible product-loss exit flagged for review. High-value shelf interaction observed; no matching checkout event found before exit. [Review clip package]

**Employee Transaction Review Events**
1. **2:38pm** — Unmatched cash/product exchange observed at counter. POS integration is not configured at this store, so no matching transaction check is available. [Review clip package]

**Camera / System Health**
- Backroom Door camera offline since 14:08. All other cameras online.

**Recommended Actions for Tomorrow**
- Review the 2:14am after-hours motion clip first.
- Review the 5:14pm product-loss exit clip package.
- Review the 2:38pm counter / exchange clip package.
- Restore the Backroom Door camera connection.

---
*Behavioral observations only. Events are flagged for human review. Confirm with footage and POS records before any action.*

Output: a fully clickable Next.js app I can deploy to Vercel.
