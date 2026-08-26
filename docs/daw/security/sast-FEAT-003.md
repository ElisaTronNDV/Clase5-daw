# SAST FEAT-003: Configuración del sistema (margen de tolerancia dimensional)

| Field | Value |
|-------|-------|
| Ticket | FEAT-003 |
| Date | 2026-08-26 |
| Scope | backend/app/models/configuracion.py, backend/app/schemas/configuracion.py, backend/app/services/configuracion_service.py, backend/app/api/routes/configuracion.py, backend/app/api/router.py, backend/app/models/__init__.py, frontend/src/app/configuracion/** (2 bloques completos) |

## Secretos (F-SAST-01)

- ✅ Sin secretos hardcodeados: grep de patrones `secret=`/`password=`/`api_key=`/`token=` con
  valores literales sobre todos los archivos nuevos/modificados de este ticket — 0 resultados.
- ✅ Sin configuración nueva de entorno (reutiliza `JWT_SECRET`/`DATABASE_URL` ya auditados).

## Inyección (F-SAST-02, F-SAST-03, F-SAST-05)

- ✅ SQL injection: `configuracion_service.py` usa exclusivamente `db.get(Configuracion, ...)` del
  ORM de SQLAlchemy, 0 queries por concatenación de strings.
- ✅ Command injection: sin `eval()`, `exec()`, `os.system()` ni `subprocess.*`.
- N/A Path traversal: este ticket no maneja rutas de archivo derivadas de input de usuario.

## XSS y funciones inseguras (F-SAST-06, F-SAST-04, F-SAST-17)

- ✅ Sin `[innerHTML]`, `bypassSecurityTrust*` ni `dangerouslySetInnerHTML` en
  `frontend/src/app/configuracion/` — binding por defecto de Angular.
- ✅ Sin deserialización insegura ni `eval`/`exec`.

## Criptografía (F-SAST-08)

- N/A — este ticket no introduce operaciones criptográficas nuevas.

## Debug / logging / uploads / CSRF (F-SAST-09, F-SAST-10, F-SAST-11, F-SAST-12)

- ✅ `DEBUG=False` sin cambios respecto a FEAT-001/002.
- ✅ Sin `print()`/`logging.*` en los archivos backend nuevos/modificados.
- N/A Unrestricted upload / CSRF: sin cambios respecto a los tickets anteriores.

## Validación de input y manejo de errores (F-SAST-14, F-SAST-15)

- ✅ `ConfiguracionUpdate.margen_tolerancia_dimensional` con `Field(gt=0)` — validación declarativa
  completa server-side.
- ✅ `model_config = ConfigDict(extra="forbid")` presente en `ConfiguracionUpdate`
  (`schemas/configuracion.py:8`) — un cliente que envíe un campo no reconocido recibe `422`.
  Verificado con test explícito (`test_update_rejects_extra_field_422`).
- ✅ **Mitigación crítica del threat model confirmada en código y en test**: `get_margen_tolerancia`/
  `update_margen_tolerancia` (`services/configuracion_service.py`) operan siempre sobre la clave fija
  `id=1`, nunca sobre "la primera fila por orden de inserción" — elimina la ambigüedad de
  concurrencia identificada en `docs/daw/security/threat-FEAT-003.md`. Verificado con
  `test_update_margen_tolerancia_updates_existing_row_without_duplicating`, que confirma una única
  fila con `id=1` tras múltiples updates.
- ✅ Manejo de errores sin fuga de información: sin excepciones de dominio nuevas (no aplica, no hay
  caso "no encontrado" en este módulo), sin traceback expuesto (`DEBUG=False`).

## Autenticación en ambos endpoints

- ✅ `GET` y `PUT /api/configuracion` (`routes/configuracion.py`) requieren
  `current_user: User = Depends(get_current_user)` — confirmado por lectura y por
  `test_get_unauthenticated_401`/`test_update_unauthenticated_401`.

## Dependencias (F-SAST-13, F-SAST-16)

Este ticket no agrega ninguna dependencia nueva (`git diff` sobre `backend/requirements.txt` y
`frontend/package.json` desde el commit del último SAST de FEAT-002: sin cambios).

**Backend / Frontend:** mismos hallazgos heredados que FEAT-001/FEAT-002, sin cambios en el código
que los afecta — ver suppressions en `docs/daw/security/sast-FEAT-002.md`.

| Paquete | Versión | CVE | Severidad | Disposición |
|---|---|---|---|---|
| `pytest` | 8.4.2 | PYSEC-2026-1845 | Low | Heredada, sin cambios (ver sast-FEAT-002.md) |
| `ecdsa` | 0.19.2 (transitiva) | PYSEC-2026-1325 | Medium | Heredada, sin cambios (ver sast-FEAT-002.md) |

Ambas suppressions siguen vigentes (`review by` 2027-02-24, dentro de los 6 meses — F-SAST-19 no
aplica todavía). No se re-documentan las 7 columnas completas acá para evitar duplicar el mismo
análisis tres veces; la evaluación original y su justificación viven en `sast-FEAT-001.md` y se
confirmaron sin cambios en `sast-FEAT-002.md`.

## Resumen

- Total: 14 checks limpios, 2 hallazgos heredados (0 Critical, 0 High, 1 Medium suprimido como
  falso positivo documentado, 1 Low aceptado como riesgo documentado — ninguno introducido ni
  afectado por este ticket)
- Result: **PASSED** — no hay Critical/High abiertos; la mitigación crítica del threat model
  (clave fija `id=1`) está confirmada en código y en test.
