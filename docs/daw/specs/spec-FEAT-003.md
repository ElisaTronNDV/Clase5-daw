# Spec FEAT-003: Configuración del sistema (margen de tolerancia dimensional)

| Field | Value |
|-------|-------|
| Ticket | FEAT-003 |
| PRD | docs/daw/prd/prd-FEAT-003.md |
| Tier | FEATURE |
| Date | 2026-08-26 |
| Spec loops | 0 |

## Summary

Se construye el apartado de Configuración: un único valor global (margen de tolerancia dimensional,
default 1.0 mm) con `GET`/`PUT` en el backend y una página real que reemplaza el placeholder de
Configuración en el frontend. La fila de configuración usa una clave fija (`id=1`, mitigación del
threat model) en vez de "la primera fila insertada", para que el upsert sea determinístico sin
agregar control de concurrencia. Se avanza en 2 bloques: backend → frontend (servicio Angular +
página), mismo patrón de bloques que FEAT-002 pero sin separar el servicio Angular de la página en
bloques distintos, dado el tamaño acotado de este módulo (1 campo, 2 endpoints).

## Coverage: PRD → blocks

| Requirement | Covered by |
|---|---|
| FR-01 (obtener valor actual) | Block 1, Block 2 |
| FR-02 (default 1.0 si no configurado, sin fila previa) | Block 1 |
| FR-03 (actualizar valor) | Block 1, Block 2 |
| FR-04 (rechazar valor no positivo) | Block 1, Block 2 |
| FR-05 (persistencia global, server-side) | Block 1 |
| FR-06 (requiere autenticación) | Block 1 |
| NFR-01 (<2s p95 obtener/actualizar) | Strategy: Block 1, tests de performance con assert de wall-clock; sin llamadas externas ni I/O costoso en el camino crítico (mismo patrón que FEAT-001/FEAT-002) |

## Dependencies between blocks

Block 1 (independiente) → Block 2 (necesita el contrato de API de Block 1 + `AuthService`/
`authGuard`/`authInterceptor` ya existentes de FEAT-001; la ruta `configuracion` ya existe protegida
por `authGuard`, confirmado por el impact scan — Block 2 no toca `app.routes.ts`).

---

## Block 1 — Backend: modelo, schema, servicio y endpoints de configuración

**Files**
- `backend/app/models/configuracion.py` (new) — modelo `Configuracion`
- `backend/app/models/__init__.py` (modified) — registrar `Configuracion` junto a `User`/`Product`
  (si no, `db/session.py:init_db()` nunca crea la tabla `configuracion` — mismo gap que el
  impact-scan detectó y cerró en FEAT-002)
- `backend/app/schemas/configuracion.py` (new) — `ConfiguracionOut`, `ConfiguracionUpdate`
- `backend/app/services/configuracion_service.py` (new) — módulo de funciones sueltas (no una
  clase — mismo patrón que `product_service.py`/`auth_service.py`, confirmado por el arch-auditor):
  `get_margen_tolerancia`, `update_margen_tolerancia`
- `backend/app/api/routes/configuracion.py` (new) — `GET /configuracion`, `PUT /configuracion`
- `backend/app/api/router.py` (modified) — incluye `configuracion_router` con prefix
  `/configuracion`
- `backend/tests/unit/test_configuracion_service.py`,
  `backend/tests/integration/test_configuracion_get.py`,
  `backend/tests/integration/test_configuracion_update.py`,
  `backend/tests/contract/test_configuracion_contracts.py`,
  `backend/tests/performance/test_configuracion_performance.py` (new)

**Logic**
`routes/configuracion.py` no accede a la DB ni implementa lógica de negocio (regla de AGENTS.md):
delega todo a `configuracion_service`, mismo patrón que `auth.py`/`products.py`.
`configuracion_service.py` garantiza que la tabla `configuracion` nunca tenga más de una fila
usando una **clave fija `id=1`** (mitigación del threat model,
`docs/daw/security/threat-FEAT-003.md`: sin esto, el upsert dependería de "buscar la primera fila
por orden de inserción", lo que abre una ventana de carrera entre dos `PUT` concurrentes — con
`id=1` fijo esa ambigüedad desaparece sin agregar ningún lock):
- `get_margen_tolerancia(db)`: `db.get(Configuracion, 1)`; si existe devuelve su valor, si no
  devuelve la constante `DEFAULT_MARGEN_TOLERANCIA = 1.0` **sin crear ninguna fila** (FR-02 — el
  valor por defecto no requiere seed en la base de datos).
- `update_margen_tolerancia(db, valor)`: `db.get(Configuracion, 1)`; si existe actualiza
  `margen_tolerancia_dimensional` y hace commit; si no, crea `Configuracion(id=1,
  margen_tolerancia_dimensional=valor)` y hace commit. Devuelve el valor final en ambos casos.

Riesgo residual documentado (no mitigado, aceptado): dos `PUT` concurrentes sobre una fila
inexistente podrían ambos intentar el `INSERT` con `id=1` — el segundo fallaría por PK duplicada.
Es el mismo tipo de riesgo de bajo impacto ya aceptado en `product_service.create_product` para el
chequeo de duplicados (confirmado por el arch-auditor); no se implementa retry ni locking porque el
PRD no lo exige y el tráfico esperado es de un único workspace interno.

**API contract**

`GET /api/configuracion`
- Response 200: `{"margen_tolerancia_dimensional": 1.0}`
- Errores: `401`
- Auth: Bearer JWT requerido (AC-06)

`PUT /api/configuracion`
- Request: `{"margen_tolerancia_dimensional": 2.5}`
- Response 200: `{"margen_tolerancia_dimensional": 2.5}`
- Errores: `422` (automático de Pydantic: valor ≤ 0 — AC-03; campo faltante o no numérico — AC-04;
  campo no reconocido — mitigación `extra="forbid"`) · `401`
- Auth: Bearer JWT requerido (AC-06)

**Data model**
- Entidad `Configuracion` (`backend/app/models/configuracion.py`):
  - `id`: `Integer`, primary key (siempre `1`, fijado por el service — ver "Logic")
  - `margen_tolerancia_dimensional`: `Float`, `nullable=False`
- Sin `UNIQUE` ni constraint de "una sola fila" a nivel de DB: el singleton lo garantiza el service
  mediante la clave fija `id=1` (mismo criterio que `Product` resuelve el chequeo de duplicados en
  el service en vez de con una constraint de DB).

**Input validation**
- `ConfiguracionUpdate`: `margen_tolerancia_dimensional: float = Field(gt=0)` — restricción
  declarativa en el propio schema, mismo patrón que `ProductCreate`/`UserCreate`.
- `model_config = ConfigDict(extra="forbid")` en `ConfiguracionUpdate` — mismo patrón de protección
  ya usado en `ProductCreate`/`ProductUpdate` (aunque acá no hay un campo "protegido" específico
  como `stock_comprometido`, previene que un cliente envíe cualquier campo no reconocido en el
  body).
- `ConfiguracionOut`: `model_config = ConfigDict(from_attributes=True)` (mismo patrón que
  `ProductOut`/`UserOut` — necesario para que `response_model` funcione sobre un objeto SQLAlchemy).

**Error handling**
- Validación de Pydantic (valor ≤ 0, campo faltante, no numérico, campo extra) → `422` automático
  de FastAPI.
- No hay excepciones de dominio nuevas: `get_margen_tolerancia` siempre devuelve un valor (persistido
  o default), `update_margen_tolerancia` siempre crea o actualiza — no existe un caso "no
  encontrado" que requiera un tipo de excepción como `ProductNotFoundError`.
- Excepción no controlada → sube sin interceptarse; `DEBUG=False` no expone traceback.

**Required tests**
- [ ] `tests/unit/test_configuracion_service.py::test_get_margen_tolerancia_returns_default_when_no_row` — AC-01
- [ ] `tests/unit/test_configuracion_service.py::test_get_margen_tolerancia_returns_persisted_value_when_row_exists`
- [ ] `tests/unit/test_configuracion_service.py::test_update_margen_tolerancia_creates_row_when_none_exists`
- [ ] `tests/unit/test_configuracion_service.py::test_update_margen_tolerancia_updates_existing_row_without_duplicating` — confirma clave fija `id=1`, nunca una segunda fila
- [ ] `tests/integration/test_configuracion_get.py::test_get_default_200` — AC-01
- [ ] `tests/integration/test_configuracion_get.py::test_get_unauthenticated_401` — AC-06
- [ ] `tests/integration/test_configuracion_update.py::test_update_success_200` — AC-02
- [ ] `tests/integration/test_configuracion_update.py::test_update_value_not_positive_422` — AC-03
- [ ] `tests/integration/test_configuracion_update.py::test_update_missing_field_422` — AC-04
- [ ] `tests/integration/test_configuracion_update.py::test_update_non_numeric_422` — AC-04
- [ ] `tests/integration/test_configuracion_update.py::test_update_rejects_extra_field_422` — mitigación `extra="forbid"`
- [ ] `tests/integration/test_configuracion_update.py::test_update_unauthenticated_401` — AC-06
- [ ] `tests/integration/test_configuracion_update.py::test_get_after_update_returns_last_saved_value` — AC-05
- [ ] `tests/contract/test_configuracion_contracts.py::test_configuracion_out_shape_matches_schema`
- [ ] `tests/performance/test_configuracion_performance.py::test_get_responds_under_2s` — NFR-01
- [ ] `tests/performance/test_configuracion_performance.py::test_update_responds_under_2s` — NFR-01

**Completion criterion**
`GET` sin configuración previa devuelve `1.0` sin crear ninguna fila; `PUT` con un valor válido
persiste con `id=1` fijo y un `GET` subsecuente refleja el nuevo valor; `PUT` con un valor ≤ 0, no
numérico, faltante o con un campo extra rechaza con `422` sin modificar el valor persistido; ambos
endpoints devuelven `401` sin autenticación.

---

## Block 2 — Frontend: servicio Angular y página de Configuración

**Files**
- `frontend/src/app/configuracion/models/configuracion.models.ts` (new) — `ConfiguracionOut`,
  `ConfiguracionUpdate`
- `frontend/src/app/configuracion/services/configuracion.service.ts` (new)
- `frontend/src/app/configuracion/services/configuracion.service.spec.ts` (new)
- `frontend/src/app/configuracion/configuracion.ts` / `.html` / `.spec.ts` (modified) — reemplaza el
  placeholder "módulo en construcción" por el formulario real

**Logic**
`ConfiguracionService`: `get(): Observable<ConfiguracionOut>` (GET `configuracion`),
`update(data: ConfiguracionUpdate): Observable<ConfiguracionOut>` (PUT `configuracion`) — mismo
patrón que `ProductService`: usa `environment.apiUrl` + `HttpClient` inyectado con `inject()`, no
atrapa errores (los propaga como error del `Observable`). El `Authorization: Bearer` lo agrega
`authInterceptor` globalmente (ya existente, sin lógica nueva acá).

`Configuracion`: reactive form con 1 campo (`margen_tolerancia_dimensional`). Al iniciar llama a
`configuracionService.get()` y precarga el form con el valor recibido (AC-01, AC-05). Al enviar
llama a `configuracionService.update()`: éxito → muestra un mensaje de confirmación; error `422` →
mensaje de validación; cualquier otro error (incl. red) → mensaje genérico. **No se toca
`app.routes.ts`**: la ruta `configuracion` ya existe como hija de la ruta protegida, heredando
`authGuard` (confirmado por el impact scan de PLAN).

**Input validation**
Espejo del backend: `margen_tolerancia_dimensional` con `Validators.required` + un validador local
`positiveNumber` **reimplementado en este archivo** (no extraído a `shared/`) — decisión consciente,
siguiendo el mismo precedente ya sentado por `product-form.ts` (confirmado por el arch-auditor:
AGENTS.md no exige una abstracción compartida sin que se pida; sería la segunda copia idéntica del
validador, y se documenta acá para que no se lea como un olvido en la revisión). El botón de submit
está deshabilitado mientras el form es inválido (AC-03, AC-04).

**Error handling**
`Configuracion`: error `422` → "El valor ingresado no es válido, debe ser un número mayor a 0";
cualquier otro error → mensaje genérico de error, sin perder el valor mostrado en el form.

**Required tests**
- [ ] `configuracion.service.spec.ts::get obtiene el valor actual de configuración`
- [ ] `configuracion.service.spec.ts::get con error propaga el error`
- [ ] `configuracion.service.spec.ts::update envía el body correcto y emite el valor actualizado`
- [ ] `configuracion.service.spec.ts::update con 422 propaga el error`
- [ ] `configuracion.spec.ts::precarga el valor obtenido del servicio al iniciar` — AC-01, AC-05
- [ ] `configuracion.spec.ts::el submit está deshabilitado con el campo vacío` — AC-04
- [ ] `configuracion.spec.ts::el submit está deshabilitado si el valor es ≤ 0` — AC-03
- [ ] `configuracion.spec.ts::submit válido llama a ConfiguracionService.update y muestra confirmación` — AC-02
- [ ] `configuracion.spec.ts::muestra un mensaje de error ante un 422 del servidor`
- [ ] `configuracion.spec.ts::muestra un mensaje genérico ante un error no esperado (ej. red)`

**Completion criterion**
`ng test` pasa; navegar a `/configuracion` muestra el valor actual (1.0 si nunca se configuró, o el
último guardado); guardar un valor inválido no persiste el cambio y muestra un mensaje de error;
guardar un valor válido lo persiste y queda reflejado al recargar la página.

---

## Final verification

Con los 2 bloques completos: un usuario autenticado puede ver el margen de tolerancia dimensional
(1.0 mm por defecto), modificarlo a un valor válido y verlo persistido; el sistema rechaza valores
inválidos (≤ 0, no numéricos, faltantes, o con campos extra) sin perder el valor anterior; todo el
módulo requiere autenticación. `docs/daw/security/threat-FEAT-003.md` cubre las mitigaciones de
seguridad incorporadas (clave fija `id=1` para el singleton).
