"""
Tests for Auth API endpoints.
"""

from fastapi.testclient import TestClient

from backend.main import app


def test_register():
    client = TestClient(app)
    resp = client.post("/api/auth/register", json={
        "abha_id": "12-3456-7890-1234",
        "name": "Test Patient",
        "phone": "9999999999",
        "email": "test@example.com"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["message"] == "Registered successfully"
    assert data["abha_id"] == "12-3456-7890-1234"


def test_register_duplicate():
    client = TestClient(app)
    # Register once
    client.post("/api/auth/register", json={
        "abha_id": "12-3456-7890-1234",
        "name": "Test Patient",
    })
    # Try to register again
    resp = client.post("/api/auth/register", json={
        "abha_id": "12-3456-7890-1234",
        "name": "Test Patient 2",
    })
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_login():
    client = TestClient(app)
    # Register first
    client.post("/api/auth/register", json={
        "abha_id": "12-3456-7890-1234",
        "name": "Test Patient",
    })
    # Login with OTP (default password is "defaultpass" in mock)
    resp = client.post("/api/auth/login", json={
        "abha_id": "12-3456-7890-1234",
        "otp": "defaultpass"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid():
    client = TestClient(app)
    resp = client.post("/api/auth/login", json={
        "abha_id": "12-3456-7890-1234",
        "otp": "wrong"
    })
    assert resp.status_code == 401


def test_abha_verify():
    client = TestClient(app)
    # Register first
    client.post("/api/auth/register", json={
        "abha_id": "12-3456-7890-1234",
        "name": "Test Patient",
    })
    resp = client.post("/api/auth/abha-verify", json={
        "abha_id": "12-3456-7890-1234"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert "access_token" in data


def test_abha_verify_not_found():
    client = TestClient(app)
    resp = client.post("/api/auth/abha-verify", json={
        "abha_id": "99-9999-9999-9999"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is False


def test_me_unauthenticated():
    client = TestClient(app)
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["authenticated"] is False
