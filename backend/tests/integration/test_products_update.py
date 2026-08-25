def _auth_headers(client, email="products-update@dyp.com"):
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


def test_update_success_200(client):
    headers = _auth_headers(client)
    created = client.post("/api/products", json=_valid_payload(), headers=headers)
    product_id = created.json()["id"]

    response = client.put(
        f"/api/products/{product_id}",
        json=_valid_payload(stock=20),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["stock"] == 20


def test_update_duplicate_400(client):
    headers = _auth_headers(client)
    client.post("/api/products", json=_valid_payload(material="Acero A"), headers=headers)
    created_b = client.post(
        "/api/products", json=_valid_payload(material="Acero B"), headers=headers
    )
    product_b_id = created_b.json()["id"]

    response = client.put(
        f"/api/products/{product_b_id}",
        json=_valid_payload(material="acero a"),
        headers=headers,
    )

    assert response.status_code == 400


def test_update_missing_field_422(client):
    headers = _auth_headers(client)
    created = client.post("/api/products", json=_valid_payload(), headers=headers)
    product_id = created.json()["id"]
    payload = _valid_payload()
    del payload["material"]

    response = client.put(f"/api/products/{product_id}", json=payload, headers=headers)

    assert response.status_code == 422


def test_update_value_not_positive_422(client):
    headers = _auth_headers(client)
    created = client.post("/api/products", json=_valid_payload(), headers=headers)
    product_id = created.json()["id"]

    response = client.put(
        f"/api/products/{product_id}",
        json=_valid_payload(stock=0),
        headers=headers,
    )

    assert response.status_code == 422


def test_update_rejects_stock_comprometido_422(client):
    headers = _auth_headers(client)
    created = client.post("/api/products", json=_valid_payload(), headers=headers)
    product_id = created.json()["id"]

    response = client.put(
        f"/api/products/{product_id}",
        json=_valid_payload(stock_comprometido=999),
        headers=headers,
    )

    assert response.status_code == 422


def test_update_not_found_404(client):
    headers = _auth_headers(client)

    response = client.put("/api/products/9999", json=_valid_payload(), headers=headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "product not found"}


def test_update_unauthenticated_401(client):
    response = client.put("/api/products/1", json=_valid_payload())

    assert response.status_code == 401
