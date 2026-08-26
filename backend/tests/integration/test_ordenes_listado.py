from sqlalchemy.orm import sessionmaker

from app.models.orden import Orden


def _auth_headers(client, email="ordenes-listado@dyp.com"):
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


def _confirmar(client, headers, **overrides):
    response = client.post(
        "/api/ordenes/confirmar", json=_confirmar_payload(**overrides), headers=headers
    )
    assert response.status_code == 201
    return response.json()


def _cerrar_ultima_orden(initialized_db):
    Session = sessionmaker(bind=initialized_db)
    session = Session()
    try:
        orden = session.query(Orden).order_by(Orden.id.desc()).first()
        orden.estado = "cerrada"
        session.commit()
        return orden.id
    finally:
        session.close()


def test_filtra_por_estado(client, initialized_db):
    headers = _auth_headers(client)
    _confirmar(client, headers, material="Material A", espesor=1.0, largo=100, ancho=100)
    _confirmar(client, headers, material="Material B", espesor=2.0, largo=200, ancho=200)
    _cerrar_ultima_orden(initialized_db)

    response = client.get("/api/ordenes", params={"estado": "vigente"}, headers=headers)

    assert response.status_code == 200
    ordenes = response.json()["ordenes"]
    assert len(ordenes) == 1
    assert ordenes[0]["estado"] == "vigente"


def test_sin_filtro_muestra_todas_las_ordenes(client, initialized_db):
    headers = _auth_headers(client)
    _confirmar(client, headers, material="Material C", espesor=1.0, largo=100, ancho=100)
    _confirmar(client, headers, material="Material D", espesor=2.0, largo=200, ancho=200)
    _cerrar_ultima_orden(initialized_db)

    response = client.get("/api/ordenes", headers=headers)

    assert response.status_code == 200
    assert len(response.json()["ordenes"]) == 2


def test_busca_por_nest_parcial_combinado_con_estado(client, initialized_db):
    headers = _auth_headers(client)
    orden_a = _confirmar(
        client, headers, material="Material E", espesor=1.0, largo=100, ancho=100
    )
    _confirmar(client, headers, material="Material F", espesor=2.0, largo=200, ancho=200)
    _cerrar_ultima_orden(initialized_db)

    nest_prefix = orden_a["nest_code"][: len("NEST-0000")]

    response = client.get(
        "/api/ordenes",
        params={"estado": "vigente", "nest": nest_prefix},
        headers=headers,
    )

    assert response.status_code == 200
    ordenes = response.json()["ordenes"]
    assert len(ordenes) == 1
    assert ordenes[0]["nest_code"] == orden_a["nest_code"]


def test_filtra_estado_invalido_devuelve_422(client):
    headers = _auth_headers(client)

    response = client.get(
        "/api/ordenes", params={"estado": "no-existe"}, headers=headers
    )

    assert response.status_code == 422
