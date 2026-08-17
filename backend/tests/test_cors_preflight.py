import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app


def test_cors_allowed_origin_get():
    """Request from allowed origin returns proper CORS headers and credentials flag."""
    client = TestClient(app)
    headers = {
        "Origin": "http://localhost:5173",
    }
    resp = client.get("/api/v1/health", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert resp.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_options_request():
    """Browser preflight OPTIONS request returns 200 and allowed methods/headers."""
    client = TestClient(app)
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization, content-type",
    }
    resp = client.options("/api/v1/research-projects", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in resp.headers.get("access-control-allow-methods", "")
    assert "authorization" in resp.headers.get("access-control-allow-headers", "").lower()


def test_cors_disallowed_origin_rejected():
    """Untrusted origins do not receive CORS allow headers."""
    client = TestClient(app)
    headers = {
        "Origin": "https://malicious-attacker.com",
    }
    resp = client.get("/api/v1/health", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") is None


def test_cors_vercel_subdomain_allowed():
    """Any deployed Vercel subdomain or preview branch is allowed via origin regex."""
    client = TestClient(app)
    headers = {
        "Origin": "https://evidence-lab-frontend-git-main-sawan.vercel.app",
    }
    resp = client.get("/api/v1/health", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "https://evidence-lab-frontend-git-main-sawan.vercel.app"
    assert resp.headers.get("access-control-allow-credentials") == "true"
