# Spec FEAT-004: Módulo Oficina — carga de archivo de corte y generación de orden de trabajo

| Field | Value |
|-------|-------|
| Ticket | FEAT-004 |
| PRD | docs/daw/prd/prd-FEAT-004.md |
| Tier | FEATURE |
| Date | 2026-08-26 |
| Spec loops | 1 |

## Summary

Se agrega un módulo `ordenes` (backend) que expone 4 endpoints: extraer datos de un PDF (sin
persistir), confirmar una orden (persistiendo con NEST, comprometiendo stock del maestro con
matching por tolerancia), listar/buscar órdenes, y descargar el documento PDF con código de barras.
El parseo usa `pdfplumber` y trata cada página del PDF como un borrador de orden independiente. La
confirmación es una transacción única (`db.flush()` para obtener el id → asignar `nest_code` →
`db.commit()`); si no hay producto que matchee por tolerancia, responde 409 sin persistir nada, y el
cliente reintenta con `crear_producto_automaticamente=true`. El frontend agrega un módulo `oficina`
que sigue el patrón ya usado por `inventario`/`configuracion`.

## Coverage: PRD → blocks

| Requirement | Covered by |
|---|---|
| FR-01 | Block 4 |
| FR-02 | Block 4 |
| FR-03 | Block 2 |
| FR-04 | Block 2 |
| FR-05 | Block 2 |
| FR-06 | Block 2 |
| FR-07 | Block 2 |
| FR-08 | Block 6 |
| FR-09 | Block 4, Block 6 |
| FR-10 | Block 4 |
| FR-11 | Block 1, Block 4 |
| FR-12 | Block 3 |
| FR-13 | Block 3, Block 4 |
| FR-14 | Block 4 |
| FR-15 | Block 3, Block 4 |
| FR-16 | Block 4, Block 6 |
| FR-17 | Block 5 |
| FR-18 | Block 4, Block 6 |
| FR-19 | Block 4, Block 6 |
| FR-20 | Block 4, Block 5 |
| NFR-01 | Strategy: procesamiento 100% en memoria, límite de 50 páginas y 10MB acotan el costo de `pdf_extraction_service`; test de performance en Block 2 |
| NFR-02 | Strategy: `barcode_service` genera con `module_width=0.3mm`/300 DPI; test de decodificación con `pyzbar` en Block 5 |
| NFR-03 | Strategy: índice en `ordenes.nest_code`, query de listado sin joins pesados; test de performance en Block 4 |

## Dependencies between blocks

`Block 1` (modelos) → `Block 2` (extracción, independiente de DB) y `Block 3` (extensión de
`product_service`, independiente de `Orden`) pueden implementarse en paralelo tras `Block 1`, pero se
numeran en secuencia por simplicidad de revisión. `Block 4` depende de `Block 1`, `Block 2` y
`Block 3` (los integra). `Block 5` depende de `Block 4` (necesita `Orden` persistida y el router ya
creado). `Block 6` depende de `Block 4` y `Block 5` (consume los 4 endpoints). Orden de ejecución:
1 → 2 → 3 → 4 → 5 → 6.

## Block 1 — Modelos de datos y excepciones de dominio

**Files**
- `backend/app/models/orden.py` (new) — modelos `Orden` y `PiezaOrden`.
- `backend/app/models/__init__.py` (modified) — registrar `Orden`, `PiezaOrden` en `__all__`.
- `backend/app/core/exceptions.py` (modified) — agregar `ArchivoCorteInvalidoError`,
  `ProductoSinCoincidenciaError`, `OrdenNotFoundError`, junto a las ya existentes
  (`EmailAlreadyRegisteredError`, `ProductAlreadyExistsError`, `ProductNotFoundError`).

**Logic**

`Orden` es el primer modelo del proyecto con una relación FK padre-hijo (`PiezaOrden.orden_id`).
`nest_code` se define `nullable=True` a nivel de esquema por una razón técnica deliberada: se deriva
del `id` autoincremental de la propia fila (`f"NEST-{id:06d}"`), que solo se conoce después del
`INSERT`. El flujo correcto (documentado también en Block 4) es: `db.add(orden)` con
`nest_code=None` → `db.flush()` (asigna `id`, ejecuta el INSERT) → `orden.nest_code = f"NEST-{orden.id:06d}"`
→ `db.commit()`. La invariante de negocio (nunca hay una fila comiteada con `nest_code` nulo) se
sostiene porque cualquier excepción entre el flush y el commit hace rollback completo de la
transacción — no queda nunca una fila a medio escribir en disco.

**Data model**

`Orden`:
| Campo | Tipo | Constraints |
|---|---|---|
| `id` | Integer | PK, autoincrement |
| `nest_code` | String | unique, nullable=True (ver nota arriba), index |
| `estado` | String | not null, default `"vigente"` (valores válidos: `"vigente"`, `"cerrada"` — este ticket solo escribe `"vigente"`; la transición a `"cerrada"` es de Taller, fuera de alcance) |
| `multiplicidad` | Integer | not null |
| `material` | String | not null |
| `espesor` | Float | not null |
| `largo` | Float | not null |
| `ancho` | Float | not null |
| `tiempo_ejecucion_estimado` | String | nullable |
| `indice_formato` | String | nullable (ej. "2/3", trazabilidad a la hoja física del PDF original) |
| `product_id` | Integer | FK → `products.id`, not null |
| `created_at` | DateTime | not null, default `func.now()` |

`PiezaOrden`:
| Campo | Tipo | Constraints |
|---|---|---|
| `id` | Integer | PK, autoincrement |
| `orden_id` | Integer | FK → `ordenes.id`, not null, index |
| `ref` | String | nullable (las filas "Saved scrap" no traen Ref.) |
| `cantidad` | Integer | not null |
| `pieza` | String | not null |
| `descripcion` | String | not null |
| `es_recorte` | Boolean | not null, default `False` |
| `largo_mm` | Float | nullable (solo si `es_recorte=True`) |
| `ancho_mm` | Float | nullable (solo si `es_recorte=True`) |

**Error handling**
- N/A en este bloque (no expone lógica ni endpoints; las excepciones se declaran pero se usan desde
  Block 2/3/4).

**Required tests**
- [ ] `backend/tests/unit/test_orden_model.py::test_crea_orden_con_piezas` — crea una `Orden` con 2
  `PiezaOrden` asociadas directamente contra la sesión y verifica la relación por `orden_id`.
- [ ] `backend/tests/unit/test_orden_model.py::test_nest_code_se_asigna_post_flush` — verifica que
  `db.flush()` asigna `id` antes de setear `nest_code`, y que el valor final es único tras `commit`.
- [ ] `backend/tests/unit/test_orden_model.py::test_tablas_registradas_en_metadata` — confirma que
  `Base.metadata.create_all()` crea las tablas `ordenes` y `piezas_orden` (verifica que el barrel de
  `models/__init__.py` las registró).

**Completion criterion**
Los 3 tests pasan; `Base.metadata.create_all()` crea ambas tablas sin errores.

## Block 2 — Extracción de datos del archivo de corte

**Files**
- `backend/requirements.txt` (modified) — agregar `pdfplumber>=0.11,<1.0`.
- `backend/app/schemas/orden.py` (new) — `PiezaExtraida`, `OrdenBorrador` (schemas de solo lectura,
  sin persistencia).
- `backend/app/services/pdf_extraction_service.py` (new) — `extraer_paginas(contenido: bytes) -> list[OrdenBorrador]`.

**Logic**

Abre el PDF con `pdfplumber.open(io.BytesIO(contenido))`. Límite duro de 50 páginas — si el archivo
tiene más, `ArchivoCorteInvalidoError` sin procesar ninguna (mitigación DoS del threat model). Por
cada página:
1. Busca la tabla "Datos generales" (clave-valor) y la tabla de "Piezas" (columnas Ref./Cant./Pieza/Descripción).
   Si falta cualquiera de las dos → `ArchivoCorteInvalidoError` (FR-06).
2. Extrae: `Multiplicidad`, `Dimensiones [mm]` (split en `largo`/`ancho`), `Espesor [mm]`, `Material`,
   `Tiempo de ejecución estimado`, `Índice formato`.
3. Por cada fila de la tabla de piezas: `ref` (vacío → `None`), `cantidad` (int), `pieza` (str),
   `descripcion` (str).
4. Si `descripcion.strip() == "Saved scrap"`: parsea `pieza` con el patrón
   `^(?P<largo>[\d.]+)x(?P<ancho>[\d.]+)_RECT_SCRAP$` (case-insensitive) → `largo_mm`, `ancho_mm`
   como float, `es_recorte=True`. Si el patrón no matchea en una fila marcada "Saved scrap" →
   `ArchivoCorteInvalidoError` (estructura reconocida pero corrupta).
5. Cualquier excepción interna de `pdfplumber` (parsing, memoria, formato) se captura dentro de esta
   función y se remapea siempre a `ArchivoCorteInvalidoError` con mensaje genérico — nunca se
   propaga el traceback original (mitigación de Information Disclosure del threat model).

Devuelve `list[OrdenBorrador]`, uno por página, sin tocar la base de datos.

**Input validation**
- `contenido`: bytes no vacíos (validado por el caller en Block 4; aquí se asume no vacío).
- Máximo 50 páginas por archivo.
- Campos numéricos (`multiplicidad`, `espesor`, `largo`, `ancho`) deben parsear como número; si no
  → `ArchivoCorteInvalidoError`.

**Error handling**
| Error | Causa | Manejo |
|---|---|---|
| `ArchivoCorteInvalidoError` | Faltan tablas esperadas, patrón de "Saved scrap" corrupto, más de 50 páginas, campo numérico no parseable, o excepción interna de `pdfplumber` | Se lanza desde el servicio; Block 4 la mapea a 422 |

**Required tests**
- [ ] `test_pdf_extraction_service.py::test_extrae_ejemplo_1` — usa
  `docs/Archivos de Corte/Ejemplo 1.pdf` real: 1 página, multiplicidad=1, dimensiones 1310.000x580.000,
  espesor=12.700, material="SAE_1010", 4 piezas, 0 recortes.
- [ ] `test_pdf_extraction_service.py::test_extrae_ejemplo_2_multipagina` — usa `Ejemplo 2.pdf`: 3
  páginas, `indice_formato` "1/3"/"2/3"/"3/3", cada una con su propio listado de piezas.
- [ ] `test_pdf_extraction_service.py::test_extrae_ejemplo_3_con_saved_scrap` — usa `Ejemplo 3.pdf`:
  2 piezas normales + 2 filas "Saved scrap" con `largo_mm`/`ancho_mm` = (1085.00, 1500.00) y
  (955.00, 559.16) respectivamente, `ref=None` en ambas.
- [ ] `test_pdf_extraction_service.py::test_rechaza_pdf_sin_tablas_esperadas` — PDF válido sin las
  tablas → `ArchivoCorteInvalidoError` (sad path, FR-06).
- [ ] `test_pdf_extraction_service.py::test_rechaza_mas_de_50_paginas` — PDF sintético de 51 páginas
  → `ArchivoCorteInvalidoError` (sad path, NFR-01/DoS).
- [ ] `test_pdf_extraction_service.py::test_captura_excepcion_interna_pdfplumber` — mock de
  `pdfplumber` lanzando una excepción interna → se remapea a `ArchivoCorteInvalidoError`, no
  propaga el mensaje original (sad path, Information Disclosure).

**Completion criterion**
Los 3 PDFs reales extraen exactamente los valores documentados arriba (assertions concretas por
campo), y los 3 tests de sad-path pasan.

## Block 3 — Extensión de `product_service`: matching por tolerancia, compromiso de stock, alta automática

**Files**
- `backend/app/services/product_service.py` (modified) — agregar `buscar_por_tolerancia`,
  `comprometer_stock`, `crear_producto_automatico`.

**Logic**

- `buscar_por_tolerancia(db, material, espesor, largo, ancho, margen) -> Product | None`: compara
  `_normalize_material(material) == _normalize_material(p.material)` (reutiliza el helper existente),
  `p.espesor == espesor` (exacto), y `abs(p.largo - largo) <= margen and abs(p.ancho - ancho) <= margen`.
- `comprometer_stock(db, product, cantidad) -> Product`: `product.stock_comprometido += cantidad`;
  `db.flush()` (sin commit — el commit lo hace `orden_service` al final de la transacción completa).
- `crear_producto_automatico(db, material, espesor, largo, ancho) -> Product`: llama primero a
  `_find_duplicate` (defensivo, evita duplicados incluso en este camino) — si encuentra uno, lanza
  `ProductAlreadyExistsError`; si no, arma `Product(material=material, espesor=espesor, largo=largo,
  ancho=ancho, stock=0, stock_comprometido=0, punto_pedido=0)`, `db.add(product)`, `db.flush()` (sin
  commit). No pasa por el schema HTTP `ProductCreate` (que exige `stock > 0` para el alta manual de
  FEAT-002; esa validación no se toca).

**Input validation**
- N/A (funciones de servicio internas, no reciben input HTTP directo; la validación de rango del
  payload ocurre en Block 4).

**Error handling**
| Error | Causa | Manejo |
|---|---|---|
| `ProductAlreadyExistsError` | `crear_producto_automatico` encuentra un duplicado exacto vía `_find_duplicate` (condición de carrera defensiva) | Se propaga tal cual (ya mapeada a 400 en `products.py`; Block 4 la remapea a 409 en el contexto de confirmación, ver Block 4) |

**Required tests**
- [ ] `test_product_service.py::test_buscar_por_tolerancia_encuentra_dentro_del_margen` — producto
  con dimensiones dentro del margen configurado.
- [ ] `test_product_service.py::test_buscar_por_tolerancia_no_encuentra_fuera_del_margen` — sad path.
- [ ] `test_product_service.py::test_buscar_por_tolerancia_material_case_insensitive` — reutiliza
  `_normalize_material`.
- [ ] `test_product_service.py::test_comprometer_stock_incrementa_correctamente` — incluye un caso
  sintético con `multiplicidad > 1` (ningún PDF de ejemplo lo cubre; riesgo ya documentado en el PRD).
- [ ] `test_product_service.py::test_crear_producto_automatico_stock_cero` — verifica
  `stock=0, stock_comprometido=0, punto_pedido=0`.
- [ ] `test_product_service.py::test_crear_producto_automatico_rechaza_duplicado` — sad path,
  `ProductAlreadyExistsError`.

**Completion criterion**
Las 6 funciones/casos tienen test unitario pasando, incluyendo el caso `multiplicidad > 1` sintético.

## Block 4 — `orden_service`, endpoints de extracción/confirmación/listado, generación de NEST

**Files**
- `backend/app/schemas/orden.py` (modified) — agregar `PiezaConfirmar`, `OrdenConfirmarRequest`,
  `PiezaResponse`, `OrdenResponse`, `OrdenListItem`.
- `backend/app/services/orden_service.py` (new) — `confirmar_orden`, `listar_ordenes`.
- `backend/app/api/routes/ordenes.py` (new) — `POST /api/ordenes/extraer`, `POST /api/ordenes/confirmar`,
  `GET /api/ordenes`.
- `backend/app/api/router.py` (modified) — registrar el router de órdenes con
  `include_router(ordenes_router, prefix="/ordenes", tags=["ordenes"])`.

**API contract**

`POST /api/ordenes/extraer`
- Request: `multipart/form-data`, campo `archivo` (UploadFile).
- Validaciones antes de invocar `pdf_extraction_service`: extensión `.pdf` (FR-01), magic bytes
  `%PDF-` (mitigación threat model), tamaño ≤ 10 MB (FR-02, chequeado sobre los bytes leídos).
- Response 200: `{"paginas": [OrdenBorrador, ...]}` (schema de Block 2).
- Errores: `400` extensión o magic bytes inválidos · `413` tamaño excedido · `422`
  `ArchivoCorteInvalidoError` (estructura no reconocida) · `401` no autenticado.
- Auth: `Depends(get_current_user)`.

`POST /api/ordenes/confirmar`
- Request (`OrdenConfirmarRequest`, `ConfigDict(extra="forbid")`):
  `indice_formato: str | None`, `multiplicidad: int = Field(gt=0, le=10000)`, `material: str`,
  `espesor: float = Field(gt=0, le=100000)`, `largo: float = Field(gt=0, le=100000)`,
  `ancho: float = Field(gt=0, le=100000)`, `tiempo_ejecucion_estimado: str | None`,
  `piezas: list[PiezaConfirmar]`, `crear_producto_automaticamente: bool = False`.
  `PiezaConfirmar` (`ConfigDict(extra="forbid")`): `ref: str | None`,
  `cantidad: int = Field(gt=0, le=100000)`, `pieza: str`, `descripcion: str`,
  `es_recorte: bool = False`, `largo_mm: float | None`, `ancho_mm: float | None`.
- Lógica (`orden_service.confirmar_orden`, una sola transacción):
  1. `margen = configuracion_service.get_margen_tolerancia(db)`.
  2. `producto = product_service.buscar_por_tolerancia(db, material, espesor, largo, ancho, margen)`.
  3. Si `producto is None` y `crear_producto_automaticamente is False` → `ProductoSinCoincidenciaError`
     (sin ningún `db.add`/`db.commit` — nada se persiste).
  4. Si `producto is None` y `crear_producto_automaticamente is True` →
     `producto = product_service.crear_producto_automatico(db, material, espesor, largo, ancho)`.
  5. `product_service.comprometer_stock(db, producto, multiplicidad)`.
  6. `orden = Orden(nest_code=None, estado="vigente", product_id=producto.id, ...)`; `db.add(orden)`;
     `db.flush()`; `orden.nest_code = f"NEST-{orden.id:06d}"`; crear una `PiezaOrden` por cada
     elemento de `piezas` con `orden_id=orden.id`.
  7. `db.commit()` (único commit de toda la operación — todo o nada).
  8. `alerta_stock_bajo = (producto.stock - producto.stock_comprometido) <= producto.punto_pedido`.
- Response 201: `OrdenResponse` (`id, nest_code, estado, multiplicidad, material, espesor, largo,
  ancho, tiempo_ejecucion_estimado, indice_formato, product_id, created_at, piezas: [PiezaResponse],
  alerta_stock_bajo: bool`).
- Errores: `401` no autenticado · `422` validación de payload (rango numérico, `extra="forbid"`) ·
  `409` `ProductoSinCoincidenciaError` (incluye `material, espesor, largo, ancho` en el body para que
  el cliente arme el reintento) · `409` `ProductAlreadyExistsError` (condición de carrera rara).
- Auth: `Depends(get_current_user)`.

`GET /api/ordenes`
- Query params opcionales: `estado: Literal["vigente", "cerrada"] | None`, `nest: str | None`
  (búsqueda parcial, `LIKE '%valor%'` case-insensitive sobre `nest_code`, combinable con `estado`).
- Response 200: `{"ordenes": [OrdenListItem, ...]}` (`id, nest_code, estado, material, espesor,
  largo, ancho, multiplicidad, created_at`).
- Errores: `401` no autenticado · `422` valor de `estado` fuera del enum.
- Auth: `Depends(get_current_user)`.

**Data model**
Ninguno nuevo (reutiliza `Orden`/`PiezaOrden` de Block 1).

**Input validation**
Ver rangos en `OrdenConfirmarRequest`/`PiezaConfirmar` arriba. `estado` restringido a
`Literal["vigente", "cerrada"]` en el query param de listado.

**Error handling**
| Error | HTTP | Body |
|---|---|---|
| Extensión/magic bytes inválidos | 400 | mensaje genérico |
| Archivo > 10MB | 413 | tamaño máximo permitido |
| `ArchivoCorteInvalidoError` | 422 | mensaje genérico, sin traceback |
| Validación Pydantic (rango, `extra="forbid"`) | 422 | detalle automático de FastAPI |
| `ProductoSinCoincidenciaError` | 409 | `{material, espesor, largo, ancho}` |
| `ProductoSinCoincidenciaError` con `crear_producto_automaticamente=true` pero un duplicado exacto aparece por condición de carrera | 409 | `ProductAlreadyExistsError` propagada desde `crear_producto_automatico` (Block 3) |
| Sin autenticación | 401 | estándar de `get_current_user` |

**Required tests**
- [ ] `test_ordenes_extraer.py::test_extraer_pdf_real_devuelve_paginas` — `Ejemplo 1.pdf` → 200.
- [ ] `test_ordenes_extraer.py::test_extraer_rechaza_extension_invalida` — sad path, 400.
- [ ] `test_ordenes_extraer.py::test_extraer_rechaza_archivo_grande` — sintético >10MB, 413.
- [ ] `test_ordenes_extraer.py::test_extraer_rechaza_estructura_invalida` — PDF sin tablas, 422.
- [ ] `test_ordenes_confirmar.py::test_confirmar_con_producto_existente` — 201, `stock_comprometido`
  incrementado en el maestro.
- [ ] `test_ordenes_confirmar.py::test_confirmar_sin_match_devuelve_409` — sad path, orden NO creada.
- [ ] `test_ordenes_confirmar.py::test_confirmar_con_alta_automatica` — 201, producto creado con
  `stock=0`.
- [ ] `test_ordenes_confirmar.py::test_confirmar_rechaza_multiplicidad_invalida` — sad path, 422
  (`multiplicidad<=0`).
- [ ] `test_ordenes_confirmar.py::test_nest_code_es_secuencial_y_unico` — dos confirmaciones
  consecutivas generan NESTs distintos y correlativos.
- [ ] `test_ordenes_confirmar.py::test_confirmar_devuelve_alerta_stock_bajo_cuando_corresponde` —
  producto con `stock - stock_comprometido <= punto_pedido` tras confirmar → `alerta_stock_bajo:
  true` en la respuesta (AC-15).
- [ ] `test_ordenes_confirmar.py::test_confirmar_condicion_carrera_duplicado_devuelve_409` — sad
  path, `ProductAlreadyExistsError` de `crear_producto_automatico` mapeada a 409.
- [ ] `test_ordenes_listado.py::test_filtra_por_estado` — `?estado=vigente`.
- [ ] `test_ordenes_listado.py::test_sin_filtro_muestra_todas_las_ordenes` — AC-19.
- [ ] `test_ordenes_listado.py::test_busca_por_nest_parcial_combinado_con_estado` — AC-20.
- [ ] `test_ordenes_contracts.py::test_shape_orden_response` — shape exacto.
- [ ] `test_ordenes_auth.py::test_los_tres_endpoints_rechazan_sin_token` — 401 en `/extraer`,
  `/confirmar`, `/` (GET).

**Completion criterion**
Los 16 tests pasan; AC-01 a AC-15 y AC-18 a AC-21 del PRD quedan cubiertos por al menos un test.

## Block 5 — Código de barras y documento PDF descargable

**Files**
- `backend/requirements.txt` (modified) — agregar `python-barcode>=0.15,<1.0`, `pyzbar>=0.1.9,<1.0`,
  `reportlab>=4.0,<5.0`.
- `backend/app/services/barcode_service.py` (new) — `generar_codigo_barras(nest_code: str) -> bytes`.
- `backend/app/services/pdf_document_service.py` (new) —
  `generar_documento_orden(orden: Orden, piezas: list[PiezaOrden]) -> bytes`.
- `backend/app/api/routes/ordenes.py` (modified) — agregar `GET /api/ordenes/{id}/documento`.

**API contract**

`GET /api/ordenes/{id}/documento`
- Path param: `id: int` (id numérico de la orden, no el `nest_code`).
- Response 200: `application/pdf` (bytes generados on-demand, nunca persistidos en disco/DB).
- Errores: `401` no autenticado · `404` `OrdenNotFoundError` (id inexistente).
- Auth: `Depends(get_current_user)`.

**Logic**

`barcode_service.generar_codigo_barras`: `python-barcode` con `Code128` + `ImageWriter`, opciones
`module_width=0.3` (mm), `module_height=15.0`, `quiet_zone=6.5`, `dpi=300` (mitigación explícita del
riesgo de código ilegible documentado en AGENTS.md). Devuelve bytes PNG en memoria (`BytesIO`), sin
archivo temporal en disco.

`pdf_document_service.generar_documento_orden`: usa `reportlab` (platypus) para componer: encabezado
(NEST, material, espesor, dimensiones, multiplicidad), tabla de piezas (ref, cantidad, pieza,
descripción), imagen del código de barras embebida desde los bytes en memoria. Devuelve bytes PDF.

El endpoint lee la `Orden` + sus `PiezaOrden` por `id`, genera el código de barras y el documento
en cada request (no se cachea ni se persiste el binario — mitigación de retención de datos del
threat model).

**Error handling**
| Error | HTTP | Causa |
|---|---|---|
| `OrdenNotFoundError` | 404 | `id` no existe en `ordenes` |

**Required tests**
- [ ] `test_barcode_service.py::test_genera_imagen_png_valida` — header PNG válido.
- [ ] `test_barcode_service.py::test_codigo_decodificable_por_pyzbar_a_300dpi` — **crítico**: decodifica
  la imagen generada con `pyzbar` y confirma que el valor == `nest_code` original (NFR-02, AC-17).
- [ ] `test_pdf_document_service.py::test_genera_pdf_valido_con_barcode_embebido` — header `%PDF`
  válido, tamaño de bytes > 0.
- [ ] `test_ordenes_documento.py::test_descarga_documento_orden_existente` — 200,
  `content-type: application/pdf`.
- [ ] `test_ordenes_documento.py::test_documento_orden_inexistente_404` — sad path.
- [ ] `test_ordenes_documento.py::test_documento_rechaza_sin_auth` — 401.

**Completion criterion**
El test de decodificación con `pyzbar` pasa (verificación real, no solo "se generó una imagen"), y
los 5 tests restantes pasan.

## Block 6 — Frontend: módulo Oficina

**Files**
- `frontend/src/app/oficina/models/orden.models.ts` (new) — interfaces `OrdenBorrador`,
  `PiezaExtraida`, `OrdenConfirmarRequest`, `OrdenResponse`, `OrdenListItem`.
- `frontend/src/app/oficina/services/orden.service.ts` (new) — `subirArchivo`, `confirmarOrden`,
  `listarOrdenes`, `descargarDocumento`.
- `frontend/src/app/oficina/oficina.ts` / `.html` / `.scss` (modified) — reemplaza el stub,
  orquesta las 3 sub-vistas.
- `frontend/src/app/oficina/subir-archivo/subir-archivo.ts` / `.html` / `.scss` (new).
- `frontend/src/app/oficina/revision-borrador/revision-borrador.ts` / `.html` / `.scss` (new).
- `frontend/src/app/oficina/listado-ordenes/listado-ordenes.ts` / `.html` / `.scss` (new).

**Logic**

`orden.service.ts` (mismo patrón que `product.service.ts`/`configuracion.service.ts`:
`@Injectable({providedIn: 'root'})`, `inject(HttpClient)`):
- `subirArchivo(file: File): Observable<{paginas: OrdenBorrador[]}>` — arma `FormData`, `POST
  /api/ordenes/extraer`.
- `confirmarOrden(payload: OrdenConfirmarRequest): Observable<OrdenResponse>` — `POST
  /api/ordenes/confirmar`; el componente captura el 409 (`HttpErrorResponse`) para mostrar la
  advertencia de RF-05-a.
- `listarOrdenes(estado?: string, nest?: string): Observable<{ordenes: OrdenListItem[]}>` — `GET
  /api/ordenes` con `HttpParams`.
- `descargarDocumento(id: number): Observable<Blob>` — `GET /api/ordenes/{id}/documento`,
  `responseType: 'blob'`.

`Oficina` orquesta: subir → mostrar N borradores (uno por página) → revisar/confirmar cada uno
individualmente (decisión del PRD: sin confirmación en bloque) → listado.

`SubirArchivo`: input de archivo con validación de extensión en cliente (UX; la validación real es
del servidor) y llamada a `subirArchivo`.

`RevisionBorrador`: formulario editable con los campos del borrador actual, muestra `indice_formato`
para correlacionar con la hoja física (mitigación de riesgo del PRD); botón "Confirmar" llama a
`confirmarOrden` usando los valores editados (AC-10); si la respuesta es 409, muestra un diálogo con
los datos del producto no encontrado y un botón "Crear producto y confirmar" que reintenta con
`crear_producto_automaticamente: true`; si la respuesta 201 trae `alerta_stock_bajo: true`, muestra
un indicador visual (mismo patrón de alerta que ya usa `Inventario`, si existe, o un mensaje
equivalente).

`ListadoOrdenes`: filtro por estado + buscador por NEST (llamando a `listarOrdenes` con debounce
razonable), tabla de resultados, botón de descarga que llama a `descargarDocumento` y dispara la
descarga del blob con `URL.createObjectURL` + un enlace temporal con click programático.

**Error handling (frontend)**
Mismo patrón que `product-form.ts`: `err instanceof HttpErrorResponse && err.status === XXX` con
mensajes en español. El 401 ya lo intercepta `auth.interceptor.ts` (sin cambios necesarios acá).

**Required tests**
- [ ] `orden.service.spec.ts::arma FormData correctamente en subirArchivo`.
- [ ] `orden.service.spec.ts::propaga el error 409 de confirmarOrden`.
- [ ] `orden.service.spec.ts::arma los query params de listarOrdenes`.
- [ ] `subir-archivo.spec.ts::rechaza en cliente un archivo no-PDF`.
- [ ] `revision-borrador.spec.ts::muestra los datos extraídos en un formulario editable antes de
  confirmar` (AC-09).
- [ ] `revision-borrador.spec.ts::usa el valor editado en vez del extraído al confirmar` (AC-10).
- [ ] `revision-borrador.spec.ts::muestra el diálogo de advertencia ante 409 y reintenta con la bandera`.
- [ ] `revision-borrador.spec.ts::muestra el indicador de alerta_stock_bajo cuando viene en true`.
- [ ] `listado-ordenes.spec.ts::aplica el filtro de estado`.
- [ ] `listado-ordenes.spec.ts::combina filtro de estado con búsqueda por NEST`.

**Completion criterion**
Los 10 specs de Angular pasan (`ng test`); smoke manual del flujo completo
subir→revisar→confirmar→listar→descargar contra el backend real, documentado en VERIFY.

## Final verification

- Los 21 AC del PRD trazan a al menos un test concreto en algún bloque (tabla de cobertura arriba).
- Subir `Ejemplo 2.pdf` (3 páginas) produce 3 borradores independientes; confirmar los 3 genera 3
  `nest_code` únicos y consecutivos.
- El stock comprometido del producto matcheado (o recién creado) refleja la multiplicidad de cada
  orden confirmada, verificable desde el listado de Inventario (FEAT-002).
- El documento descargado de cualquier orden confirmada contiene un código de barras que `pyzbar`
  decodifica exactamente al `nest_code` de esa orden.
- El listado de órdenes filtra por estado y busca por NEST parcial, combinando ambos criterios.
- `backend/requirements.txt` incluye `pdfplumber`, `python-barcode`, `pyzbar`, `reportlab` con
  rangos de versión acotados.
