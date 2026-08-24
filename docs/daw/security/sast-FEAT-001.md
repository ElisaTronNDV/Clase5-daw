# SAST FEAT-001: Autenticación y estructura base del proyecto

| Field | Value |
|-------|-------|
| Ticket | FEAT-001 |
| Date | 2026-08-24 |
| Scope | backend/app/**, backend/tests/**, frontend/src/app/** (4 bloques completos) |

## Secretos (F-SAST-01)

- ✅ Sin secretos hardcodeados: grep de patrones `SECRET=`/`PASSWORD=`/`API_KEY=`/`TOKEN=` con
  valores literales sobre `backend/app/` y `frontend/src/app/` — 0 resultados.
- ✅ `JWT_SECRET`/`DATABASE_URL` sin default en `core/config.py` (la app falla al arrancar si no
  están en el entorno).
- ✅ `.env` no está trackeado por git (`git ls-files | grep '\.env$'` — 0 resultados) y está en
  `.gitignore`.

## Inyección (F-SAST-02, F-SAST-03, F-SAST-05)

- ✅ SQL injection: 0 queries por concatenación de strings ni `.execute(f"...")`; todo el acceso a
  datos pasa por el query builder de SQLAlchemy (`db.query(User).filter(...)`).
- ✅ Command injection: sin `eval()`, `exec()`, `os.system()` ni `subprocess.*` en todo `backend/app/`.
- N/A Path traversal: este ticket no maneja rutas de archivo derivadas de input de usuario.

## XSS y funciones inseguras (F-SAST-06, F-SAST-04, F-SAST-17)

- ✅ Sin `[innerHTML]`, `bypassSecurityTrust*` ni `dangerouslySetInnerHTML` en `frontend/src/app/` —
  todo el binding de Angular pasa por su sanitización por defecto.
- ✅ Sin deserialización insegura ni uso de `eval`/`exec` en ningún archivo del ticket.

## Criptografía (F-SAST-08)

- ✅ Hash de contraseñas: bcrypt (passlib), costo 12 — no MD5/SHA1/DES/ECB en ningún archivo.
- ✅ JWT: HS256 con algoritmo fijado explícitamente en `decode_access_token` (mitigación del threat
  model), sin uso de ECDSA/RSA en el código propio.

## Debug / logging / uploads / CSRF (F-SAST-09, F-SAST-10, F-SAST-11, F-SAST-12)

- ✅ `DEBUG: bool = False` por defecto en `config.py` y en `.env.example`; `docs_url`/`redoc_url`
  deshabilitados cuando `DEBUG=False`.
- ✅ Sin `print()`/`logging.*` en `backend/app/` — no hay superficie de logueo de datos sensibles
  todavía.
- N/A Unrestricted upload: este ticket no expone endpoints de subida de archivos.
- N/A CSRF: la autenticación es 100% Bearer token (Authorization header), no hay cookies de sesión
  — el vector CSRF clásico no aplica a este diseño (ya evaluado en el threat model).

## Validación de input y manejo de errores (F-SAST-14, F-SAST-15)

- ✅ `email` validado con `EmailStr` (Pydantic), `password` con `Field(min_length=8)` en
  `UserCreate` — validación completa server-side en los dos únicos endpoints que reciben input de
  usuario no autenticado.
- ✅ Manejo de errores sin fuga de información: 401 genérico idéntico para email inexistente y
  password incorrecta (evita enumeración), sin traceback expuesto (`DEBUG=False`), excepciones de
  dominio tipadas (`EmailAlreadyRegisteredError`) en vez de `except` silenciosos.

## Dependencias (F-SAST-13, F-SAST-16)

**Backend (`pip-audit -r requirements.txt`):**

| Paquete | Versión | CVE | Severidad | Disposición |
|---|---|---|---|---|
| `pytest` | 8.4.2 | PYSEC-2026-1845 | Low | Ver Suppression 1 |
| `ecdsa` | 0.19.2 (transitiva, vía `python-jose[cryptography]`) | PYSEC-2026-1325 | Medium | Ver Suppression 2 |

**Frontend (`npm audit`, con y sin `--omit=dev`):** 0 vulnerabilidades encontradas.

### Suppression 1: PYSEC-2026-1845 (pytest)

| Field | Value |
|---|---|
| File | `backend/requirements.txt` (pytest>=8.0,<9.0) |
| Category | Local privilege/DoS vía nombre predecible de directorio `/tmp/pytest-of-{user}` en UNIX |
| Disposition | ACCEPTED_RISK |
| Reviewer | Maria Elisa (ma.elisa.tron@gmail.com) |
| Date | 2026-08-24 |
| Justification | `pytest` es una dependencia exclusiva de desarrollo/test, nunca se despliega a producción. El vector requiere otro usuario local no confiable en la misma máquina que corre la suite — no aplica al modelo de amenaza de este proyecto (entorno de desarrollo de un único usuario). |
| Compensating control | N/A (no se despliega); revisar el bump a `pytest>=9.0.3` en la próxima actualización de dependencias de rutina, sin urgencia. |
| Review by | 2027-02-24 |

### Suppression 2: PYSEC-2026-1325 (ecdsa — Minerva timing attack)

| Field | Value |
|---|---|
| File | `backend/requirements.txt` (`python-jose[cryptography]`, trae `ecdsa` como transitiva) |
| Category | Side-channel timing attack sobre firmas ECDSA en la curva P-256 (`ecdsa.SigningKey.sign_digest()`) |
| Disposition | FALSE_POSITIVE |
| Reviewer | Maria Elisa (ma.elisa.tron@gmail.com) |
| Date | 2026-08-24 |
| Justification | El código de este ticket usa exclusivamente HS256 (HMAC, no ECDSA) para firmar y validar JWT — `core/security.py` fija `algorithm="HS256"` en `create_access_token` y `algorithms=["HS256"]` en `decode_access_token` (mitigación #1 del threat model). La función vulnerable (`sign_digest` sobre curvas EC) nunca se invoca desde este código ni se selecciona ningún algoritmo ES256/ES384/etc. `python-ecdsa` no tiene fix planeado (fuera de alcance del proyecto upstream), pero la superficie vulnerable no es alcanzable con este uso. |
| Compensating control | El threat model (`docs/daw/security/threat-FEAT-001.md`) ya exige fijar el algoritmo explícitamente, lo cual además de mitigar "alg confusion" garantiza que el código ECDSA de esta dependencia nunca se ejecute. |
| Review by | 2027-02-24 (o antes, si algún ticket futuro introduce un algoritmo ES256/ES384/ES512) |

## Resumen

- Total: 20 checks limpios, 2 hallazgos (0 Critical, 0 High, 1 Medium suprimido como falso
  positivo documentado, 1 Low aceptado como riesgo documentado)
- Result: **PASSED** — no hay Critical/High abiertos; el único Medium está formalmente suprimido con
  las 7 columnas requeridas (F-SAST-18); el Low está documentado (no bloquea).
