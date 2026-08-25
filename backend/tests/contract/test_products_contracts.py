def _auth_headers(client, email="products-contract@dyp.com"):
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


def test_product_out_shape_matches_schema(client):
    headers = _auth_headers(client)

    response = client.post("/api/products", json=_valid_payload(), headers=headers)

    assert response.status_code == 201
    assert set(response.json().keys()) == {
        "id",
        "material",
        "espesor",
        "largo",
        "ancho",
        "stock",
        "stock_comprometido",
        "punto_pedido",
    }
