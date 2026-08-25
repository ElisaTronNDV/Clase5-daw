def _auth_headers(client, email="products-list@dyp.com"):
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


def test_list_returns_all_products(client):
    headers = _auth_headers(client)
    client.post("/api/products", json=_valid_payload(material="Acero A"), headers=headers)
    client.post("/api/products", json=_valid_payload(material="Acero B"), headers=headers)

    response = client.get("/api/products", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    materials = {p["material"] for p in body}
    assert materials == {"Acero A", "Acero B"}


def test_list_unauthenticated_401(client):
    response = client.get("/api/products")

    assert response.status_code == 401
