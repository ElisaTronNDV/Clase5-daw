def _auth_headers(client, email="ordenes-documento@dyp.com"):
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


def test_descarga_documento_orden_existente(client):
    headers = _auth_headers(client)
    client.post("/api/products", json=_product_payload(), headers=headers)

    orden = client.post(
        "/api/ordenes/confirmar", json=_confirmar_payload(), headers=headers
    ).json()

    response = client.get(f"/api/ordenes/{orden['id']}/documento", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_documento_orden_inexistente_404(client):
    headers = _auth_headers(client)

    response = client.get("/api/ordenes/999999/documento", headers=headers)

    assert response.status_code == 404
    # Distingue el 404 de dominio (OrdenNotFoundError) del 404 genérico de FastAPI
    # cuando la ruta todavía no existe (mismo status code, distinto detail).
    assert response.json()["detail"] == "orden not found"


def test_documento_rechaza_sin_auth(client):
    response = client.get("/api/ordenes/1/documento")

    assert response.status_code == 401
