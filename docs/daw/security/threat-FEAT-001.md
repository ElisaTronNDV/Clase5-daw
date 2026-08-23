# Threat Model FEAT-001: Autenticación y estructura base del proyecto

| Field | Value |
|-------|-------|
| Ticket | FEAT-001 |
| Date | 2026-08-23 |
| Spec de referencia | docs/daw/specs/spec-FEAT-001.md (a escribirse tras este modelo) |
| PRD de referencia | docs/daw/prd/prd-FEAT-001.md |

## Componentes y superficies de ataque

| Componente | Superficie |
|---|---|
| `POST /api/auth/register` | Input de usuario, endpoint público (sin auth) |
| `POST /api/auth/login` | Input de usuario, endpoint público, emite credencial (JWT) |
| `GET /api/auth/me` | Endpoint protegido, valida JWT |
| JWT (emisión/validación) | Mecanismo de autenticación en sí |
| Tabla `users` (SQLite) | Almacena email (PII) + hash de contraseña (credencial) |
| `AuthService` + `localStorage` (Angular) | Guarda el JWT del lado del cliente |
| `AuthInterceptor` (Angular) | Adjunta el JWT a cada request saliente |
| `AuthGuard` (Angular) | Control de navegación client-side (no es un límite de seguridad real — la aplicación real ocurre server-side vía `get_current_user`) |
| Configuración (`JWT_SECRET`, `.env`) | Material secreto del que depende toda la autenticación |
| CORS (backend) | Determina qué orígenes del navegador pueden llamar a la API |

## Límites de confianza (F-TM-02)

1. **Navegador ↔ API backend** — distinto nivel de confianza (cliente no confiable → servidor). Toda petición HTTP cruza este límite.
2. **API backend ↔ base de datos SQLite** — mismo proceso/host en este alcance, pero se declara igual: es donde se decide si una query está parametrizada o no.
3. **Proceso backend ↔ entorno (`.env`)** — límite entre el código versionado y el material secreto que no debe versionarse.

## Análisis STRIDE por componente

### `POST /api/auth/register` y `POST /api/auth/login`

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Spoofing | Fuerza bruta / registro masivo abusivo (sin rate-limit) | Medium | Medium | 🟡 Ver "Riesgo aceptado #1" abajo |
| Tampering | Manipulación del body en tránsito | Low | Medium | HTTPS/TLS obligatorio en cualquier entorno más allá de localhost (requisito de despliegue, documentado en el spec) |
| Repudiation | Sin log de altas/logins | Low | Low | Fuera de alcance de este ticket; no se identifica necesidad de negocio para auditoría todavía |
| Information Disclosure | Enumeración de emails vía el mensaje "email ya registrado" (AC-06) | Medium | Low | 🟡 Ver "Riesgo aceptado #2" abajo |
| Denial of Service | Sin rate-limit, mismo riesgo que Spoofing arriba | Medium | Medium | 🟡 Ver "Riesgo aceptado #1" |
| Elevation of Privilege | N/A — no hay roles/permisos (RF-19-a) | — | — | — |

### `GET /api/auth/me` y validación de JWT (`get_current_user`)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Spoofing | Forjado de token si no se fija el algoritmo de firma ("alg confusion" / "alg:none") | Low | Critical | 🟠 **Mitigación obligatoria**: `jwt.decode(..., algorithms=["HS256"])` explícito — nunca confiar en el `alg` del header del token |
| Tampering | Modificación del payload | Low | High | Firma HMAC (python-jose) invalida cualquier alteración — ya cubierto por diseño |
| Repudiation | N/A | — | — | — |
| Information Disclosure | El payload del JWT es solo base64 (no cifrado), legible por cualquiera con el token | Low | Low | Mitigación: claims mínimos — solo `sub` (id de usuario) y `exp`, nunca password ni PII adicional |
| Denial of Service | N/A específico más allá de lo general | — | — | — |
| Elevation of Privilege | Token robado (vía XSS) = impersonación total hasta expirar (24h) | Low | High | Ya documentado y aceptado en el PRD (`Risks and Mitigations`, JWT en localStorage); mitigación de diseño: sanitización por defecto de Angular, no usar `[innerHTML]` con contenido no confiable |

### `JWT_SECRET` / gestión de secretos

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Spoofing / Tampering | Fuga del secreto → forja de tokens válidos para cualquier usuario (bypass total de auth) | Low | Critical | 🟠 **Mitigación obligatoria**: `JWT_SECRET` solo desde variable de entorno, sin default hardcodeado para producción; la app falla al arrancar si no está seteado fuera de un `.env` local de desarrollo claramente documentado como no-productivo; `.env` en `.gitignore` (ya incorporado al Bloque 1) |
| Information Disclosure | Secreto logueado por error | Low | High | Mitigación: nunca loguear el objeto `Settings` completo ni variables de entorno |

### Tabla `users` (SQLite)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Tampering | Inyección SQL | Low | Critical | SQLAlchemy ORM (queries parametrizadas), sin SQL crudo en el diseño |
| Information Disclosure | `hashed_password` expuesto en alguna respuesta | Low | High | `UserOut` (Pydantic `response_model`) excluye el campo explícitamente — ni siquiera si el service lo incluyera por error se serializaría |
| Information Disclosure | Email (PII) en reposo sin cifrado a nivel de archivo SQLite | Medium | Low | Mitigación: se delega al cifrado de disco a nivel de infraestructura/host (requisito de despliegue documentado), consistente con PII de baja sensibilidad (emails corporativos, no datos financieros/de salud); no se agrega una dependencia de cifrado de DB (ej. SQLCipher) en este ticket por no estar justificada en el PRD |

### CORS (backend ↔ frontend)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Tampering / Information Disclosure | `CORSMiddleware` con origen `*` permitiría que cualquier sitio llame a la API desde el navegador de un usuario autenticado | Low | Medium | 🟡 **Mitigación obligatoria**: allowlist explícita de orígenes vía `Settings.ALLOWED_ORIGINS` (nunca `*`); el uso de Bearer token (no cookies) ya limita el impacto real de CSRF, ya que el navegador no adjunta el header `Authorization` automáticamente en peticiones cross-site |

### Superficie general (Swagger, manejo de errores)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Information Disclosure | `/docs` (Swagger) expuesto en todo ambiente | Low | Low | Mitigación: `docs_url`/`redoc_url` deshabilitados cuando `Settings.DEBUG=False` (default `False`) |
| Information Disclosure | Stack traces expuestos en errores no controlados | Low | Medium | Mitigación: `debug=False` por defecto, handler global de excepciones que devuelve mensaje genérico sin traceback (F-SAST-15) |

## Clasificación de datos sensibles (F-TM-05)

| Dato | Clasificación | Cifrado en tránsito | Cifrado en reposo |
|---|---|---|---|
| Email | PII | HTTPS/TLS (requisito de despliegue) | Delegado a cifrado de disco a nivel host (ver tabla `users` arriba) |
| Contraseña (en tránsito, antes de hashear) | Credencial | HTTPS/TLS (requisito de despliegue) | N/A — nunca se persiste en texto plano |
| Hash de contraseña (bcrypt, costo≥12) | Credencial derivada | N/A | El hash unidireccional bcrypt ES el control de protección en reposo recomendado por OWASP para contraseñas — superior a un cifrado reversible, porque no puede deshacerse ni con acceso completo a la DB y la clave |
| JWT (token de sesión) | Credencial | HTTPS/TLS (requisito de despliegue) | No se persiste server-side (stateless); en el cliente vive en `localStorage`, riesgo ya aceptado en el PRD |

## Riesgos aceptados (F-TM-04)

### Riesgo aceptado #1: sin rate-limiting / bloqueo de cuenta en `/login` y `/register`

- **Quién lo acepta:** Maria Elisa (product owner del ticket, ma.elisa.tron@gmail.com), confirmado en esta conversación.
- **Justificación:** herramienta interna de la empresa con tráfico esperado bajo; bcrypt con costo≥12 ya introduce una demora significativa por intento que limita la tasa práctica de fuerza bruta. Agregar rate-limiting en este ticket expandiría su alcance sin un requisito del PRD que lo pida.
- **Condiciones de revisión:** revisar antes de exponer el sistema fuera de la red interna de la empresa, o en un plazo máximo de 6 meses desde esta fecha (2026-08-23 → revisar antes de 2027-02-23).

### Riesgo aceptado #2: enumeración de emails vía `/register` (AC-06)

- **Quién lo acepta:** ya aprobado como parte del PRD FEAT-001 (AC-06 exige informar explícitamente que el email ya está registrado); no requiere una segunda aprobación porque no es una decisión nueva de esta fase, es la ejecución de un criterio de aceptación ya validado.
- **Justificación:** es un requisito funcional explícito y deliberado del producto (RF-19/AC-28 del PRD-001 original); modificarlo requeriría reabrir DEFINE. Impacto bajo dado que es una herramienta interna sin superficie de registro público masivo.
- **Condiciones de revisión:** si en el futuro el registro se abre a un público más amplio o no confiable, reevaluar este trade-off como parte de ese ticket.

## Mitigaciones obligatorias a incorporar al spec

1. `jwt.decode(...)` fija `algorithms=["HS256"]` explícitamente (nunca confiar en el `alg` del token) — Bloque 2.
2. `JWT_SECRET` sin default hardcodeado válido para producción; documentado en `.env.example` cómo generarlo (`openssl rand -hex 32`) — Bloque 1/2.
3. Claims del JWT mínimos: solo `sub` y `exp` — Bloque 2.
4. `CORSMiddleware` con allowlist explícita vía `Settings.ALLOWED_ORIGINS`, nunca `*` — Bloque 1.
5. `docs_url`/`redoc_url` deshabilitados cuando `DEBUG=False` (default) — Bloque 1.
6. `debug=False` por defecto + handler global de excepciones sin traceback — Bloque 1/2.
7. Cifrado en reposo de la tabla `users` delegado a disco a nivel de infraestructura — documentar como prerequisito de despliegue (nota en el spec, no código).

## Resumen

- Riesgos: C:0 H:2 M:4 L:2
- Los 2 HIGH (forja de JWT por algoritmo no fijado, compromiso de `JWT_SECRET`) tienen mitigación concreta incorporada al spec.
- 2 riesgos MEDIUM quedan como riesgo aceptado formal (rate-limiting, enumeración de emails), con las 3 condiciones de F-TM-04 completas.
- Resultado: **PASSED** — todas las mitigaciones obligatorias se incorporan al spec antes de escribirlo a disco.
