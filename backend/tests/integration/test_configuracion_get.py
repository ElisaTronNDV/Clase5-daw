def _auth_headers(client, email="configuracion-get@dyp.com"):
    client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_default_200(client):
    headers = _auth_headers(client)

    response = client.get("/api/configuracion", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"margen_tolerancia_dimensional": 1.0}


def test_get_unauthenticated_401(client):
    response = client.get("/api/configuracion")

    assert response.status_code == 401
