def _auth_headers(client, email="products-get@dyp.com"):
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


def test_get_by_id_success_200(client):
    headers = _auth_headers(client)
    created = client.post("/api/products", json=_valid_payload(), headers=headers)
    product_id = created.json()["id"]

    response = client.get(f"/api/products/{product_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == product_id


def test_get_by_id_not_found_404(client):
    headers = _auth_headers(client)

    response = client.get("/api/products/9999", headers=headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "product not found"}
