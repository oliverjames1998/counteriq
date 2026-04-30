# CounterIQ — Dashboard Spec (MVP)

Stack: Next.js 15 App Router · TypeScript · Tailwind · shadcn/ui · Lucide.
Tone: Linear / Datadog / Verkada. Light + dark. Inter sans, JetBrains Mono.

## Routes (MVP)
1. `/login` — magic-link login.
2. `/onboarding/store` — name, address, timezone.
3. `/onboarding/hours` — 7-day business hours + holiday overrides.
4. `/onboarding/cameras` — add cameras via RTSP test modal.
5. `/onboarding/zones/:cameraId` — polygon zone editor.
6. `/onboarding/privacy` — privacy review + signage download + acknowledge.
7. `/dashboard` — KPIs + report preview + 4-camera grid + recent alerts.
8. `/cameras` — camera list + add/edit.
9. `/cameras/:id/zones` — zone editor.
10. `/cameras/:id/live` — single live frame (1 fps poll).
11. `/incidents` — filterable feed.
12. `/incidents/:id` — clip player + metadata + AI summary + actions.
13. `/reports` — list of daily reports.
14. `/reports/:date` — full daily report.
15. `/settings/alerts` — alert routes.
16. `/settings/hours` — business hours.
17. `/settings/privacy` — privacy + audio settings (audio OFF).
18. `/settings/team` — users / billing / data.
19. `/settings/audit` — audit log.

## Sidebar (MVP)
Home · Cameras · Incidents · Reports · Settings (Alerts, Hours,
Privacy & Audio, Team, Audit Log).

## Topbar
StoreSwitcher (single store at MVP) · alerts bell · profile menu.

## Mobile (≤768px)
Sidebar → bottom nav (Home / Incidents / Reports / Settings).
KPI tiles 2×2. Cameras 1-col. Modals → full-screen sheets.

## Components (MVP)
AppShell · Sidebar · Topbar · KPIStat · ReportPreviewCard · CameraCard ·
CameraAudioStatusBadge · IncidentCard · ClipPlayer · ZoneCanvas ·
ReportViewer · AlertSettingsForm · BusinessHoursForm · PrivacyAudioSettingsForm ·
AuditLogTable · CameraTestModal · EmptyState · LoadingState · SeverityBadge ·
StatusBadge · EventTypePill · MediaTypeIcon · ConfirmDialog · Toast ·
PrivacyStatusCard.

## Privacy banner (footer of every incident + report)
"Behavioral observations only. Events are flagged for human review.
Confirm with footage and POS records before any action."

## Mock data shape (for clickable prototype)
- 1 store: "Brownwood Mart"
- 4 cameras (audio OFF on all)
- 4 zones drawn (Counter, Entrance, High-Value Shelf, Restricted)
- 8 seeded events for "yesterday"
- 1 daily report seeded for yesterday
