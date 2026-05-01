# CounterIQ API

FastAPI backend for the CounterIQ MVP. Stack: Python 3.11 · FastAPI ·
Pydantic v2 · supabase-py · ffmpeg.

## Endpoints (Phase 4C scope)

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/healthz` | none | Liveness probe |
| GET | `/api/me` | Bearer JWT | Echo current user from Supabase JWT |
| POST | `/api/stores` | Bearer JWT | Create store; auto-grants `owner` role |
| GET | `/api/stores` | Bearer JWT | List stores the user is a member of |
| GET | `/api/stores/{id}` | Bearer JWT | Get one store (must be a member) |
| POST | `/api/cameras/test` | Bearer JWT | Probe RTSP URL (ffmpeg `-an` enforced) |
| POST | `/api/cameras` | Bearer JWT | Create camera record |
| POST | `/api/zones` | Bearer JWT | Create zone polygon |
| GET | `/api/cameras/{id}/zones` | Bearer JWT | List zones for a camera |
| GET | `/api/events` | Bearer JWT | Filter by store/type/status/camera/time |
| POST | `/api/edge/events` | `X-Edge-Key` | Batch up to 100 events from edge device |

## Privacy contract (enforced)

- **No facial recognition / STT / demographic / emotion modules.** CI fails
  the build if any banned library is added to `requirements.txt`. See
  `.github/workflows/dep-policy.yml`.
- **Audio off by default.** Every ffmpeg invocation includes `-an`. The DB
  trigger `cameras_audio_enable_check` blocks audio enable without a
  compliance row.
- **Sanitizer.** Any LLM-generated copy must pass `app/util/sanitizer.py`
  before render or send.

## Local run

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate     # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env.local
# Edit .env.local — at minimum set SUPABASE_URL, SUPABASE_SECRET_KEY,
# and DEV_MOCK_AUTH=true if you want to smoke-test without a real JWT.

uvicorn app.main:app --reload --port 8000
```

Open: `http://localhost:8000/docs`.

## Smoke tests

```bash
# Health
curl -s http://localhost:8000/healthz
# → {"ok":true}

# Unauth → 401
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/me
# → 401

# DEV_MOCK_AUTH=true mode → 200
curl -s -H "Authorization: Bearer mock" http://localhost:8000/api/me
# → {"id":"00000000-...","email":"dev@counteriq.local","role":"authenticated"}
```

## pytest

```bash
pytest -q
```

## Production auth

Supabase project keys are asymmetric ECC (ES256). The API verifies tokens
against `${SUPABASE_URL}/auth/v1/.well-known/jwks.json` (cached 10 min).
The legacy HS256 shared-secret keys have been revoked.

## Build + run via Docker

```bash
docker build -t counteriq-api .
docker run --rm -p 8000:8000 --env-file .env.local counteriq-api
```

## Not in this scope

PATCH/DELETE on stores, cameras, zones, events. Clip presign/upload. Alert
dispatch. Daily report generation. Edge pairing/heartbeat. POS endpoints.
These land in later phases per `prompts/CURSOR_BACKEND_PROMPT.md`.
