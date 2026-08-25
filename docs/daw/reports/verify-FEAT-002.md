# Verify FEAT-002: Gestión de inventario (CRUD de productos)

| Field | Value |
|-------|-------|
| Ticket | FEAT-002 |
| PRD | docs/daw/prd/prd-FEAT-002.md |
| Spec | docs/daw/specs/spec-FEAT-002.md |
| Tier | FEATURE |

## Ronda 1 — 2026-08-25

### Resultado: BLOCKED

Verificación de cierre end-to-end (no reutiliza las revisiones por bloque de CODE), ejecutada por
`daw-module-verifier` con lectura completa de PRD, spec, threat model, SAST y código de los 3
bloques, más ejecución propia de ambas suites.

### Trazabilidad PRD → Código → Tests

| AC / NFR | Resultado | Evidencia |
|---|---|---|
| AC-01 (crear + id secuencial) | ✅ PASS | `product_service.py:create_product` → `test_create_success_201`, `test_create_product_success` |
| AC-02 (rechazo duplicado, crear y editar, case-insensitive) | ✅ PASS | `_find_duplicate`/`_normalize_material` → `test_create_duplicate_400`, `test_update_duplicate_400`, tests unit correspondientes (mayúsculas/minúsculas y espacios mezclados, no tautológico) |
| AC-03 (campos obligatorios vacíos) | ✅ PASS | `Field(min_length=1)` → `test_create/update_missing_field_422` + `product-form.spec.ts` |
| AC-04 (valores ≤ 0) | ✅ PASS | `Field(gt=0)` → `test_create/update_value_not_positive_422` + test de `product-form.spec.ts` (agregado en corrección puntual de Block 3) |
| AC-05 (stock_comprometido=0 al crear) | ✅ PASS | `product_service.py` hardcodea 0, nunca de `data` → `test_create_initializes_stock_comprometido_zero` |
| AC-06 (editar persiste cambios) | ✅ PASS | `update_product` → `test_update_success_200` + test de modo edición en `product-form.spec.ts` |
| AC-07 (stock_comprometido solo lectura al editar) | ✅ PASS | `extra="forbid"` + ausencia del campo en `ProductUpdate`; HTML sin input/formControlName → `test_update_rejects_stock_comprometido_422` + test de frontend |
| AC-08 (listado completo, 7 columnas) | ⚠️ WARN | El test de `inventario.spec.ts` solo verifica que `material` aparece en el DOM, no las otras 6 columnas (el código sí las renderiza) — cobertura superficial en el punto exacto del AC |
| AC-09 (401 sin autenticar) | ✅ PASS | `Depends(get_current_user)` en los 4 endpoints → `test_create/list/update_unauthenticated_401` |
| NFR-01 (<2s p95 crear/editar/listar) | ⚠️ WARN | Solo hay test de performance para crear y listar; falta uno para editar/`PUT`, pese a que el propio NFR-01 nombra "crear, editar y listar" — gap heredado de la spec (Block 1 solo pidió 2 tests de performance) |

### Integración entre bloques

- ✅ Contrato `ProductOut`/`ProductCreate`/`ProductUpdate` idéntico entre backend
  (`schemas/product.py`) y frontend (`product.models.ts`), mismos nombres snake_case en ambos
  lados.
- ✅ `ProductService` apunta a `${environment.apiUrl}/products`, coincide con el prefix real del
  backend (`/api` + `/products`).
- ✅ `Inventario`/`ProductForm` solo consumen `ProductService`, nunca `HttpClient` directo.

### Flujo end-to-end (verificado por lectura de la cadena real)

- ✅ Crear → ver en listado → editar → rechazo de duplicados (case-insensitive, create y update,
  excluyendo el propio id) confirmado siguiendo la cadena completa de llamadas.

### Mitigación de seguridad crítica (`stock_comprometido`)

- ✅ Backend: ausente de ambos schemas de request, `extra="forbid"` en ambos → 422 si el cliente lo
  envía, verificado con tests explícitos.
- ✅ Frontend: sin `formControlName` para ese campo en ningún form; se muestra como texto plano en
  modo edición, nunca vía `getRawValue()`.

### Fuera de alcance respetado

- ✅ Ningún archivo de `oficina/`/`taller/` tocado por este ticket; `stock_comprometido` solo se
  inicializa en 0 y se protege, sin ningún flujo que lo modifique.

### Ejecución real de la suite (por el verificador, no reportada de terceros)

- ✅ Backend: `pytest -q` → 47/47 passed.
- ✅ Frontend: `ng test --watch=false` → 14/15 archivos, 48 tests; 1 timeout de worker en
  `auth.service.spec.ts` (síntoma de infraestructura conocido en este entorno WSL). Reintentado con
  el workaround documentado (`--include` pareado con un spec verde) → 2/2 archivos, 13/13 tests.
  Total real: 58/58 frontend, 105/105 combinado.

### Tareas del spec

- ✅ Block 1 (backend): 28/28 tests requeridos existen y pasan.
- ✅ Block 2 (ProductService Angular): 7/7 tests requeridos existen y pasan.
- ✅ Block 3 (páginas + routing): 13/13 tests requeridos existen y pasan (+1 test extra agregado
  para cerrar el gap de AC-04 detectado en la revisión de bloque).

### Evidencia TDD

- ❌ **FAIL bloqueante.** Ningún commit del ticket, ninguna entrada del `history` de
  `.daw-state.json`, ni ningún archivo en `docs/daw/reports/` documenta qué test fallaba (con qué
  assertion) antes de escribir el código correspondiente, para ninguno de los 3 bloques. Es el
  mismo gap (Regla #-1 de `.daw/rules/testing.instructions.md`) que ya bloqueó a FEAT-001 en su
  primera ronda de verificación y que se resolvió reconstruyendo la evidencia a mano
  (`docs/daw/reports/tdd-evidence-FEAT-001-backend.md` / `-frontend.md`). Para FEAT-002 no hay
  reconstrucción ni evidencia original: una suite en verde es indistinguible de tests escritos
  después del código.

### Calidad

- ✅ N/A Lint — sin linter configurado en el proyecto (consistente con AGENTS.md, no es una
  regresión de este ticket).
- ✅ Imports limpios, sin código muerto.
- ⚠️ Coverage — sin herramienta de cobertura instrumentada configurada en este ticket (ni
  `pytest-cov` ni `ng test --coverage`); cobertura de comportamiento alta por inspección, sin
  número verificable.

### Veredicto

```
Veredicto: BLOCKED
FAILs: 1 (evidencia TDD ausente) | WARNs: 3 (AC-08 superficial, NFR-01 incompleto, coverage sin instrumentar) | PASSes: 15
```

### Acción tomada

Corrective loop VERIFY → CODE: se reconstruirá evidencia TDD verificable para los 3 bloques (mismo
formato que FEAT-001), y se evaluará si los WARNs de AC-08/NFR-01 se corrigen en la misma vuelta o
quedan documentados como riesgo aceptado. Gates `tests` y `sast` se limpian — deben re-ganarse tras
la corrección.

## Ronda 2 — 2026-08-25

### Resultado: PASSED

Corrective loop aplicado (commit `2ee13f3`, sin diff en código de producción respecto a los 3
commits de bloque): se agregaron `docs/daw/reports/tdd-evidence-FEAT-002-backend.md` y
`-frontend.md` (16 + 13 unidades reconstruidas rojo→verde), `test_update_responds_under_2s`
(NFR-01) y el refuerzo del test de listado para las 7 columnas (AC-08).

Re-verificación de cierre completa (no incremental — se repitió toda la trazabilidad PRD → código →
tests, no solo los 3 gaps de la ronda 1):

- ✅ AC-01 a AC-09, NFR-01: los 10 criterios trazados a código y test real, no tautológico.
- ✅ **Gap 1 (evidencia TDD) cerrado**: ambos reportes leídos íntegros, coherentes con el código en
  disco (nombres de test, líneas y mensajes de error verificados contra los archivos fuente reales).
- ✅ **Gap 2 (AC-08) cerrado**: el test nuevo lee las celdas reales de la tabla y verifica los 7
  valores distintos, ya no solo `material`.
- ✅ **Gap 3 (NFR-01) cerrado**: `test_update_responds_under_2s` ejercita el camino completo de
  `PUT`, mide wall-clock real, no es un stub.
- ✅ Integración entre bloques, flujo end-to-end, mitigación de `stock_comprometido` en ambas capas:
  sin cambios respecto a la ronda 1, siguen sólidos.
- ✅ Fuera de alcance respetado (sin código de `oficina/`/`taller/` en ninguno de los 4 commits).
- ✅ Ejecución real de la suite por el verificador: backend 48/48, frontend 15/15 archivos y 59/59
  tests (con el mismo workaround documentado para el timeout de worker de Vitest en WSL).

```
Veredicto: PASSED
FAILs: 0 | WARNs: 1 (coverage sin instrumentar — sin herramienta configurada en el proyecto, mismo
criterio aceptado en ronda 1 y en FEAT-001, no bloqueante) | PASSes: 21
```

### Acción tomada

`gates.verify` = `true`. Pendiente de aprobación del usuario para transicionar a RELEASE.
