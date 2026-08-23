def test_register_response_never_includes_hashed_password(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "contract@dyp.com", "password": "secret123"},
    )

    assert response.status_code == 201
    assert "hashed_password" not in response.json()


def test_login_response_shape_matches_token_schema(client):
    client.post(
        "/api/auth/register",
        json={"email": "shape@dyp.com", "password": "secret123"},
    )

    response = client.post(
        "/api/auth/login",
        json={"email": "shape@dyp.com", "password": "secret123"},
    )

    assert response.status_code == 200
    assert set(response.json().keys()) == {"access_token", "token_type"}
