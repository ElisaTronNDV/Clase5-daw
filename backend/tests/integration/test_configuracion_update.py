def _auth_headers(client, email="configuracion-update@dyp.com"):
    client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_update_success_200(client):
    headers = _auth_headers(client)

    response = client.put(
        "/api/configuracion",
        json={"margen_tolerancia_dimensional": 2.5},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {"margen_tolerancia_dimensional": 2.5}


def test_update_value_not_positive_422(client):
    headers = _auth_headers(client)

    response = client.put(
        "/api/configuracion",
        json={"margen_tolerancia_dimensional": 0},
        headers=headers,
    )

    assert response.status_code == 422


def test_update_missing_field_422(client):
    headers = _auth_headers(client)

    response = client.put("/api/configuracion", json={}, headers=headers)

    assert response.status_code == 422


def test_update_non_numeric_422(client):
    headers = _auth_headers(client)

    response = client.put(
        "/api/configuracion",
        json={"margen_tolerancia_dimensional": "abc"},
        headers=headers,
    )

    assert response.status_code == 422


def test_update_rejects_extra_field_422(client):
    headers = _auth_headers(client)

    response = client.put(
        "/api/configuracion",
        json={"margen_tolerancia_dimensional": 2.0, "id": 99},
        headers=headers,
    )

    assert response.status_code == 422


def test_update_unauthenticated_401(client):
    response = client.put(
        "/api/configuracion", json={"margen_tolerancia_dimensional": 2.0}
    )

    assert response.status_code == 401


def test_get_after_update_returns_last_saved_value(client):
    headers = _auth_headers(client)
    client.put(
        "/api/configuracion",
        json={"margen_tolerancia_dimensional": 3.7},
        headers=headers,
    )

    response = client.get("/api/configuracion", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"margen_tolerancia_dimensional": 3.7}
