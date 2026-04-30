# Lovable Prompt — CounterIQ Landing Page

Paste this into Lovable to build the marketing landing page.

---

Build a marketing landing page for "CounterIQ — AI-assisted loss prevention
and store operations monitoring for high-risk retail."

Stack: Next.js 15, Tailwind CSS, shadcn/ui, Lucide icons. Single-page,
serious B2B aesthetic — Linear / Vercel marketing feel. Inter sans.
Slate neutrals, indigo-600 primary, no gradients of color, no emojis in
copy. Subtle dot pattern background allowed.

SECTIONS in order:

1. NAVBAR
- Left: CounterIQ wordmark.
- Center: Product, How it works, Pricing, Privacy, Pilot.
- Right: "Log in" link, "Book a demo" button (indigo).

2. HERO
- H1: "Know what happened in your store. Without watching hours of footage."
- Subhead: "CounterIQ is AI-assisted loss prevention and operations
  monitoring for vape shops, smoke shops, gas stations, c-stores, and
  liquor stores. Existing cameras. One email every morning. Starts at
  $299/month. No setup fee."
- Primary CTA: "Book a 5-minute demo" (indigo button).
- Secondary CTA: "See how it works" (anchor link).
- Visual: a clean rendered laptop/tablet showing a daily report email.

3. SOCIAL PROOF STRIP (placeholder)
Logos row: "As featured in" + 5 placeholder logos (NACS, SIGMA, etc).

4. THE PROBLEM
H2: "Your cameras already record everything. They don't tell you anything."
3-column grid:
- "Owners scrub footage less than once a month."
- "Internal shrink runs 2–8% of revenue. Most of it never gets caught."
- "Hiring a loss-prevention manager costs $4K+/month."

5. HOW IT WORKS
H2: "Plug in. Watch your inbox. Make better decisions."
4-step horizontal flow:
1. Connect existing cameras over RTSP. No NVR replacement.
2. Draw 4 zones (counter, entrance, high-value shelf, restricted).
3. Edge box runs detection 24/7. Short clips. No streaming bills.
4. 1-page report at 6am. SMS for urgent events. Audit-logged.

6. WHAT IT DETECTS
H2: "Operational events worth your attention."
3-column card grid (each card is a feature, not a person-spying claim):
- Counter Unattended — "Register left empty for X minutes during business hours."
- After-Hours Motion — "Anyone moving inside the store outside business hours."
- Restricted-Zone Entry — "Anyone entering the backroom or office area."
- Possible Product-Loss Exit — "High-value shelf interaction followed by
  exit with no matching checkout. Flagged for review."
- Unmatched Cash/Product Exchange — "Counter handoff with no matching POS
  transaction in window. Flagged for review."
- Camera + Edge Health — "Cameras offline, edge device offline."

7. PRIVACY-FIRST (THE BIG ONE)
H2: "We don't watch people. We watch patterns."
Left column: "What we do not do" — bulleted list with shield icons:
- No facial recognition
- No demographic detection
- No emotion or sentiment detection
- No speech transcription
- No conversation analysis
- No private-area monitoring
- No automatic accusations
- No automatic discipline
Right column: "How we keep it safe":
- Audio off by default. Owner-only opt-in with state-aware compliance flow.
- Customer signage and employee notice required.
- All clip access audit-logged.
- Owner can disable audio or delete all data with one button.
- Footage and reports use observational language only — "possible,"
  "observed," "flagged for review."

8. DAILY REPORT EXAMPLE
H2: "What lands in your inbox at 6am."
Show a styled rendering of the sample daily report (the Brownwood Mart
example). Caption: "Real wording from a pilot store. Names changed."

9. PRICING
H2: "No setup fee. Monthly per-store. Scaled by cameras and features."
3-card grid:

- **Starter — $299/month** — Up to 4 cameras. Daily AI report.
  Counter-unattended detection. After-hours motion alerts.
  Restricted-zone alerts. SMS + email. 30-day clip retention.
  Privacy & audit logs.

- **Pro — $399/month** (HIGHLIGHTED) — Up to 6 cameras. Everything in
  Starter, plus possible product-loss exit review, unmatched
  cash/product exchange review, better alert routing, multi-clip
  incident package viewer.

- **Advanced — $499/month** — Up to 8 cameras. Everything in Pro, plus
  longer clip retention, priority support, advanced reporting,
  stronger multi-camera event review.

Below the grid, a small "Add-ons" line in muted text:
"Add-ons: extra camera $25–$39 · POS integration +$99 · Optional audio
event detection +$49 · Extended retention +$49 · Multi-store: custom"

Footer line under pricing:
"First 10 stores lock their rate for 12 months."

10. PILOT OFFER
H2: "Paid pilot. Real product. Lock $299 for 12 months."
Bullet list:
- No setup fee.
- Starts at $299/month (Starter tier, up to 4 cameras).
- Cancel anytime after 60 days.
- First 10 stores lock their monthly rate for 12 months.
- We help configure cameras and zones during onboarding.
- One edge device included.

Value statement under the bullets (italic, slightly larger):
"If CounterIQ helps you catch one missed transaction, one product-loss
event, or one off-register cash exchange, it can pay for itself that
month."

CTA: "Apply for the pilot" (indigo button) → contact form
(name, store, city, phone, what kind of store, # of cameras).

11. FAQ
- Will CounterIQ work with my Hikvision/Dahua/Reolink/Lorex cameras?
- Do I need to replace my NVR?
- How much does CounterIQ cost? Starts at $299/month for up to 4 cameras. No setup fee.
- Is there a free trial? No. CounterIQ is a paid product from day one.
  But the first 10 stores lock $299/month for 12 months.
- Can I cancel? Yes — cancel anytime after the first 60 days.
- What if I need more cameras? Pro at $399 covers up to 6, Advanced at
  $499 covers up to 8. Extra cameras above tier limit are $25–$39 each.
- Will my rate go up? Not for the first 10 stores. Your $299 is locked
  for 12 months from install.
- Is this legal in my state?
- What about my employees — will they quit?
- Do you do facial recognition? (NO — bold)
- Do you record audio? (NO — by default. Optional, owner-only opt-in.)
- How long does install take?
- What happens if my internet goes out?

12. FOOTER
- Logo + tagline
- Columns: Product / Pricing / Privacy / Pilot / Contact
- Legal: TOS, Privacy Policy, Acceptable Use Policy
- Copyright + small SOC 2 In Progress badge

DESIGN RULES:
- Serious, operational, trustworthy.
- No "AI revolution" hype. No "catch thieves" language.
- Use only approved language from PRIVACY_RULES.md.
- Mobile responsive.
- One CTA at top, one at bottom of each major section.

Output: a deployable Next.js single-page landing site.
