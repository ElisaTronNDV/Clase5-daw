from pathlib import Path

import pypdfium2 as pdfium

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "docs" / "Archivos de Corte"

MAX_BYTES = 10 * 1024 * 1024


def _auth_headers(client, email="ordenes-extraer@dyp.com"):
    client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _leer_fixture(nombre: str) -> bytes:
    return (FIXTURES_DIR / nombre).read_bytes()


def _pdf_vacio_sin_tablas() -> bytes:
    doc = pdfium.PdfDocument.new()
    doc.new_page(200, 200)
    import io

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_extraer_pdf_real_devuelve_paginas(client):
    headers = _auth_headers(client)
    contenido = _leer_fixture("Ejemplo 1.pdf")

    response = client.post(
        "/api/ordenes/extraer",
        files={"archivo": ("Ejemplo 1.pdf", contenido, "application/pdf")},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["paginas"]) == 1
    assert body["paginas"][0]["material"] == "SAE_1010"
    assert len(body["paginas"][0]["piezas"]) == 4


def test_extraer_rechaza_extension_invalida(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/ordenes/extraer",
        files={"archivo": ("archivo.txt", b"contenido-cualquiera", "text/plain")},
        headers=headers,
    )

    assert response.status_code == 400


def test_extraer_rechaza_archivo_grande(client):
    headers = _auth_headers(client)
    contenido = b"%PDF-1.4\n" + b"A" * (MAX_BYTES + 1000)

    response = client.post(
        "/api/ordenes/extraer",
        files={"archivo": ("grande.pdf", contenido, "application/pdf")},
        headers=headers,
    )

    assert response.status_code == 413


def test_extraer_rechaza_estructura_invalida(client):
    headers = _auth_headers(client)
    contenido = _pdf_vacio_sin_tablas()

    response = client.post(
        "/api/ordenes/extraer",
        files={"archivo": ("vacio.pdf", contenido, "application/pdf")},
        headers=headers,
    )

    assert response.status_code == 422
