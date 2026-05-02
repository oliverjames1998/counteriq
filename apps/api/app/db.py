"""Supabase REST helpers.

Architecture:
- No service-role key. RLS protects every table.
- For user-scoped reads/writes: forward the caller's Supabase JWT in the
  Authorization header — PostgREST then enforces the same RLS policies the
  frontend relies on.
- For edge-device flows: call anon-callable security-definer RPCs
  (`claim_edge_device`, `ingest_edge_event`) with the anon key. The RPC
  itself validates the X-Edge-Key sha256 hash and inserts on the device's
  behalf without ever exposing service privileges to the network.
"""
from __future__ import annotations

from typing import Any, Optional

import httpx

from .config import get_settings


def _base_headers(api_key: str, bearer: Optional[str] = None) -> dict[str, str]:
    return {
        "apikey": api_key,
        "Authorization": f"Bearer {bearer or api_key}",
        "Content-Type": "application/json",
    }


def user_get(path: str, jwt: str, params: Optional[dict[str, Any]] = None) -> httpx.Response:
    s = get_settings()
    url = f"{s.SUPABASE_URL.rstrip('/')}/rest/v1/{path.lstrip('/')}"
    return httpx.get(url, headers=_base_headers(s.SUPABASE_PUBLISHABLE_KEY, jwt), params=params, timeout=15)


def user_post(path: str, jwt: str, body: Any) -> httpx.Response:
    s = get_settings()
    url = f"{s.SUPABASE_URL.rstrip('/')}/rest/v1/{path.lstrip('/')}"
    headers = _base_headers(s.SUPABASE_PUBLISHABLE_KEY, jwt) | {"Prefer": "return=representation"}
    return httpx.post(url, headers=headers, json=body, timeout=20)


def anon_rpc(name: str, params: dict[str, Any]) -> httpx.Response:
    """Call a Supabase RPC with the anon key. Use only for security-definer
    RPCs that perform their own auth checks (e.g. ingest_edge_event)."""
    s = get_settings()
    url = f"{s.SUPABASE_URL.rstrip('/')}/rest/v1/rpc/{name}"
    return httpx.post(url, headers=_base_headers(s.SUPABASE_PUBLISHABLE_KEY), json=params, timeout=20)
