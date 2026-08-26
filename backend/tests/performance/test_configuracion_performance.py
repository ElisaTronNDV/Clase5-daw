import time


def _auth_headers(client, email="configuracion-perf@dyp.com"):
    client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_responds_under_2s(client):
    headers = _auth_headers(client)

    start = time.monotonic()
    response = client.get("/api/configuracion", headers=headers)
    elapsed = time.monotonic() - start

    assert response.status_code == 200
    assert elapsed < 2.0


def test_update_responds_under_2s(client):
    headers = _auth_headers(client)

    start = time.monotonic()
    response = client.put(
        "/api/configuracion",
        json={"margen_tolerancia_dimensional": 1.5},
        headers=headers,
    )
    elapsed = time.monotonic() - start

    assert response.status_code == 200
    assert elapsed < 2.0
