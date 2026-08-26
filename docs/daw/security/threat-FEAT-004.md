# Threat Model FEAT-004: Módulo Oficina (carga de archivo de corte y generación de orden de trabajo)

| Field | Value |
|-------|-------|
| Ticket | FEAT-004 |
| Date | 2026-08-26 |
| Componentes analizados | `POST /api/ordenes/extraer`, `POST /api/ordenes/confirmar`, `GET /api/ordenes`, `GET /api/ordenes/{id}/documento`, `pdf_extraction_service.py`, `orden_service.py`, `barcode_service.py`, extensión de `product_service.py`, tablas `ordenes`/`piezas_orden`, módulo frontend `oficina/` |

## Componentes y su rol (F-TM-01, F-TM-06)

| Componente | Rol |
|---|---|
| `POST /api/ordenes/extraer` | Recibe un archivo PDF subido por el usuario — primer punto donde entra **contenido binario no confiable** a este módulo (distinto a los tickets anteriores, que solo recibían JSON) |
| `pdf_extraction_service.py` | Parsea el PDF con `pdfplumber` (librería de terceros) y extrae datos estructurados; no persiste nada |
| `POST /api/ordenes/confirmar` | Recibe el JSON (potencialmente editado por el usuario) y, en una sola transacción, matchea/crea producto, compromete stock y persiste la orden con NEST |
| `product_service.py` (extensión) | Nuevas funciones: matching por tolerancia, `comprometer_stock`, alta automática con `stock=0` |
| `barcode_service.py` | Genera la imagen CODE_128 (`python-barcode`) a partir del NEST ya persistido |
| `GET /api/ordenes/{id}/documento` | Genera on-demand (con `reportlab`) el PDF descargable con el detalle de piezas + código de barras |
| `GET /api/ordenes` | Lectura — lista/filtra/busca órdenes, expuesta a cualquier usuario autenticado (RF-19-a) |
| Tablas `ordenes` / `piezas_orden` (SQLite) | Persistencia — primer modelo del proyecto con relación FK padre-hijo |
| `oficina/services/orden.service.ts` | Cliente Angular — sube el archivo (`FormData`), envía la confirmación, descarga el PDF como blob |

## Límites de confianza (F-TM-02)

Reutiliza los límites ya declarados en `docs/daw/security/threat-FEAT-001.md` y agrega uno nuevo:

1. **Navegador ↔ API backend** — toda request a `/api/ordenes/*` cruza este límite; se protege con
   el mismo `get_current_user` (Bearer JWT) que ya audita FEAT-001. Sin cambios respecto a los
   tickets anteriores.
2. **API backend ↔ SQLite** — vía SQLAlchemy ORM, sin SQL crudo. Sin cambios.
3. **NUEVO — API backend ↔ contenido binario no confiable (`pdfplumber`)**: el archivo subido por el
   usuario es contenido arbitrario que una librería de terceros parsea. Este es el primer límite de
   confianza de este tipo en el proyecto (los tickets anteriores solo procesaban JSON validado por
   Pydantic). Cruzarlo sin controles es la superficie de ataque nueva más relevante de este ticket.

## Análisis STRIDE por componente

### `POST /api/ordenes/extraer` (subida de archivo — superficie nueva)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Spoofing | N/A — cubierto por `get_current_user`, ya mitigado en FEAT-001 | — | — | Reutiliza la mitigación existente |
| Tampering | 🟠 Un archivo con extensión `.pdf` pero contenido arbitrario (spoofing de tipo) podría explotar comportamiento inesperado del parser | Medium | Medium | Validar magic bytes (`%PDF-`) antes de invocar `pdfplumber`, además de la validación de extensión (FR-01) |
| Denial of Service | 🟠 Un PDF bajo el límite de 10MB (FR-02) pero diseñado para parsear extremadamente lento o consumir memoria excesiva (objetos anidados, decompression bomb interna) podría degradar el worker | Medium | High | **Mitigación obligatoria**: (a) límite ya definido de 10MB (FR-02); (b) límite explícito de páginas a procesar (máx. 50 páginas por archivo, rechazo con `ArchivoCorteInvalidoError` si se excede); (c) capturar cualquier excepción/timeout de `pdfplumber` dentro de `pdf_extraction_service` sin dejar que un fallo de la librería tumbe el worker |
| Information Disclosure | 🟡 Un error de parsing no controlado podría filtrar el traceback interno de `pdfplumber` en la respuesta HTTP | Low | Low | Capturar toda excepción de la librería dentro de `pdf_extraction_service` y remapear siempre a `ArchivoCorteInvalidoError` (422) con mensaje genérico — nunca propagar el traceback original al cliente |
| Elevation of Privilege | N/A — mismo modelo sin roles de RF-19-a, ya aceptado en FEAT-001/002/003 | — | — | Accepted risk heredado |

### `POST /api/ordenes/confirmar` (transacción de negocio)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Tampering | 🟡 El usuario puede editar los valores extraídos antes de confirmar (comportamiento **previsto** por FR-08/FR-09, no un bypass) pero sin límites de rango podría enviar `multiplicidad`, `espesor`, `largo` o `ancho` con valores absurdos (negativos, cero o extremadamente grandes) | Medium | Medium | Validación de rango explícita en el schema Pydantic de confirmación: `multiplicidad: int = Field(gt=0, le=10000)`, `espesor/largo/ancho: float = Field(gt=0, le=100000)` — mismo criterio de "mayor a cero" que ya usa `ProductCreate` en FEAT-002 |
| Tampering | Inyección SQL | Low | Critical | SQLAlchemy ORM, sin SQL crudo — mismo patrón que `products`/`configuracion` |
| Tampering | 🟢 `ConfigDict(extra="forbid")` ausente permitiría que el cliente inyecte campos no esperados (ej. forzar directamente `stock_comprometido` de un producto vía el payload de confirmación) | Low | High | **Mitigación obligatoria**: `ConfigDict(extra="forbid")` en el schema `OrdenConfirmarRequest`, igual que en `ProductCreate`/`ProductUpdate` (FEAT-002) y `ConfiguracionUpdate` (FEAT-003) |
| Repudiation | Sin registro de qué usuario confirmó cada orden (`Orden` no tiene `user_id`) | — | — | Accepted risk — mismo patrón que FEAT-002/003 (workspace compartido sin auditoría, RF-19-a). No es una regresión de este ticket. |
| Information Disclosure | N/A — `OrdenResponse` solo expone datos de negocio, sin PII | — | — | — |
| Denial of Service | N/A — operación de una fila + una FK, sin llamadas externas | — | — | NFR-01/NFR-03 (<3s / <2s p95) ya cubiertos por diseño |
| Elevation of Privilege | 🟢 El flujo `crear_producto_automaticamente=true` permite crear un producto nuevo sin pasar por Inventario. Es el comportamiento previsto de RF-05-b, disponible para cualquier usuario autenticado — el mismo nivel de acceso que ya tiene para crear productos manualmente en FEAT-002 | — | — | No es una escalada real (mismo permiso ya existente); documentado como riesgo aceptado, consistente con el "Elevation of Privilege" ya aceptado en `threat-FEAT-001.md`/`threat-FEAT-002.md` (RF-19-a, sin RBAC) |

### `product_service.py` (extensión: matching, compromiso de stock, alta automática)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Tampering (integridad de datos) | 🟠 Si el alta automática (RF-05-b) no reutiliza `_find_duplicate`/`_normalize_material`, podría crear un producto duplicado sin que la invariante de unicidad de FEAT-002 lo impida | Medium | Medium | **Mitigación obligatoria**: el alta automática invoca explícitamente `_find_duplicate` y `_normalize_material` antes de insertar, igual que `create_product` |
| Tampering | 🟢 `comprometer_stock` podría dejar `stock_comprometido` en un estado inconsistente si la orden falla a mitad de camino | Low | Medium | Un único `db.commit()` al final de `confirmar_orden` (todo o nada); cualquier excepción antes del commit hace rollback completo, sin escrituras parciales |

### `GET /api/ordenes` (listado/búsqueda)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Information Disclosure | N/A — datos de negocio compartidos por diseño (workspace único, RF-19-a) | — | — | — |
| Denial of Service | 🟢 Búsqueda por NEST con `LIKE '%...%'` sin límite de resultados podría degradar con un volumen alto de órdenes | Low | Low | Paginación o límite razonable de resultados (ej. 100) si el volumen lo justifica — a validar contra el volumen real esperado; no bloqueante para este ticket dado el uso interno |

### `GET /api/ordenes/{id}/documento` (generación de PDF + código de barras)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Denial of Service | 🟢 Generar el PDF on-demand en cada descarga (no se persiste) tiene un costo por request, pero es proporcional al tamaño de la orden (uso interno, volumen bajo) | Low | Low | Aceptado sin mitigación adicional — mismo perfil que el resto de endpoints autenticados |
| Information Disclosure | N/A — el documento solo contiene datos de negocio ya visibles vía `GET /api/ordenes/{id}` | — | — | — |
| Tampering | N/A — el NEST y los datos de la orden ya están persistidos e inmutables en este flujo (no hay edición de orden confirmada, fuera de alcance del PRD) | — | — | — |

### Dependencia nueva (supply chain, W-TM-01)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| — | Se agregan 4 librerías nuevas (`pdfplumber`, `python-barcode`, `pyzbar`, `reportlab`), ampliando la superficie de dependencias de terceros | Low | Medium | Fijar rangos de versión acotados en `requirements.txt` (mismo criterio que las dependencias existentes, ej. `pdfplumber>=0.11,<1.0`); el SAST de CODE (F-SAST-13/16) debe escanear CVEs conocidos de estas 4 librerías antes de cerrar el ticket |

### Frontend (`oficina/services/orden.service.ts`, componentes de revisión)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Tampering (XSS) | N/A — sin `[innerHTML]` planeado; el listado de piezas y los campos extraídos se renderizan con binding por defecto de Angular (sanitizado) | — | — | Mismo patrón limpio de FEAT-002/003 |
| Tampering (CSRF) | N/A — auth Bearer, no cookies de sesión | — | — | Igual que tickets anteriores |

## Clasificación de datos sensibles (F-TM-05)

`material`, `espesor`, `largo`, `ancho`, `multiplicidad`, `tiempo_ejecucion_estimado`, listado de
piezas, NEST: datos de negocio (manufactura), **no PII, no credenciales, no financieros**. El único
dato sensible en la cadena (el JWT de sesión) ya está cubierto por el threat model de FEAT-001; este
ticket lo reutiliza sin modificarlo. F-TM-07 (cifrado de PII/credenciales) no aplica — no hay PII ni
credenciales nuevas.

El archivo PDF subido por el usuario **no se persiste** tras la extracción (se procesa en memoria y
se descarta); esto evita un problema de retención de datos de negocio sin política definida y reduce
la superficie de un eventual leak de archivos.

## Mitigaciones a incorporar en la spec

1. **Validar magic bytes (`%PDF-`)** además de la extensión `.pdf`, antes de invocar `pdfplumber`.
2. **Límite explícito de páginas a procesar** (máx. 50) y captura total de excepciones de
   `pdfplumber` dentro de `pdf_extraction_service`, remapeadas siempre a `ArchivoCorteInvalidoError`
   (422) sin propagar tracebacks al cliente.
3. **Validación de rango numérico** en `OrdenConfirmarRequest` (`multiplicidad: Field(gt=0, le=10000)`,
   `espesor/largo/ancho: Field(gt=0, le=100000)`).
4. **`ConfigDict(extra="forbid")`** en `OrdenConfirmarRequest` (y en cualquier otro schema de entrada
   de este módulo).
5. El alta automática de producto (RF-05-b) **reutiliza explícitamente** `_find_duplicate` y
   `_normalize_material` de `product_service.py` — no construye el `Product` de forma independiente.
6. **Un único `db.commit()`** al final de `confirmar_orden` (todo-o-nada, sin escrituras parciales).
7. Fijar rangos de versión acotados para `pdfplumber`, `python-barcode`, `pyzbar` y `reportlab` en
   `requirements.txt`.
8. El PDF subido **no se persiste** en disco/DB tras la extracción — se procesa en memoria y se
   descarta.

## Resultado

```
┌─────────────────────────────────────────────────────────┐
│  /daw-threat-modeling — PASSED                           │
├─────────────────────────────────────────────────────────┤
│  Attack surfaces identified: 5 (extraer, confirmar,       │
│    listar, documento, product_service extendido)          │
│  Trust boundaries declared: 3 (2 reutilizados de FEAT-001, │
│    1 nuevo: backend ↔ contenido binario no confiable)      │
│  Risks: C:0 H:0 M:5 L:6                                    │
│  🟠 5 mitigaciones obligatorias (magic bytes + límite de    │
│    páginas, rangos numéricos, extra="forbid",              │
│    reutilización de _find_duplicate, commit único) — todas  │
│    incorporadas a la spec antes de escribir código, no      │
│    quedan como riesgo abierto                               │
│  Report: docs/daw/security/threat-FEAT-004.md              │
└─────────────────────────────────────────────────────────┘
```
