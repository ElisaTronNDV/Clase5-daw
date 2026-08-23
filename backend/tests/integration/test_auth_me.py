from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings


def _register_and_get_token(client, email="me@dyp.com", password="secret123"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    login_response = client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    return login_response.json()["access_token"]


def test_me_valid_token_200(client):
    token = _register_and_get_token(client)

    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "me@dyp.com"
    assert "id" in body
    assert "hashed_password" not in body


def test_me_missing_token_401(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid or expired token"}


def test_me_expired_or_invalid_token_401(client):
    expired_token = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=5)},
        settings.JWT_SECRET,
        algorithm="HS256",
    )

    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid or expired token"}
