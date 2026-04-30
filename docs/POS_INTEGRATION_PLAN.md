# CounterIQ — POS Integration Plan

POS integration is post-MVP. Documented now so the schema and matcher are
designed correctly from day 1.

## Vendor priority
1. Clover (REST + webhooks; huge in c-stores)
2. Square (vape/smoke shop common)
3. Lightspeed Retail (vape standard)
4. Shopify POS
5. KORONA POS (vape-specific)
6. Verifone Ruby / Gilbarco Passport (gas pumps; year 2; needs middleware)

## Architecture
- OAuth start: `POST /api/pos/connect/:vendor` returns OAuth URL.
- Callback: `GET /api/pos/oauth_callback/:vendor` exchanges code, encrypts creds.
- Webhook receiver: `POST /api/pos/webhook/:vendor` HMAC-verified.
- Normalizer: per-vendor function maps payload → internal pos_transactions schema.
- Matcher worker: at +120s of each camera-side event, finds matching POS row.

## Internal pos_transactions schema
id · store_id · pos_integration_id · vendor_transaction_id · started_at ·
ended_at · total_cents · tender_type · register_id · employee_id_external ·
line_items (jsonb) · voided · refunded · no_sale · manual_price_entry ·
discount_total_cents · raw_payload (jsonb).

## Match logic
For each camera event with counter/POS zone correlation:
- Find any pos_transaction in store within ±120s of event.started_at.
- If event has SKU signal, prefer transactions containing that SKU.
- Update events.pos_match_status: matched | no_match | pending | not_applicable | unknown_no_pos.
- Severity bumps: no_match → high; matched → low.

## Derived POS-side anomaly events (pos_events table)
- no_sale_drawer (drawer opened with no transaction within 60s)
- void_with_customer_present (void during customer-at-counter)
- manual_price_entry (manual price on age-restricted SKU)
- discount_pattern (>X% or repeated to same employee)
- refund_without_visible_return (refund logged with no product-back-to-shelf
  motion in clip)

## What POS integration unlocks
- unmatched_cash_product_exchange: CV-only ~60% precision → with POS ~85%.
- unmatched_product_exit: high-value SKU lifted, no scan within 120s.
- All POS-derived events above.

## Pricing
POS integration is a +$99/month add-on. Available on Pro and Advanced tiers.
