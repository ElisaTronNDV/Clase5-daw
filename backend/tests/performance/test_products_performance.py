import time


def _auth_headers(client, email="products-perf@dyp.com"):
    client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _valid_payload(**overrides):
    payload = {
        "material": "SAE_1010",
        "espesor": 2.1,
        "largo": 3000,
        "ancho": 1500,
        "stock": 10,
        "punto_pedido": 5,
    }
    payload.update(overrides)
    return payload


def test_create_responds_under_2s(client):
    headers = _auth_headers(client)

    start = time.monotonic()
    response = client.post("/api/products", json=_valid_payload(), headers=headers)
    elapsed = time.monotonic() - start

    assert response.status_code == 201
    assert elapsed < 2.0


def test_list_responds_under_2s(client):
    headers = _auth_headers(client)
    client.post("/api/products", json=_valid_payload(), headers=headers)

    start = time.monotonic()
    response = client.get("/api/products", headers=headers)
    elapsed = time.monotonic() - start

    assert response.status_code == 200
    assert elapsed < 2.0


def test_update_responds_under_2s(client):
    headers = _auth_headers(client)
    created = client.post("/api/products", json=_valid_payload(), headers=headers)
    product_id = created.json()["id"]

    start = time.monotonic()
    response = client.put(
        f"/api/products/{product_id}",
        json=_valid_payload(stock=20),
        headers=headers,
    )
    elapsed = time.monotonic() - start

    assert response.status_code == 200
    assert elapsed < 2.0
