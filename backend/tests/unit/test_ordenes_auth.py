def test_los_tres_endpoints_rechazan_sin_token(client):
    extraer = client.post(
        "/api/ordenes/extraer",
        files={"archivo": ("test.pdf", b"%PDF-1.4\n", "application/pdf")},
    )
    assert extraer.status_code == 401

    confirmar = client.post(
        "/api/ordenes/confirmar",
        json={
            "indice_formato": "1/1",
            "multiplicidad": 1,
            "material": "SAE_1010",
            "espesor": 2.1,
            "largo": 3000,
            "ancho": 1500,
            "tiempo_ejecucion_estimado": "00:10:00",
            "piezas": [],
            "crear_producto_automaticamente": True,
        },
    )
    assert confirmar.status_code == 401

    listado = client.get("/api/ordenes")
    assert listado.status_code == 401
