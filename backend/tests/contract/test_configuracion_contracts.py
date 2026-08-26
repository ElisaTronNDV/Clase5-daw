def _auth_headers(client, email="configuracion-contract@dyp.com"):
    client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_configuracion_out_shape_matches_schema(client):
    headers = _auth_headers(client)

    response = client.get("/api/configuracion", headers=headers)

    assert response.status_code == 200
    assert set(response.json().keys()) == {"margen_tolerancia_dimensional"}
