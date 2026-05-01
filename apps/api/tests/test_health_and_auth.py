from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_me_unauth_returns_401():
    r = client.get("/api/me")
    assert r.status_code == 401


def test_me_with_mock_token_returns_200():
    r = client.get("/api/me", headers={"Authorization": "Bearer mock"})
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "authenticated"
    assert body["email"] == "dev@counteriq.local"


def test_me_with_garbage_token_rejected():
    r = client.get("/api/me", headers={"Authorization": "Bearer not-a-real-jwt"})
    assert r.status_code == 401
