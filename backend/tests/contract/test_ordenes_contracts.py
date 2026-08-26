def _auth_headers(client, email="ordenes-contract@dyp.com"):
    client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _confirmar_payload(**overrides):
    payload = {
        "indice_formato": "1/1",
        "multiplicidad": 1,
        "material": "SAE_1010",
        "espesor": 2.1,
        "largo": 3000,
        "ancho": 1500,
        "tiempo_ejecucion_estimado": "00:10:00",
        "piezas": [
            {
                "ref": "1",
                "cantidad": 1,
                "pieza": "139394-00.lsr",
                "descripcion": "PC 1368 (CO) X3",
                "es_recorte": False,
                "largo_mm": None,
                "ancho_mm": None,
            }
        ],
        "crear_producto_automaticamente": True,
    }
    payload.update(overrides)
    return payload


def test_shape_orden_response(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/ordenes/confirmar", json=_confirmar_payload(), headers=headers
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == {
        "id",
        "nest_code",
        "estado",
        "multiplicidad",
        "material",
        "espesor",
        "largo",
        "ancho",
        "tiempo_ejecucion_estimado",
        "indice_formato",
        "product_id",
        "created_at",
        "piezas",
        "alerta_stock_bajo",
    }
    assert len(body["piezas"]) == 1
    assert set(body["piezas"][0].keys()) == {
        "id",
        "ref",
        "cantidad",
        "pieza",
        "descripcion",
        "es_recorte",
        "largo_mm",
        "ancho_mm",
    }
