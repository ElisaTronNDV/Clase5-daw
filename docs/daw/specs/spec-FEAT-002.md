# Spec FEAT-002: Gestión de inventario (CRUD de productos)

| Field | Value |
|-------|-------|
| Ticket | FEAT-002 |
| PRD | docs/daw/prd/prd-FEAT-002.md |
| Tier | FEATURE |
| Date | 2026-08-25 |
| Spec loops | 0 |

## Summary

Se construye el módulo de Inventario como maestro de productos, independiente de Oficina/Taller
(que todavía no existen). Backend: modelo `Product` + CRUD (crear, editar, listar, obtener por id)
con chequeo de duplicados case-insensitive por material+espesor+largo+ancho, tanto al crear como al
editar. El campo `stock_comprometido` se inicializa en 0 y queda protegido contra escritura del
cliente (`extra="forbid"` en ambos schemas — mitigación del threat model) para cuando Oficina lo use
más adelante. Frontend: reemplaza el placeholder de Inventario por un listado real, más un formulario
reactivo compartido entre alta y edición. Se avanza en 3 bloques: backend → servicio Angular →
páginas y routing.

## Coverage: PRD → blocks

| Requirement | Covered by |
|---|---|
| FR-01 (crear producto) | Block 1, Block 3 |
| FR-02 (rechazar duplicado, crear y editar) | Block 1 |
| FR-03 (validación de campos obligatorios y > 0) | Block 1, Block 3 |
| FR-04 (id secuencial) | Block 1 |
| FR-05 (stock_comprometido = 0 al crear) | Block 1 |
| FR-06 (editar producto) | Block 1, Block 3 |
| FR-07 (stock_comprometido de solo lectura) | Block 1, Block 3 |
| FR-08 (listado completo) | Block 1, Block 3 |
| FR-09 (todo requiere autenticación) | Block 1 |
| NFR-01 (<2s p95 crear/editar/listar) | Strategy: Block 1, tests de performance con assert de wall-clock; sin llamadas externas ni I/O costoso en el camino crítico (mismo patrón que FEAT-001) |

## Dependencies between blocks

Block 1 (independiente) → Block 2 (necesita el contrato de API de Block 1) → Block 3 (necesita
`AuthService`/`authGuard`/`authInterceptor` ya existentes de FEAT-001 + `ProductService` de Block 2).

---

## Block 1 — Backend: modelo, schemas, servicio y endpoints de productos

**Files**
- `backend/app/models/product.py` (new) — modelo `Product`
- `backend/app/models/__init__.py` (modified) — registrar `Product` junto a `User` (si no,
  `db/session.py:init_db()` nunca crea la tabla `products` — gap detectado por el impact-scan)
- `backend/app/schemas/product.py` (new) — `ProductCreate`, `ProductUpdate`, `ProductOut`
- `backend/app/core/exceptions.py` (modified) — `ProductAlreadyExistsError(Exception)`,
  `ProductNotFoundError(Exception)`
- `backend/app/services/product_service.py` (new) — `get_product_by_id`, `list_products`,
  `create_product`, `update_product`
- `backend/app/api/routes/products.py` (new) — `POST /products`, `GET /products`,
  `GET /products/{id}`, `PUT /products/{id}`
- `backend/app/api/router.py` (modified) — incluye `products_router` con prefix `/products`
- `backend/tests/unit/test_product_service.py`, `backend/tests/integration/test_products_create.py`,
  `test_products_list.py`, `test_products_get.py`, `test_products_update.py`,
  `backend/tests/contract/test_products_contracts.py`,
  `backend/tests/performance/test_products_performance.py` (new)

**Logic**
`routes/products.py` no accede a la DB ni implementa lógica de negocio (regla de AGENTS.md): delega
todo a `product_service`, que usa `models.Product` para el acceso a datos — mismo patrón que
`auth.py`/`auth_service.py`. `product_service.py` centraliza la normalización de `material`
(`.strip().lower()`) en un único helper `_normalize_material()`, usado por `create_product` y
`update_product`, para que el chequeo de duplicados (FR-02) sea consistente entre ambos (gap
detectado por el impact-scan: no hay precedente de normalización de strings en el codebase, se
diseña desde cero acá). `update_product` excluye el propio `id` al buscar duplicados.

**API contract**

`POST /api/products`
- Request: `{"material": "SAE_1010", "espesor": 2.1, "largo": 3000, "ancho": 1500, "stock": 10, "punto_pedido": 5}`
- Response 201: `{"id": 1, "material": "SAE_1010", "espesor": 2.1, "largo": 3000, "ancho": 1500, "stock": 10, "stock_comprometido": 0, "punto_pedido": 5}`
- Errores: `400 {"detail": "product already exists with this material, thickness and dimensions"}`
  (AC-02) · `422` (automático de Pydantic: campo faltante — AC-03; valor ≤ 0 — AC-04; campo no
  reconocido como `stock_comprometido` — mitigación del threat model)
- Auth: Bearer JWT requerido (AC-09)

`GET /api/products`
- Response 200: `[ProductOut, ...]` (AC-08)
- Errores: `401`
- Auth: Bearer JWT requerido

`GET /api/products/{id}`
- Response 200: `ProductOut`
- Errores: `404 {"detail": "product not found"}` · `401`
- Auth: Bearer JWT requerido (enabler técnico para precargar el form de edición del Block 3 — sin AC
  propio, mismo criterio que `/health` en FEAT-001)

`PUT /api/products/{id}`
- Request: igual que `POST`
- Response 200: `ProductOut`
- Errores: `400` duplicado (AC-02, también al editar — excluye el propio id) · `404 {"detail": "product not found"}` ·
  `422` (igual que en `POST`, incluye rechazo de `stock_comprometido` — AC-07)
- Auth: Bearer JWT requerido

**Data model**
- Entidad `Product` (`backend/app/models/product.py`):
  - `id`: `Integer`, primary key, autoincrement
  - `material`: `String(255)`, `nullable=False`
  - `espesor`: `Float`, `nullable=False`
  - `largo`: `Float`, `nullable=False`
  - `ancho`: `Float`, `nullable=False`
  - `stock`: `Integer`, `nullable=False`
  - `stock_comprometido`: `Integer`, `nullable=False`, `default=0`
  - `punto_pedido`: `Integer`, `nullable=False`
- Sin `UNIQUE` a nivel de DB para material+espesor+largo+ancho: la comparación es case-insensitive
  (`.lower()`), algo que un `UNIQUE` de SQLite no expresa directamente — el chequeo vive en el
  service (FR-02).

**Input validation**
- `ProductCreate`/`ProductUpdate`: `material: str = Field(min_length=1, max_length=255)`,
  `espesor: float = Field(gt=0)`, `largo: float = Field(gt=0)`, `ancho: float = Field(gt=0)`,
  `stock: int = Field(gt=0)`, `punto_pedido: int = Field(gt=0)` — restricciones declarativas en el
  propio schema, mismo patrón que `UserCreate.password = Field(min_length=8)` (cierra el WARN del
  arch-auditor: nada de validación imperativa en el service).
- **`model_config = ConfigDict(extra="forbid")` en AMBOS `ProductCreate` y `ProductUpdate`**
  (mitigación obligatoria del threat model, `docs/daw/security/threat-FEAT-002.md`: sin esto, un
  cliente podría enviar `stock_comprometido` en el body y setearlo directamente — el plan original
  solo lo preveía en `Update`, se corrige acá para cubrir también `Create`).
- `ProductOut`: `model_config = ConfigDict(from_attributes=True)` (cierra el segundo WARN del
  arch-auditor: sin esto, `response_model=ProductOut` sobre un `Product` de SQLAlchemy falla en
  runtime — mismo patrón que `UserOut`).

**Error handling**
- `ProductAlreadyExistsError` (service, create y update) → ruta → `HTTPException(400, "product already registered with this material, thickness and dimensions")`
- `ProductNotFoundError` (service, get por id y update) → ruta → `HTTPException(404, "product not found")`
- Validación de Pydantic (campo vacío, valor ≤ 0, campo extra) → `422` automático de FastAPI
- Excepción no controlada → sube sin interceptarse; `DEBUG=False` (ya establecido en FEAT-001) no
  expone traceback

**Required tests**
- [ ] `tests/unit/test_product_service.py::test_normalize_material_trims_and_lowercases`
- [ ] `tests/unit/test_product_service.py::test_create_product_success`
- [ ] `tests/unit/test_product_service.py::test_create_product_duplicate_case_insensitive_raises` — AC-02
- [ ] `tests/unit/test_product_service.py::test_create_product_different_espesor_not_duplicate`
- [ ] `tests/unit/test_product_service.py::test_update_product_duplicate_against_other_product_raises` — AC-02 (edición)
- [ ] `tests/unit/test_product_service.py::test_update_product_no_false_positive_against_itself`
- [ ] `tests/unit/test_product_service.py::test_get_product_by_id_not_found_raises`
- [ ] `tests/integration/test_products_create.py::test_create_success_201` — AC-01
- [ ] `tests/integration/test_products_create.py::test_create_duplicate_400` — AC-02
- [ ] `tests/integration/test_products_create.py::test_create_missing_field_422` — AC-03
- [ ] `tests/integration/test_products_create.py::test_create_value_not_positive_422` — AC-04
- [ ] `tests/integration/test_products_create.py::test_create_rejects_stock_comprometido_422` — mitigación del threat model
- [ ] `tests/integration/test_products_create.py::test_create_initializes_stock_comprometido_zero` — AC-05
- [ ] `tests/integration/test_products_create.py::test_create_unauthenticated_401` — AC-09
- [ ] `tests/integration/test_products_list.py::test_list_returns_all_products` — AC-08
- [ ] `tests/integration/test_products_list.py::test_list_unauthenticated_401` — AC-09
- [ ] `tests/integration/test_products_get.py::test_get_by_id_success_200`
- [ ] `tests/integration/test_products_get.py::test_get_by_id_not_found_404`
- [ ] `tests/integration/test_products_update.py::test_update_success_200` — AC-06
- [ ] `tests/integration/test_products_update.py::test_update_duplicate_400` — AC-02
- [ ] `tests/integration/test_products_update.py::test_update_missing_field_422` — AC-03
- [ ] `tests/integration/test_products_update.py::test_update_value_not_positive_422` — AC-04
- [ ] `tests/integration/test_products_update.py::test_update_rejects_stock_comprometido_422` — AC-07, mitigación del threat model
- [ ] `tests/integration/test_products_update.py::test_update_not_found_404`
- [ ] `tests/integration/test_products_update.py::test_update_unauthenticated_401` — AC-09
- [ ] `tests/contract/test_products_contracts.py::test_product_out_shape_matches_schema`
- [ ] `tests/performance/test_products_performance.py::test_create_responds_under_2s` — NFR-01
- [ ] `tests/performance/test_products_performance.py::test_list_responds_under_2s` — NFR-01

**Completion criterion**
Los 4 endpoints funcionan de punta a punta vía `TestClient`; `stock_comprometido` nunca es
modificable desde el cliente (ni en create ni en update, verificado con un intento explícito de
enviarlo); el chequeo de duplicados es case-insensitive y aplica tanto a create como a update
(excluyendo el propio id).

---

## Block 2 — Frontend: modelos y servicio Angular de productos

**Files**
- `frontend/src/app/inventario/models/product.models.ts` (new) — `ProductCreate`, `ProductUpdate`,
  `ProductOut`
- `frontend/src/app/inventario/services/product.service.ts` (new)
- `frontend/src/app/inventario/services/product.service.spec.ts` (new)

**Logic**
`ProductService`: `list(): Observable<ProductOut[]>` (GET `products`), `getById(id: number): Observable<ProductOut>`
(GET `products/{id}`), `create(data: ProductCreate): Observable<ProductOut>` (POST `products`),
`update(id: number, data: ProductUpdate): Observable<ProductOut>` (PUT `products/{id}`) — mismo
patrón que `AuthService`: usa `environment.apiUrl` + `HttpClient` inyectado con `inject()`, no
atrapa errores (los propaga como error del `Observable` para que el componente decida el mensaje).
El `Authorization: Bearer` lo agrega `authInterceptor` globalmente (ya existente, sin lógica nueva
acá).

**Input validation**
N/A a nivel de servicio — la validación de formulario ocurre en los componentes del Block 3; el
servicio no valida nada, delega al backend.

**Error handling**
`ProductService` no atrapa errores de HTTP — los propaga como error del `Observable`.

**Required tests**
- [ ] `product.service.spec.ts::list obtiene el listado completo de productos`
- [ ] `product.service.spec.ts::getById obtiene un producto por id`
- [ ] `product.service.spec.ts::getById con 404 propaga el error`
- [ ] `product.service.spec.ts::create envía el body correcto y emite ProductOut`
- [ ] `product.service.spec.ts::create con 400 propaga el error`
- [ ] `product.service.spec.ts::update envía el body correcto y emite ProductOut`
- [ ] `product.service.spec.ts::update con 400 propaga el error`

**Completion criterion**
`ng test` pasa para `product.service.spec.ts`, cubriendo el camino exitoso y el de error de cada
método público.

---

## Block 3 — Frontend: páginas de listado, alta/edición y routing

**Files**
- `frontend/src/app/inventario/inventario.ts` / `.html` / `.scss` / `.spec.ts` (modified) —
  reemplaza el placeholder "módulo en construcción" por el listado real
- `frontend/src/app/inventario/product-form/product-form.ts` / `.html` / `.scss` / `.spec.ts` (new)
  — form reactivo compartido entre alta y edición
- `frontend/src/app/app.routes.ts` (modified) — agrega `inventario/nuevo` e
  `inventario/:id/editar` como hijas de la ruta protegida existente, sin `canActivate` propio
  (heredan el guard del padre — mismo patrón que `oficina`/`taller`/`configuracion`, verificado por
  el impact-scan y el arch-auditor)

**Logic**
`Inventario`: al iniciar llama a `productService.list()`, renderiza una tabla con material, espesor,
largo, ancho, stock, stock_comprometido y punto_pedido (AC-08); un botón "Nuevo producto" navega a
`/inventario/nuevo`; cada fila tiene un botón "Editar" que navega a `/inventario/{id}/editar`.
`ProductForm`: reactive form con los 6 campos editables (material, espesor, largo, ancho, stock,
punto_pedido). Lee el parámetro de ruta `id`: si está presente, es modo edición (llama a
`productService.getById` para precargar el form y muestra `stock_comprometido` como texto de solo
lectura, sin input — AC-07); si no está, es modo alta. Al enviar: llama a `create()` o `update()`
según el modo y navega a `/inventario` en éxito.

**Input validation**
Espejo de la validación del backend: `material` (`Validators.required`), `espesor`/`largo`/`ancho`
(`Validators.required`, valor > 0), `stock`/`punto_pedido` (`Validators.required`, entero > 0). El
botón de submit está deshabilitado mientras el form es inválido (AC-03, AC-04).

**Error handling**
`ProductForm`: error 400 (duplicado) → "Ya existe un producto con ese material, espesor y
dimensiones"; error 404 (edición de un producto que ya no existe) → mensaje y navega de vuelta a
`/inventario`; cualquier otro error → mensaje genérico de error.

**Required tests**
- [ ] `inventario.spec.ts::renderiza el listado de productos obtenido del servicio` — AC-08
- [ ] `inventario.spec.ts::muestra un botón para crear un nuevo producto`
- [ ] `inventario.spec.ts::cada producto del listado tiene un botón de edición`
- [ ] `product-form.spec.ts::modo alta — renderiza el formulario vacío con los 6 campos`
- [ ] `product-form.spec.ts::modo alta — el submit está deshabilitado con el form inválido` — AC-03/AC-04
- [ ] `product-form.spec.ts::modo alta — submit válido llama a ProductService.create y navega a /inventario` — AC-01
- [ ] `product-form.spec.ts::modo alta — muestra el mensaje de error en 400 (duplicado)` — AC-02
- [ ] `product-form.spec.ts::modo edición — precarga los valores del producto vía ProductService.getById`
- [ ] `product-form.spec.ts::modo edición — el campo stock_comprometido se muestra de solo lectura, sin input editable` — AC-07
- [ ] `product-form.spec.ts::modo edición — submit válido llama a ProductService.update y navega a /inventario` — AC-06
- [ ] `product-form.spec.ts::modo edición — producto no encontrado (404) muestra un mensaje y navega a /inventario`
- [ ] `product-form.spec.ts::muestra un mensaje genérico ante un error no esperado (ej. red)`
- [ ] `app.routes.spec.ts::inventario/nuevo e inventario/:id/editar están definidas como hijas de la ruta protegida, sin canActivate propio`

**Completion criterion**
`ng test` pasa; navegar a `/inventario` muestra el listado real (ya no el placeholder); crear un
producto lo agrega al listado; editar un producto persiste los cambios sin permitir tocar
`stock_comprometido`; intentar crear/editar hacia un duplicado muestra el error sin romper la
navegación.

---

## Final verification

Con los 3 bloques completos: un usuario autenticado puede crear un producto, verlo en el listado,
editarlo, y el sistema rechaza duplicados (mismo material case-insensitive + espesor + dimensiones)
tanto al crear como al editar. `stock_comprometido` queda en 0, protegido contra escritura del
cliente en ambos endpoints, listo para que el futuro módulo de Oficina lo use.
`docs/daw/security/threat-FEAT-002.md` cubre las mitigaciones de seguridad incorporadas.
