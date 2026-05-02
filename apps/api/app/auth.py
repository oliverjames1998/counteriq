"""Supabase JWT verification.

In production: verifies asymmetric ECC JWTs against the project's JWKS endpoint.
In DEV_MOCK_AUTH=true mode: accepts the literal token "mock" and returns a fake
authenticated user. Used only for local smoke tests.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, status

from .config import Settings, get_settings


@dataclass
class CurrentUser:
    id: str
    email: Optional[str]
    role: str
    jwt: str  # raw bearer token, forwarded to PostgREST so RLS scopes data


_JWKS_CACHE: dict = {"fetched_at": 0, "keys": None}
_JWKS_TTL = 600


def _fetch_jwks(jwks_url: str) -> dict:
    now = time.time()
    if _JWKS_CACHE["keys"] is None or now - _JWKS_CACHE["fetched_at"] > _JWKS_TTL:
        with httpx.Client(timeout=10) as c:
            r = c.get(jwks_url)
            r.raise_for_status()
            _JWKS_CACHE["keys"] = r.json()
            _JWKS_CACHE["fetched_at"] = now
    return _JWKS_CACHE["keys"]


def _verify_supabase_jwt(token: str, settings: Settings) -> dict:
    try:
        unverified = jwt.get_unverified_header(token)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"invalid token header: {e}")

    kid = unverified.get("kid")
    jwks = _fetch_jwks(settings.jwks_url)
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="signing key not found")

    try:
        public_key = jwt.algorithms.ECAlgorithm.from_jwk(key) if key.get("kty") == "EC" else jwt.algorithms.RSAAlgorithm.from_jwk(key)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[unverified.get("alg", "ES256")],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.jwt_issuer,
        )
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"jwt verification failed: {e}")


def require_user(
    authorization: Optional[str] = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")

    token = authorization.split(" ", 1)[1].strip()

    if settings.DEV_MOCK_AUTH and token == "mock":
        return CurrentUser(
            id="00000000-0000-0000-0000-000000000001",
            email="dev@counteriq.local",
            role="authenticated",
            jwt=token,
        )

    payload = _verify_supabase_jwt(token, settings)
    return CurrentUser(
        id=payload.get("sub", ""),
        email=payload.get("email"),
        role=payload.get("role", "authenticated"),
        jwt=token,
    )
