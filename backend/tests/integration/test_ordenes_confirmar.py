from app.core.exceptions import ProductAlreadyExistsError


def _auth_headers(client, email="ordenes-confirmar@dyp.com"):
    client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _product_payload(**overrides):
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


def _confirmar_payload(**overrides):
    payload = {
        "indice_formato": "1/1",
        "multiplicidad": 2,
        "material": "SAE_1010",
        "espesor": 2.1,
        "largo": 3000,
        "ancho": 1500,
        "tiempo_ejecucion_estimado": "00:10:00",
        "piezas": [
            {
                "ref": "1",
                "cantidad": 3,
                "pieza": "139394-00.lsr",
                "descripcion": "PC 1368 (CO) X3",
                "es_recorte": False,
                "largo_mm": None,
                "ancho_mm": None,
            }
        ],
        "crear_producto_automaticamente": False,
    }
    payload.update(overrides)
    return payload


def test_confirmar_con_producto_existente(client):
    headers = _auth_headers(client)
    product = client.post(
        "/api/products", json=_product_payload(), headers=headers
    ).json()

    response = client.post(
        "/api/ordenes/confirmar", json=_confirmar_payload(), headers=headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["product_id"] == product["id"]
    assert body["nest_code"].startswith("NEST-")

    updated_product = client.get(
        f"/api/products/{product['id']}", headers=headers
    ).json()
    assert updated_product["stock_comprometido"] == 2


def test_confirmar_sin_match_devuelve_409(client):
    headers = _auth_headers(client)

    before = client.get("/api/ordenes", headers=headers).json()["ordenes"]

    response = client.post(
        "/api/ordenes/confirmar", json=_confirmar_payload(), headers=headers
    )

    assert response.status_code == 409
    body = response.json()["detail"]
    assert body["material"] == "SAE_1010"
    assert body["espesor"] == 2.1
    assert body["largo"] == 3000
    assert body["ancho"] == 1500

    after = client.get("/api/ordenes", headers=headers).json()["ordenes"]
    assert len(after) == len(before)


def test_confirmar_con_alta_automatica(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/ordenes/confirmar",
        json=_confirmar_payload(crear_producto_automaticamente=True),
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()

    product = client.get(
        f"/api/products/{body['product_id']}", headers=headers
    ).json()
    assert product["stock"] == 0
    assert product["stock_comprometido"] == 2


def test_confirmar_rechaza_multiplicidad_invalida(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/ordenes/confirmar",
        json=_confirmar_payload(multiplicidad=0),
        headers=headers,
    )

    assert response.status_code == 422


def test_nest_code_es_secuencial_y_unico(client):
    headers = _auth_headers(client)

    primera = client.post(
        "/api/ordenes/confirmar",
        json=_confirmar_payload(crear_producto_automaticamente=True),
        headers=headers,
    ).json()
    segunda = client.post(
        "/api/ordenes/confirmar",
        json=_confirmar_payload(crear_producto_automaticamente=True),
        headers=headers,
    ).json()

    assert primera["nest_code"] != segunda["nest_code"]
    n1 = int(primera["nest_code"].split("-")[1])
    n2 = int(segunda["nest_code"].split("-")[1])
    assert n2 == n1 + 1


def test_confirmar_devuelve_alerta_stock_bajo_cuando_corresponde(client):
    headers = _auth_headers(client)
    client.post(
        "/api/products",
        json=_product_payload(stock=3, punto_pedido=3),
        headers=headers,
    )

    response = client.post(
        "/api/ordenes/confirmar",
        json=_confirmar_payload(multiplicidad=1),
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["alerta_stock_bajo"] is True


def test_confirmar_condicion_carrera_duplicado_devuelve_409(client, monkeypatch):
    headers = _auth_headers(client)

    from app.services import product_service as product_service_module

    def _boom(*args, **kwargs):
        raise ProductAlreadyExistsError("SAE_1010")

    monkeypatch.setattr(product_service_module, "crear_producto_automatico", _boom)

    response = client.post(
        "/api/ordenes/confirmar",
        json=_confirmar_payload(crear_producto_automaticamente=True),
        headers=headers,
    )

    assert response.status_code == 409
