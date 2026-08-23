def test_register_success_201(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "nuevo@dyp.com", "password": "secret123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "nuevo@dyp.com"
    assert "id" in body


def test_register_duplicate_email_400(client):
    payload = {"email": "duplicado@dyp.com", "password": "secret123"}
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/auth/register", json=payload)

    assert second.status_code == 400
    assert second.json() == {"detail": "email already registered"}


def test_register_password_too_short_422(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "corta@dyp.com", "password": "1234567"},
    )

    assert response.status_code == 422
