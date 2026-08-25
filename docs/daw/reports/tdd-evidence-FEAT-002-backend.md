# Evidencia TDD reconstruida — FEAT-002 (backend, Block 1)

**Contexto:** `daw-module-verifier` bloqueó el paso a RELEASE de FEAT-002 (ronda 1,
`docs/daw/reports/verify-FEAT-002.md`) porque ningún commit ni reporte documentaba qué test fallaba
(con qué assertion) antes de escribir el código, para ninguno de los 3 bloques — mismo gap (Regla
#-1 de `.daw/rules/testing.instructions.md`) que ya bloqueó a FEAT-001 en su primera ronda. Este
documento reconstruye esa evidencia de forma honesta **sobre el código ya existente y commiteado**
(commit `673c230`, Block 1): por cada unidad de lógica se rompió temporalmente la implementación de
la forma mínima necesaria para que el test fallara por la razón real (no por un error de
compilación/import ajeno), se corrió el test específico con `pytest -v`, se copió el output real de
la falla, se restauró el archivo con `git checkout --` y se confirmó el verde. No se escribió
código nuevo ni se cambió comportamiento: el código final es idéntico al que ya estaba commiteado.

**Entorno:** `backend/.venv/bin/python -m pytest`, ejecutado directo (reconstrucción de evidencia,
no gate de cierre del pipeline).

**Estado final:** árbol de trabajo de `backend/` limpio (`git status --porcelain -- backend/app`
sin salida) y suite completa en verde: `47 passed`.

## Alcance de la reconstrucción

El spec pide 28 tests para el Block 1 (7 unit + 15 integration/contract de create/get/list/update +
1 contract + 2 performance). Varios comparten exactamente el mismo mecanismo de validación (p. ej.
los tests de "campo obligatorio faltante" de create y de update dependen los dos de
`Field(min_length=1)`/`Field(...)` sin default; los de "valor ≤ 0" dependen los dos de
`Field(gt=0)`; los de "rechaza `stock_comprometido`" dependen los dos de `extra="forbid"`; los de
"401 sin autenticar" dependen los cuatro endpoints de la misma `Depends(get_current_user)"; los de
"404 not found" en `get`/`update` dependen del mismo `except ProductNotFoundError` mapeado a
`HTTPException(404, ...)`). Se reconstruyó en detalle **una unidad por cada mecanismo distinto**
(16 unidades) y se generaliza explícitamente el resto, como hizo el reporte de FEAT-001.

---

## Unidades reconstruidas

### `product_service.py::_normalize_material` (trim + lowercase)
**Test:** `tests/unit/test_product_service.py::test_normalize_material_trims_and_lowercases`
**Ruptura:** `_normalize_material` pasó a `return material` (sin `.strip().lower()`).
**Falla observada (rojo):**
```
>       assert product_service._normalize_material("  SAE_1010  ") == "sae_1010"
E       AssertionError: assert '  SAE_1010  ' == 'sae_1010'
E
E         - sae_1010
E         +   SAE_1010
tests/unit/test_product_service.py:36: AssertionError
1 failed, 1 warning in 5.00s
```
**Confirmado verde tras restaurar:** ✅ `1 passed, 1 warning in 0.41s`

### `product_service.py::_find_duplicate` (case-insensitive, AC-02)
**Test:** `tests/unit/test_product_service.py::test_create_product_duplicate_case_insensitive_raises`
**Ruptura:** en el loop de `_find_duplicate` se comparó `candidate.material == normalized_material`
(material crudo del candidato) en vez de `_normalize_material(candidate.material) ==
normalized_material`.
**Falla observada (rojo):**
```
    def test_create_product_duplicate_case_insensitive_raises(db):
        product_service.create_product(db, ProductCreate(**_payload(material="SAE_1010")))
>       with pytest.raises(ProductAlreadyExistsError):
E       Failed: DID NOT RAISE <class 'app.core.exceptions.ProductAlreadyExistsError'>
tests/unit/test_product_service.py:50: Failed
1 failed, 1 warning in 5.20s
```
**Confirmado verde tras restaurar:** ✅ `tests/unit/test_product_service.py` → `7 passed, 1 warning in 0.67s`

### `product_service.py::_find_duplicate` (exclude_id, no falso positivo contra sí mismo en update)
**Test:** `tests/unit/test_product_service.py::test_update_product_no_false_positive_against_itself`
**Ruptura:** se cambió `if exclude_id is not None:` por `if False:`, neutralizando el filtro
`Product.id != exclude_id`.
**Falla observada (rojo):** `update_product` levanta `ProductAlreadyExistsError` contra sí mismo, en
vez de aplicar el cambio pedido — prueba que el filtro de `exclude_id` es lo que sostiene el
comportamiento de "no falso positivo":
```
    def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
        product = get_product_by_id(db, product_id)
        if _find_duplicate(db, data, exclude_id=product_id) is not None:
>           raise ProductAlreadyExistsError(data.material)
E           app.core.exceptions.ProductAlreadyExistsError: SAE_1010
app/services/product_service.py:67: ProductAlreadyExistsError
1 failed, 1 warning in 5.69s
```
**Confirmado verde tras restaurar:** ✅ `tests/unit/test_product_service.py` → `7 passed, 1 warning in 0.68s`

### `product_service.py::get_product_by_id` (not found)
**Test:** `tests/unit/test_product_service.py::test_get_product_by_id_not_found_raises`
**Ruptura:** se eliminó `if product is None: raise ProductNotFoundError(product_id)`.
**Falla observada (rojo):**
```
    def test_get_product_by_id_not_found_raises(db):
>       with pytest.raises(ProductNotFoundError):
E       Failed: DID NOT RAISE <class 'app.core.exceptions.ProductNotFoundError'>
tests/unit/test_product_service.py:83: Failed
1 failed, 1 warning in 5.82s
```
**Confirmado verde tras restaurar:** ✅ `tests/unit/test_product_service.py` → `7 passed, 1 warning in 0.65s`

### `routes/products.py::create_product` (status code 201)
**Test:** `tests/integration/test_products_create.py::test_create_success_201`
**Ruptura:** `status_code=status.HTTP_201_CREATED` → `status.HTTP_200_OK`.
**Falla observada (rojo):**
```
E       assert 200 == 201
E        +  where 200 = <Response [200 OK]>.status_code
tests/integration/test_products_create.py:26: AssertionError
1 failed, 3 warnings in 10.22s
```
**Confirmado verde tras restaurar:** ✅ `1 passed, 3 warnings in 3.89s`

### `routes/products.py::create_product` (mapeo de `ProductAlreadyExistsError` a 400, AC-02)
**Test:** `tests/integration/test_products_create.py::test_create_duplicate_400`
**Ruptura:** se eliminó el `try/except ProductAlreadyExistsError` de la ruta (deja subir la
excepción cruda).
**Falla observada (rojo):** la excepción de dominio ya no se traduce a un 400 controlado y sube
como un 500 no manejado:
```
    def create_product(db: Session, data: ProductCreate) -> Product:
        if _find_duplicate(db, data) is not None:
>           raise ProductAlreadyExistsError(data.material)
E           app.core.exceptions.ProductAlreadyExistsError: sae_1010
app/services/product_service.py:46: ProductAlreadyExistsError
1 failed, 3 warnings in 12.34s
```
**Confirmado verde tras restaurar:** ✅ `tests/integration/test_products_create.py` → `7 passed, 8 warnings in 7.23s`

### `schemas/product.py::ProductCreate.material` (campo obligatorio, AC-03 — mecanismo compartido por los 7 tests de "campo faltante" de create/update)
**Test:** `tests/integration/test_products_create.py::test_create_missing_field_422`
**Ruptura:** `material: str = Field(min_length=1, max_length=255)` → `material: str | None = None`.
**Falla observada (rojo):** al no ser obligatorio, Pydantic deja pasar `material=None`, que llega
crudo al service y explota con un 500 no controlado en vez del 422 esperado por contrato:
```
        response = client.post("/api/products", json=payload, headers=headers)
...
E       AttributeError: 'NoneType' object has no attribute 'strip'
app/services/product_service.py:9: AttributeError
1 failed, 3 warnings in 12.06s
```
**Confirmado verde tras restaurar:** ✅ `tests/integration/test_products_create.py` → `7 passed, 8 warnings in 6.97s`

### `schemas/product.py::ProductCreate.espesor` (valor ≤ 0, AC-04 — mecanismo compartido por create/update, todos los campos numéricos)
**Test:** `tests/integration/test_products_create.py::test_create_value_not_positive_422`
**Ruptura:** `espesor: float = Field(gt=0)` → `espesor: float` (sin restricción).
**Falla observada (rojo):**
```
>       assert response.status_code == 422
E       assert 201 == 422
tests/integration/test_products_create.py:63: AssertionError
1 failed, 3 warnings in 10.64s
```
**Confirmado verde tras restaurar:** ✅ `tests/integration/test_products_create.py` → `7 passed, 8 warnings in 6.97s`

### `schemas/product.py::ProductCreate` (`extra="forbid"`, mitigación threat model — mecanismo compartido por create/update)
**Test:** `tests/integration/test_products_create.py::test_create_rejects_stock_comprometido_422`
**Ruptura:** `model_config = ConfigDict(extra="forbid")` → `ConfigDict(extra="ignore")`.
**Falla observada (rojo):** el campo extra `stock_comprometido` se ignora en silencio en vez de
rechazar la request:
```
>       assert response.status_code == 422
E       assert 201 == 422
tests/integration/test_products_create.py:75: AssertionError
1 failed, 3 warnings in 10.42s
```
**Confirmado verde tras restaurar:** ✅ `tests/integration/test_products_create.py` → `7 passed, 8 warnings in 6.93s`

### `product_service.py::create_product` (stock_comprometido hardcodeado en 0, AC-05)
**Test:** `tests/integration/test_products_create.py::test_create_initializes_stock_comprometido_zero`
**Ruptura:** `stock_comprometido=0` → `stock_comprometido=1` en la construcción del `Product`.
**Falla observada (rojo):**
```
>       assert response.json()["stock_comprometido"] == 0
E       assert 1 == 0
tests/integration/test_products_create.py:84: AssertionError
1 failed, 3 warnings in 10.25s
```
**Confirmado verde tras restaurar:** ✅ `tests/integration/test_products_create.py` → `7 passed, 8 warnings in 6.84s`

### `routes/products.py::create_product` (`Depends(get_current_user)`, AC-09 — mecanismo compartido por los 4 endpoints)
**Test:** `tests/integration/test_products_create.py::test_create_unauthenticated_401`
**Ruptura:** se eliminó el parámetro `current_user: User = Depends(get_current_user)` de la firma
de `create_product`.
**Falla observada (rojo):**
```
>       assert response.status_code == 401
E       assert 201 == 401
E        +  where 201 = <Response [201 Created]>.status_code
tests/integration/test_products_create.py:90: AssertionError
1 failed, 2 warnings in 9.42s
```
**Confirmado verde tras restaurar:** ✅ `tests/integration/test_products_create.py` → `7 passed, 8 warnings in 6.88s`

### `product_service.py::list_products` (AC-08)
**Test:** `tests/integration/test_products_list.py::test_list_returns_all_products`
**Ruptura:** `return db.query(Product).all()` → `return []`.
**Falla observada (rojo):**
```
>       assert len(body) == 2
E       assert 0 == 2
E        +  where 0 = len([])
tests/integration/test_products_list.py:30: AssertionError
1 failed, 3 warnings in 10.83s
```
**Confirmado verde tras restaurar:** ✅ `tests/integration/test_products_list.py` → `2 passed, 3 warnings in 3.64s`

### `routes/products.py::get_product` (mapeo de `ProductNotFoundError` a 404 — mecanismo compartido con `update_product`)
**Test:** `tests/integration/test_products_get.py::test_get_by_id_not_found_404`
**Ruptura:** se eliminó el `try/except ProductNotFoundError` de la ruta `GET /products/{id}`.
**Falla observada (rojo):** la excepción de dominio sube como 500 no controlado en vez del 404
esperado:
```
    def get_product_by_id(db: Session, product_id: int) -> Product:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product is None:
>           raise ProductNotFoundError(product_id)
E           app.core.exceptions.ProductNotFoundError: 9999
app/services/product_service.py:15: ProductNotFoundError
1 failed, 3 warnings in 10.45s
```
**Confirmado verde tras restaurar:** ✅ `tests/integration/test_products_get.py` → `2 passed, 4 warnings in 4.23s`

### `product_service.py::update_product` (persiste los cambios, AC-06)
**Test:** `tests/integration/test_products_update.py::test_update_success_200`
**Ruptura:** se comentó la línea `product.stock = data.stock` (el resto de campos sí se actualizan).
**Falla observada (rojo):**
```
>       assert response.json()["stock"] == 20
E       assert 10 == 20
tests/integration/test_products_update.py:33: AssertionError
1 failed, 3 warnings in 10.19s
```
**Confirmado verde tras restaurar:** ✅ `tests/integration/test_products_update.py` → `7 passed, 8 warnings in 7.00s`

### `schemas/product.py::ProductOut` (forma del contrato)
**Test:** `tests/contract/test_products_contracts.py::test_product_out_shape_matches_schema`
**Ruptura:** se eliminó el campo `stock_comprometido: int` de `ProductOut`.
**Falla observada (rojo):**
```
E       AssertionError: assert {'largo', 'id', 'stock', 'espesor', 'ancho', 'punto_pedido', 'material'} == {'largo', 'stock', 'espesor', 'ancho', 'punto_pedido', 'stock_comprometido', 'id', 'material'}
E
E         Extra items in the right set:
E         'stock_comprometido'
tests/contract/test_products_contracts.py:27: AssertionError
1 failed, 3 warnings in 9.04s
```
**Confirmado verde tras restaurar:** ✅ `tests/contract/test_products_contracts.py` → `1 passed, 3 warnings in 3.52s`

### `tests/performance/test_products_performance.py::test_create_responds_under_2s` (NFR-01)
**Cómo se validó que la assertion de wall-clock es real (no tautológica):** se insertó
temporalmente `time.sleep(2.5)` al inicio de `create_product`, sin tocar el test.
**Falla observada (rojo):**
```
E       assert 2.533853665998322 < 2.0
tests/performance/test_products_performance.py:32: AssertionError
1 failed, 3 warnings in 11.44s
```
**Confirmado verde tras restaurar:** ✅ `tests/performance/test_products_performance.py::test_create_responds_under_2s` → passed (ver suite completa al final)

### `tests/performance/test_products_performance.py::test_list_responds_under_2s` (NFR-01)
**Cómo se validó:** se insertó temporalmente `time.sleep(2.5)` al inicio de `list_products`, sin
tocar el test.
**Falla observada (rojo):**
```
E       assert 2.5118437229975825 < 2.0
tests/performance/test_products_performance.py:44: AssertionError
1 failed, 3 warnings in 11.41s
```
**Confirmado verde tras restaurar:** ✅ `tests/performance/test_products_performance.py::test_list_responds_under_2s` → passed (ver suite completa al final)

---

## Mecanismos generalizados (no reconstruidos individualmente, mismo patrón que la unidad cubierta)

- `test_create_product_success`, `test_create_product_different_espesor_not_duplicate`: mismo
  mecanismo de creación exitosa/no-duplicado ya ejercitado por las unidades de `_find_duplicate` y
  `create_product` de arriba.
- `test_update_product_duplicate_against_other_product_raises`: mismo mecanismo de
  `_find_duplicate`/`exclude_id` ya cubierto (con el signo opuesto) por
  `test_update_product_no_false_positive_against_itself`.
- `test_create_missing_field_422` cubre en detalle el mecanismo de campo obligatorio; los otros 6
  tests de "falta un campo" (uno por campo, en create y update) y el propio
  `test_update_missing_field_422` dependen exactamente de la misma anotación `Field(...)` sin
  default por campo — no se repitió la ruptura por cada campo.
- `test_create_value_not_positive_422` y `test_update_value_not_positive_422`: mismo mecanismo
  `Field(gt=0)`, aplicado a los 5 campos numéricos (`espesor`, `largo`, `ancho`, `stock`,
  `punto_pedido`) — se rompió uno (`espesor`) como representativo.
- `test_create_rejects_stock_comprometido_422` y `test_update_rejects_stock_comprometido_422` (AC-07):
  mismo mecanismo `extra="forbid"`, idéntico en `ProductCreate` y `ProductUpdate`.
- `test_list_unauthenticated_401`, `test_create_unauthenticated_401` (ya detallado),
  `test_update_unauthenticated_401`: misma `Depends(get_current_user)` en los 4 endpoints — se
  rompió una vez, representativo del mecanismo repetido.
- `test_get_by_id_success_200`: camino feliz simétrico al ya cubierto por
  `get_product_by_id_not_found_raises` (unit) y el mapeo 404 (integration).
- `test_update_duplicate_400`, `test_update_not_found_404`: mismos mecanismos de mapeo de excepción
  de dominio a HTTP ya cubiertos por `test_create_duplicate_400` y
  `test_get_by_id_not_found_404` respectivamente (la ruta `update_product` usa el mismo patrón
  `try/except` con los mismos dos `except`).

---

## Confirmación final de la suite completa (todas las unidades restauradas)

```
backend/.venv/bin/python -m pytest -q
47 passed, 30 warnings in 20.12s
```

Árbol de trabajo verificado limpio al cierre: `git status --porcelain -- backend/app` sin salida.
Cada ruptura se aplicó y restauró de forma aislada (una unidad a la vez, `git checkout --
<archivo>` inmediatamente después de capturar la falla), para que la evidencia de cada test sea
atribuible a una única causa.
