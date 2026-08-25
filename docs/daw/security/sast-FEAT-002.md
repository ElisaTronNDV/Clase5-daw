# SAST FEAT-002: Gestión de inventario (CRUD de productos)

| Field | Value |
|-------|-------|
| Ticket | FEAT-002 |
| Date | 2026-08-25 |
| Scope | backend/app/models/product.py, backend/app/schemas/product.py, backend/app/services/product_service.py, backend/app/api/routes/products.py, backend/app/api/router.py, backend/app/core/exceptions.py, backend/app/models/__init__.py, frontend/src/app/inventario/** (3 bloques completos) |

## Secretos (F-SAST-01)

- ✅ Sin secretos hardcodeados: grep de patrones `secret=`/`password=`/`api_key=`/`token=` con
  valores literales sobre todos los archivos nuevos/modificados de este ticket — 0 resultados.
- ✅ No se agregó configuración nueva de entorno en este ticket (reutiliza `JWT_SECRET`/
  `DATABASE_URL` ya auditados en FEAT-001, sin cambios en `core/config.py` salvo lo ya cubierto).

## Inyección (F-SAST-02, F-SAST-03, F-SAST-05)

- ✅ SQL injection: `product_service.py` usa exclusivamente el query builder de SQLAlchemy
  (`db.query(Product).filter(...)`), 0 queries por concatenación de strings ni `.execute(f"...")`.
- ✅ Command injection: sin `eval()`, `exec()`, `os.system()` ni `subprocess.*` en ningún archivo
  nuevo del ticket.
- N/A Path traversal: este ticket no maneja rutas de archivo derivadas de input de usuario.

## XSS y funciones inseguras (F-SAST-06, F-SAST-04, F-SAST-17)

- ✅ Sin `[innerHTML]`, `bypassSecurityTrust*` ni `dangerouslySetInnerHTML` en
  `frontend/src/app/inventario/` — todo el binding (tabla de `Inventario`, texto de solo lectura
  de `stock_comprometido` en `ProductForm`) pasa por la sanitización por defecto de Angular.
- ✅ Sin deserialización insegura ni uso de `eval`/`exec` en ningún archivo del ticket.

## Criptografía (F-SAST-08)

- N/A — este ticket no introduce operaciones criptográficas nuevas (reutiliza JWT/bcrypt ya
  auditados en FEAT-001 vía `get_current_user`, sin tocar `core/security.py`).

## Debug / logging / uploads / CSRF (F-SAST-09, F-SAST-10, F-SAST-11, F-SAST-12)

- ✅ `DEBUG: bool = False` sin cambios respecto a FEAT-001 (`backend/app/core/config.py:23`) —
  ningún traceback expuesto por los endpoints nuevos.
- ✅ Sin `print()`/`logging.*` en ninguno de los archivos backend nuevos/modificados del ticket.
- N/A Unrestricted upload: este ticket no expone endpoints de subida de archivos.
- N/A CSRF: mismos endpoints Bearer-only que FEAT-001, sin cookies de sesión.

## Validación de input y manejo de errores (F-SAST-14, F-SAST-15)

- ✅ Los 6 campos de `ProductCreate`/`ProductUpdate` tienen validación declarativa completa
  (`Field(min_length=1, max_length=255)` en `material`, `Field(gt=0)` en el resto) —
  `backend/app/schemas/product.py`.
- ✅ **Mitigación obligatoria del threat model confirmada en código**:
  `model_config = ConfigDict(extra="forbid")` presente en AMBOS `ProductCreate`
  (`schemas/product.py:7`) y `ProductUpdate` (`schemas/product.py:20`) — un cliente que envíe
  `stock_comprometido` en el body recibe `422` en vez de setearlo, en `POST` y en `PUT` por igual.
  Verificado además con test explícito en ambos endpoints
  (`test_create_rejects_stock_comprometido_422`, `test_update_rejects_stock_comprometido_422`).
- ✅ Manejo de errores sin fuga de información: `ProductAlreadyExistsError` → `400` con mensaje de
  negocio fijo, `ProductNotFoundError` → `404` con mensaje fijo, ambos vía excepciones de dominio
  tipadas en `routes/products.py` (sin `except` silenciosos, sin traceback expuesto).

## Autenticación en los 4 endpoints (reutiliza F-TM-02 de FEAT-001)

- ✅ `POST`, `GET`, `GET/{id}`, `PUT` en `backend/app/api/routes/products.py` requieren
  `current_user: User = Depends(get_current_user)` — confirmado por lectura y por los tests
  `test_create/list/update_unauthenticated_401`.

## Dependencias (F-SAST-13, F-SAST-16)

Este ticket no agrega ninguna dependencia nueva (`git diff` sobre `backend/requirements.txt` y
`frontend/package.json` desde el inicio de la rama: sin cambios).

**Backend (`pip-audit -r requirements.txt`):** mismos 2 hallazgos que FEAT-001, sin cambios en el
código que los afecta.

| Paquete | Versión | CVE | Severidad | Disposición |
|---|---|---|---|---|
| `pytest` | 8.4.2 | PYSEC-2026-1845 | Low | Ver Suppression 1 (heredada de FEAT-001) |
| `ecdsa` | 0.19.2 (transitiva, vía `python-jose[cryptography]`) | PYSEC-2026-1325 | Medium | Ver Suppression 2 (heredada de FEAT-001) |

**Frontend (`npm audit`):** 0 vulnerabilidades encontradas.

### Suppression 1: PYSEC-2026-1845 (pytest) — heredada, sin cambios

| Field | Value |
|---|---|
| File | `backend/requirements.txt` (pytest>=8.0,<9.0) |
| Category | Local privilege/DoS vía nombre predecible de directorio `/tmp/pytest-of-{user}` en UNIX |
| Disposition | ACCEPTED_RISK |
| Reviewer | Maria Elisa (ma.elisa.tron@gmail.com) |
| Date | 2026-08-24 (evaluación original en `sast-FEAT-001.md`, sin cambios de código que la afecten) |
| Justification | `pytest` es una dependencia exclusiva de desarrollo/test, nunca se despliega a producción. Este ticket no introduce ningún cambio a cómo se ejecuta la suite. |
| Compensating control | N/A (no se despliega); revisar el bump a `pytest>=9.0.3` en la próxima actualización de dependencias de rutina. |
| Review by | 2027-02-24 (sin cambios, dentro de la ventana de 6 meses — F-SAST-19 no aplica todavía) |

### Suppression 2: PYSEC-2026-1325 (ecdsa — Minerva timing attack) — heredada, sin cambios

| Field | Value |
|---|---|
| File | `backend/requirements.txt` (`python-jose[cryptography]`, trae `ecdsa` como transitiva) |
| Category | Side-channel timing attack sobre firmas ECDSA en la curva P-256 |
| Disposition | FALSE_POSITIVE |
| Reviewer | Maria Elisa (ma.elisa.tron@gmail.com) |
| Date | 2026-08-24 (evaluación original en `sast-FEAT-001.md`, sin cambios de código que la afecten) |
| Justification | Este ticket no toca `core/security.py`; sigue usando exclusivamente HS256 (HMAC) para JWT, nunca ECDSA. La función vulnerable no es alcanzable desde ningún endpoint de `products`. |
| Compensating control | Mismo threat model de FEAT-001 sigue exigiendo el algoritmo fijo explícito. |
| Review by | 2027-02-24 (sin cambios) |

## Resumen

- Total: 16 checks limpios, 2 hallazgos heredados (0 Critical, 0 High, 1 Medium suprimido como
  falso positivo documentado, 1 Low aceptado como riesgo documentado — ninguno introducido ni
  afectado por este ticket)
- Result: **PASSED** — no hay Critical/High abiertos; las 2 suppressions heredadas siguen vigentes
  (dentro de los 6 meses, F-SAST-19 no aplica); la mitigación obligatoria del threat model
  (`extra="forbid"` en ambos schemas) está confirmada en código y en tests.

## Re-verificación — 2026-08-25 (cierre de CODE tras loop correctivo VERIFY→CODE)

El loop correctivo (falta de evidencia TDD + WARNs de AC-08/NFR-01, ver
`docs/daw/reports/verify-FEAT-002.md`) no modificó código de producción: `git diff e0780b9 --
backend/app frontend/src/app` da vacío. Lo único agregado fueron 2 tests
(`test_update_responds_under_2s` en backend, un test de columnas en `inventario.spec.ts`) y 3
reportes de documentación (`verify-FEAT-002.md`, `tdd-evidence-FEAT-002-backend.md`,
`tdd-evidence-FEAT-002-frontend.md`), verificados sin secretos ni datos sensibles (grep de
patrones de secreto/clave — 0 resultados).

- Suppression 1 y 2: sin cambios, `review by` 2027-02-24, dentro de los 6 meses (F-SAST-19 no
  aplica todavía).
- Result: **PASSED** (sin re-escaneo completo, por ausencia de diff en el código — el hallazgo
  previo sigue siendo la evaluación vigente).
