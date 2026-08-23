def test_login_success_200_returns_token(client):
    client.post(
        "/api/auth/register",
        json={"email": "login@dyp.com", "password": "secret123"},
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "login@dyp.com", "password": "secret123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


def test_login_wrong_password_401_generic_message(client):
    client.post(
        "/api/auth/register",
        json={"email": "wrongpass@dyp.com", "password": "secret123"},
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "wrongpass@dyp.com", "password": "not-the-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid credentials"}


def test_login_nonexistent_email_401_same_generic_message(client):
    response_wrong_password = _register_and_login_with_wrong_password(client)
    response_nonexistent = client.post(
        "/api/auth/login",
        json={"email": "no-existe@dyp.com", "password": "whatever123"},
    )

    assert response_nonexistent.status_code == 401
    assert response_nonexistent.json() == response_wrong_password.json()


def _register_and_login_with_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"email": "compare@dyp.com", "password": "secret123"},
    )
    return client.post(
        "/api/auth/login",
        json={"email": "compare@dyp.com", "password": "not-the-password"},
    )
