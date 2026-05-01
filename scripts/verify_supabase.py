"""Verify Supabase connection + table presence via PostgREST OpenAPI spec."""
from __future__ import annotations

import os
import sys
import urllib.request
import urllib.error
import json
from pathlib import Path

EXPECTED_TABLES = [
    "users",
    "stores",
    "store_users",
    "cameras",
    "zones",
    "events",
    "clips",
    "alerts",
    "alert_routes",
    "daily_reports",
    "settings",
    "audit_logs",
    "edge_devices",
    "audio_compliance_confirmations",
    "pos_integrations",
    "pos_transactions",
    "pos_events",
]


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def fetch_openapi(url: str, key: str) -> dict:
    req = urllib.request.Request(
        f"{url.rstrip('/')}/rest/v1/",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/openapi+json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def probe_table(url: str, key: str, table: str) -> tuple[int, int]:
    """Return (http_status, exact_row_count). row_count = -1 on failure."""
    req = urllib.request.Request(
        f"{url.rstrip('/')}/rest/v1/{table}?select=*&limit=0",
        method="GET",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Prefer": "count=exact",
            "Range-Unit": "items",
            "Range": "0-0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            cr = resp.headers.get("Content-Range", "")
            count = int(cr.split("/")[-1]) if "/" in cr and cr.split("/")[-1].isdigit() else -1
            return resp.status, count
    except urllib.error.HTTPError as e:
        return e.code, -1


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    env = load_env(repo_root / ".env.local")
    url = env.get("SUPABASE_URL")
    secret = env.get("SUPABASE_SECRET_KEY") or env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not secret:
        print("ERROR: SUPABASE_URL and SUPABASE_SECRET_KEY must be set in .env.local")
        return 2

    print(f"Connecting to: {url}")
    try:
        spec = fetch_openapi(url, secret)
    except Exception as e:
        print(f"ERROR: failed to reach PostgREST OpenAPI: {e}")
        return 3

    definitions = spec.get("definitions", {}) or spec.get("components", {}).get("schemas", {}) or {}
    found_tables = sorted(definitions.keys())
    print(f"Connected. PostgREST schemas exposed: {len(found_tables)}\n")

    missing = [t for t in EXPECTED_TABLES if t not in definitions]
    extra = [t for t in found_tables if t not in EXPECTED_TABLES]

    print(f"{'Table':<38} {'Cols':>5}  {'Rows':>6}  {'HTTP':>5}")
    print("-" * 60)
    ok = 0
    for t in EXPECTED_TABLES:
        if t not in definitions:
            print(f"{t:<38} {'--':>5}  {'--':>6}  {'MISS':>5}")
            continue
        cols = len((definitions[t].get("properties") or {}))
        status, count = probe_table(url, secret, t)
        rows = str(count) if count >= 0 else "?"
        print(f"{t:<38} {cols:>5}  {rows:>6}  {status:>5}")
        if status == 200:
            ok += 1

    print("\nSummary")
    print(f"  Expected tables:  {len(EXPECTED_TABLES)}")
    print(f"  Found + reachable: {ok}")
    print(f"  Missing:          {len(missing)} {missing if missing else ''}")
    print(f"  Extra exposed:    {len(extra)} {extra if extra else ''}")
    print("  RLS status:       not exposed via PostgREST OpenAPI; check Supabase dashboard or run SQL: SELECT relname, relrowsecurity FROM pg_class WHERE relkind='r' AND relnamespace='public'::regnamespace;")

    return 0 if ok == len(EXPECTED_TABLES) and not missing else 1


if __name__ == "__main__":
    sys.exit(main())
