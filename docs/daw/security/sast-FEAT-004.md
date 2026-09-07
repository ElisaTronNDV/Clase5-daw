# SAST FEAT-004: Módulo Oficina — carga de archivo de corte y generación de orden de trabajo

| Field | Value |
|-------|-------|
| Ticket | FEAT-004 |
| Date | 2026-09-07 |
| Scope | backend/app/api/routes/ordenes.py, backend/app/api/router.py, backend/app/core/exceptions.py, backend/app/models/orden.py, backend/app/models/__init__.py, backend/app/schemas/orden.py, backend/app/services/{orden_service,pdf_extraction_service,pdf_document_service,barcode_service,product_service}.py, frontend/src/app/oficina/** (6 bloques completos) |

## Secretos (F-SAST-01)

- ✅ Sin secretos hardcodeados: grep de patrones `secret=`/`password=`/`api_key=`/`token=` con
  valores literales sobre todos los archivos nuevos/modificados de este ticket — 0 resultados.
- ✅ Sin configuración nueva de entorno (reutiliza `JWT_SECRET`/`DATABASE_URL` ya auditados en
  FEAT-001).
- ✅ `.env` en `.gitignore` (sin cambios).

## Inyección (F-SAST-02, F-SAST-03, F-SAST-05)

- ✅ SQL injection: `orden_service.py` y `product_service.py` usan exclusivamente el ORM de
  SQLAlchemy (`db.query(...).filter(...)`, `db.add`, `db.flush`, `db.commit`). 0 SQL crudo, 0
  concatenación de strings en queries. `Orden.nest_code.ilike(f"%{nest}%")` construye el **valor**
  del patrón LIKE (parametrizado por SQLAlchemy), no SQL; el usuario solo puede afectar sus propios
  resultados de búsqueda con wildcards `%`/`_`.
- ✅ Command injection: sin `eval()`, `exec()`, `os.system()` ni `subprocess.*` en el código nuevo.
- ✅ Path traversal: **N/A** — `POST /api/ordenes/extraer` recibe `UploadFile`, lee el contenido a
  memoria (`await archivo.read()`) y lo pasa como `bytes` a `pdf_extraction_service`. El `filename`
  solo se usa para `.lower().endswith(".pdf")`, nunca para construir una ruta de filesystem. Ningún
  servicio nuevo abre/escribe archivos derivados de input de usuario.

## XSS y funciones inseguras (F-SAST-06, F-SAST-04, F-SAST-17)

- ✅ Sin `[innerHTML]`, `bypassSecurityTrust*`, `outerHTML` ni `dangerouslySetInnerHTML` en
  `frontend/src/app/oficina/` — binding e interpolación por defecto de Angular (auto-sanitizado).
- ✅ `listado-ordenes.ts::dispararDescarga`: `URL.createObjectURL(blob)` sobre un blob
  `application/pdf` de la propia API + `<a download="orden-${id}.pdf">` con `id: number` tipado +
  `revokeObjectURL`. Sin XSS ni DOM injection.
- ✅ Deserialización insegura (F-SAST-04): **N/A** — `pdfplumber` usa `pdfminer.six`/`pypdfium2`
  para parsear el PDF, no `pickle`/`yaml.load`/`marshal`.
- ✅ Inyección de markup de `reportlab` (`pdf_document_service.py`): los campos influidos por el
  usuario (`pieza.ref`, `pieza.pieza`, `pieza.descripcion` del payload de confirmación) se pasan
  como **strings planos en celdas de `Table`**, no dentro de `Paragraph`. `reportlab` solo
  interpreta mini-markup XML (`<b>`, `<font>`, `<img>`, `<para>`) dentro de flowables `Paragraph`;
  en una celda string se renderiza literal. Los únicos `Paragraph` usan `orden.nest_code`
  (system-generated, formato `NEST-000123`) y literales. (`reportlab 4.5.1` además ya tiene
  parcheado CVE-2023-33733.)

## Criptografía (F-SAST-08)

- ✅ **N/A** — FEAT-004 no introduce operaciones criptográficas nuevas. No toca
  `backend/app/core/security.py` (sigue HS256/HMAC para JWT, nunca ECDSA — relevante para el
  hallazgo heredado de `ecdsa`, ver Dependencias).

## Debug / logging / uploads / CSRF (F-SAST-09, F-SAST-10, F-SAST-11, F-SAST-12)

- ✅ `DEBUG=False` sin cambios respecto a FEAT-001/002/003.
- ✅ Sin `print()`/`logging.*`/`logger` en los archivos backend nuevos.
- ✅ Unrestricted upload (F-SAST-11): **mitigado**. `POST /api/ordenes/extraer` valida server-side
  extensión `.pdf` + magic bytes `%PDF-` + tamaño ≤ 10 MB antes de procesar. El contenido se pasa
  como `bytes` a `pdfplumber`; nunca se ejecuta, nunca se persiste en disco, nunca se sirve de
  vuelta. El `content-type` del cliente no se confía.
- N/A CSRF: la API es stateless con JWT en header `Authorization` (sin cookies de sesión), sin
  cambios respecto a los tickets anteriores.

## Validación de input y manejo de errores (F-SAST-14, F-SAST-15)

- ✅ `OrdenConfirmarRequest` y `PiezaConfirmar` con `model_config = ConfigDict(extra="forbid")`
  (`schemas/orden.py`) — un cliente no puede inyectar `stock_comprometido`, `nest_code`, `estado`
  ni ningún campo no declarado vía el payload de confirmación. Mitigación #4 del threat model
  confirmada.
- ✅ Rangos numéricos declarativos: `multiplicidad: Field(gt=0, le=10000)`,
  `espesor/largo/ancho: Field(gt=0, le=100000)`, `cantidad: Field(gt=0, le=100000)`. Mitigación #3
  del threat model confirmada.
- ✅ Manejo de errores sin fuga de internals (F-SAST-15): `pdf_extraction_service.extraer_paginas`
  captura cualquier excepción interna de `pdfplumber` (`except Exception`) y la remapea a
  `ArchivoCorteInvalidoError("...formato no reconocido.")` con mensaje genérico + `from exc` (la
  cadena original queda server-side; `DEBUG=False`). Los mensajes específicos que llegan al cliente
  (`422`, `str(exc)` en `ordenes.py`) contienen solo datos del propio PDF del usuario, no internals.
  Mitigación de Information Disclosure del threat model confirmada.
- ⚠️ **W-SAST (Low, aceptado como deuda — ver más abajo)**: campos string de
  `OrdenConfirmarRequest`/`PiezaConfirmar` sin `Field(max_length=...)`.

## DoS / rendimiento (mitigaciones del threat model)

- ✅ `pdf_extraction_service`: límite duro `MAX_PAGINAS = 50` + límite de entrada 10 MB + captura
  total de excepciones acotan el costo de parseo; una decompression bomb interna queda limitada por
  el tope de 10 MB de entrada.
- ✅ `confirmar_orden`: transacción todo-o-nada con un único `db.commit()` y
  `except Exception: db.rollback(); raise`. Mitigación #6 del threat model confirmada.
- ⚠️ **W-SAST (Low, aceptado como deuda — ver más abajo)**: el límite de 10 MB se valida después de
  `await archivo.read()`.

## Autenticación en los 4 endpoints

- ✅ `POST /api/ordenes/extraer`, `POST /api/ordenes/confirmar`, `GET /api/ordenes`,
  `GET /api/ordenes/{id}/documento` — los cuatro declaran
  `current_user: User = Depends(get_current_user)`. Confirmado por lectura y por
  `test_ordenes_auth.py::test_los_tres_endpoints_rechazan_sin_token` y
  `test_ordenes_documento.py::test_documento_rechaza_sin_auth`.
- ℹ️ Autorización a nivel objeto: cualquier usuario autenticado lista/descarga cualquier orden.
  Modelo de workspace compartido sin RBAC (RF-19-a), ya aceptado en
  `threat-FEAT-001/002/003/004`. No es regresión.

## Dependencias (F-SAST-13, F-SAST-16)

FEAT-004 agrega 5 dependencias backend: `pdfplumber>=0.11,<1.0`, `python-multipart>=0.0.12,<1.0`,
`python-barcode>=0.15,<1.0`, `pyzbar>=0.1.9,<1.0`, `reportlab>=4.0,<5.0` — todas justificadas en el
spec. Frontend: `package.json` y `package-lock.json` **sin cambios**.

**Backend (`.venv/bin/pip-audit`):**

| Paquete | Versión instalada | CVE | Severidad | Disposición |
|---|---|---|---|---|
| `pdfplumber` | 0.11.10 | — | — | Nueva, sin CVE conocido |
| `pdfminer.six` / `pypdfium2` (transitivas de pdfplumber) | 5.13.0 | — | — | Nuevas, sin CVE conocido |
| `pillow` (transitiva de pdfplumber/python-barcode) | 12.3.0 | — | — | Actual, sin CVE Critical/High |
| `reportlab` | 4.5.1 | — | — | Nueva, ≥ versión con CVE-2023-33733 parcheado |
| `python-barcode` | 0.16.1 | — | — | Nueva, sin CVE conocido |
| `pyzbar` | 0.1.9 | — | — | Nueva, sin CVE conocido |
| `python-multipart` | — | — | — | Nueva, sin CVE conocido |
| `ecdsa` | 0.19.2 (transitiva, vía `python-jose[cryptography]`) | PYSEC-2026-1325 | Medium | **Heredada — FALSE_POSITIVE, ver Suppression 1** |
| `pytest` | 8.4.2 | PYSEC-2026-1845 | Low | **Heredada — ACCEPTED_RISK, ver `sast-FEAT-002.md` Suppression 1** |

`pip-audit` reporta los mismos 2 hallazgos que FEAT-001/002/003, ninguno en las 5 dependencias
nuevas.

**Frontend (`npm audit`):** 1 hallazgo moderate **nuevo** en `qs` — no introducido por FEAT-004
(el lockfile no cambió; apareció por actualización de la base de advisories de npm; FEAT-002/003
reportaron 0 con el mismo lockfile). Ver Suppression 2.

### Suppression 1: PYSEC-2026-1325 (ecdsa — Minerva timing attack) — heredada, sin cambios

| Field | Value |
|---|---|
| File | `backend/requirements.txt` (`python-jose[cryptography]`, trae `ecdsa` como transitiva) |
| Category | F-SAST-16 — side-channel timing attack sobre firmas ECDSA en la curva P-256 |
| Disposition | FALSE_POSITIVE |
| Reviewer | Maria Elisa (ma.elisa.tron@gmail.com) |
| Date | 2026-09-07 (evaluación original en `sast-FEAT-001.md`, confirmada sin cambios en `-FEAT-002.md`/`-FEAT-003.md`) |
| Justification | FEAT-004 no toca `core/security.py`; el proyecto usa exclusivamente HS256 (HMAC) para JWT, nunca ECDSA. Ningún archivo nuevo de FEAT-004 importa `ecdsa` ni usa firmas EC; las 5 deps nuevas no traen ECDSA en su ruta de ejecución. La función vulnerable no es alcanzable desde ningún endpoint. |
| Compensating control | El threat model de FEAT-001 sigue exigiendo el algoritmo fijo explícito (`algorithms=["HS256"]` en `jwt.decode`). |
| Review by | 2027-02-24 (heredado de la evaluación original — dentro de los 6 meses, F-SAST-19 no aplica) |

### Suppression 2: GHSA-x5fp-wj9c-mxmx / GHSA-4mjr-xmp4-gh2g (qs) — nueva

| Field | Value |
|---|---|
| File | `frontend/package-lock.json` (`qs@6.15.3`, transitiva de `@angular/cli`) |
| Category | F-SAST-16 — Medium CVE en dependencia (array-limit bypass via bracket-key comma parsing + DoS via attacker-controlled isBuffer, en `qs`) |
| Disposition | ACCEPTED_RISK |
| Reviewer | Maria Elisa (ma.elisa.tron@gmail.com) |
| Date | 2026-09-07 |
| Justification | `qs` entra solo por la cadena `@angular/cli@22.1.5 → @modelcontextprotocol/sdk@1.30.0 → express@5.2.1 → qs` (confirmado con `npm ls qs`). Es tooling de build/CLI. El artefacto de producción es un bundle estático de Angular (`ng build` → `main.js`/`styles.css`) servido como archivos estáticos, sin runtime Node/Express en ningún entorno desplegado ni en el dev server (Angular usa su propio dev server, no Express). La función vulnerable — parseo de query strings HTTP controladas por un atacante dentro de Express — nunca se ejecuta. `package-lock.json` no cambió en FEAT-004. |
| Compensating control | El deploy no incluye ningún servidor Node; el bundle se sirve como estáticos. Revisar el bump de `@angular/cli` que actualice `express`/`qs` transitivo en el próximo mantenimiento de dependencias (no se corre `npm audit fix` en FEAT-004 porque modificaría `package-lock.json`, fuera del alcance de este ticket). |
| Review by | 2027-03-07 |

## Hallazgos Low aceptados como deuda (W-SAST — no bloquean)

Registrados con decisión explícita de la usuaria (2026-09-07): documentar y abrir como ticket de
mantenimiento aparte, no arreglar dentro de FEAT-004.

| # | Archivo | Descripción | Severidad | Remediación propuesta |
|---|---|---|---|---|
| W-1 | `backend/app/api/routes/ordenes.py` (~L60-71) | El límite de 10 MB se valida **después** de `contenido = await archivo.read()`. Un cliente autenticado puede enviar un body de varios GB: Starlette lo vuelca a un `SpooledTemporaryFile` y `.read()` lo carga entero antes del rechazo en L67. Debilita parcialmente la mitigación DoS de FR-02 (protege memoria del parser, no I/O ni disco temporal). Requiere usuario autenticado; el temp file se limpia al cerrar la request. | Low | Chequear `archivo.size` (poblado por Starlette desde `Content-Length`) antes del `await archivo.read()`, y/o límite de body a nivel de reverse proxy. |
| W-2 | `backend/app/schemas/orden.py` | `material`, `pieza`, `descripcion`, `ref`, `indice_formato`, `tiempo_ejecucion_estimado` son `str`/`str \| None` sin `Field(max_length=...)`. Las columnas son `String(255)` pero SQLite no enforcea longitud → un payload con strings de MB se persiste sin recorte. F-SAST-14: validación de input incompleta (los campos numéricos sí tienen cota). | Low | Agregar `Field(max_length=255)` a esos campos, consistente con el ancho de columna. |

## Resumen

- Total: 20+ checks limpios sobre el código nuevo (secretos, SQLi, command injection, path
  traversal, XSS, deserialización, markup reportlab, crypto, debug/logging, upload, auth,
  `extra="forbid"`, rangos numéricos, transacción atómica). Mitigaciones #1–#6 del threat model
  confirmadas en código.
- Dependencias: **0 Critical, 0 High.** 2 Medium suprimidos con documentación (1 FALSE_POSITIVE
  heredado + 1 ACCEPTED_RISK nuevo con aprobación de la usuaria), 1 Low heredado aceptado. Las 5
  deps nuevas sin CVE conocido.
- 2 hallazgos Low adicionales (W-1, W-2) aceptados como deuda documentada por decisión de la
  usuaria — no bloquean.
- Triage completo en la revisión de `daw-sec-auditor` (2026-09-07).
- Result: **PASSED** — no hay Critical/High abiertos; todos los Medium suprimidos con las 7
  columnas (F-SAST-18) y dentro de la ventana de 6 meses (F-SAST-19).
