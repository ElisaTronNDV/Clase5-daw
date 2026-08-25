def _auth_headers(client, email="products-create@dyp.com"):
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


def test_create_success_201(client):
    headers = _auth_headers(client)

    response = client.post("/api/products", json=_valid_payload(), headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["material"] == "SAE_1010"
    assert "id" in body


def test_create_duplicate_400(client):
    headers = _auth_headers(client)
    client.post("/api/products", json=_valid_payload(), headers=headers)

    response = client.post(
        "/api/products", json=_valid_payload(material="sae_1010"), headers=headers
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "product already registered with this material, thickness and dimensions"
    }


def test_create_missing_field_422(client):
    headers = _auth_headers(client)
    payload = _valid_payload()
    del payload["material"]

    response = client.post("/api/products", json=payload, headers=headers)

    assert response.status_code == 422


def test_create_value_not_positive_422(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/products", json=_valid_payload(espesor=0), headers=headers
    )

    assert response.status_code == 422


def test_create_rejects_stock_comprometido_422(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/products",
        json=_valid_payload(stock_comprometido=999),
        headers=headers,
    )

    assert response.status_code == 422


def test_create_initializes_stock_comprometido_zero(client):
    headers = _auth_headers(client)

    response = client.post("/api/products", json=_valid_payload(), headers=headers)

    assert response.status_code == 201
    assert response.json()["stock_comprometido"] == 0


def test_create_unauthenticated_401(client):
    response = client.post("/api/products", json=_valid_payload())

    assert response.status_code == 401
