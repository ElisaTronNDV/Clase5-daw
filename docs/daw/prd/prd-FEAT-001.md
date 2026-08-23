# PRD FEAT-001: Autenticación y estructura base del proyecto

| Field | Value |
|-------|-------|
| Ticket | FEAT-001 |
| Tracker | none |
| Date | 2026-08-23 |
| PRD loops | 0 |

## Context and Problem

DyP LaserCore es un sistema nuevo que automatiza la captura de datos del archivo de corte para
generar códigos NEST, controlar stock de chapas y dar de alta recortes sobrantes (ver PRD-001
`docs/daw/prd/prd-001-captura-corte-inventario.md`). Antes de poder construir cualquiera de sus
módulos funcionales (Oficina, Taller, Inventario, Configuración) el proyecto necesita una base:
autenticación de usuarios y el esqueleto de backend/frontend sobre el que se van a montar los demás
tickets. Sin esta base, ningún otro módulo tiene dónde vivir ni cómo restringir el acceso.

Este ticket es el primero de cuatro en los que se divide la implementación de PRD-001, por módulo
funcional: FEAT-001 (este) → FEAT-002 (Inventario + Configuración) → FEAT-003 (Oficina) →
FEAT-004 (Taller).

## Goals

- Permitir que un usuario se registre y autentique con email y contraseña.
- Restringir el acceso a toda funcionalidad del sistema a usuarios autenticados.
- Dejar la estructura de carpetas de backend (FastAPI) y frontend (Angular) definida según
  `AGENTS.md` → "Architecture conventions", con el modelo `User` y los endpoints de auth como primer
  caso de uso real de esa estructura.
- Dejar el shell de navegación (layout + rutas protegidas) con las 4 páginas de módulo como
  placeholders, listas para que cada ticket siguiente implemente su contenido.

## Functional Requirements

- FR-01: El sistema debe mostrar una pantalla de login solicitando email y contraseña a todo usuario
  sin sesión activa que acceda a la URL del sistema.
- FR-02: El sistema debe redirigir a la pantalla de login a todo usuario no autenticado que intente
  acceder a cualquier ruta protegida.
- FR-03: El sistema debe permitir el registro de un nuevo usuario mediante una pantalla accesible sin
  sesión activa, solicitando email y contraseña.
- FR-04: El sistema debe rechazar el registro si el email ingresado ya pertenece a un usuario
  existente, informando el error al usuario.
- FR-05: El sistema debe rechazar el registro si la contraseña ingresada tiene menos de 8 caracteres,
  informando el error al usuario.
- FR-06: El sistema debe emitir un token JWT al autenticar exitosamente a un usuario, con una validez
  fija de 24 horas desde su emisión.
- FR-07: El sistema debe conceder acceso sin restricciones de rol o permiso a los 4 módulos (Oficina,
  Taller, Inventario, Configuración) a todo usuario autenticado.
- FR-08: El sistema debe presentar, para un usuario autenticado, una navegación con acceso a los 4
  módulos, mostrando en cada uno una página placeholder mientras su funcionalidad no esté
  implementada.
- FR-09: El sistema debe permitir a un usuario autenticado cerrar su sesión, invalidando el token en
  el cliente y redirigiéndolo a la pantalla de login. *(Asunción: no está explícito en PRD-001;
  se agrega por ser parte estándar de todo flujo de autenticación. Marcado aquí en lugar de asumirlo
  en silencio.)*

## Non-Functional Requirements

- NFR-01: Las contraseñas deben almacenarse con hash bcrypt (factor de costo ≥ 12), nunca en texto
  plano.
- NFR-02: El token JWT emitido debe expirar exactamente a las 24 horas de su emisión (simplificación
  documentada de RNF-05 del PRD-001: se implementa como expiración fija desde el login, no como
  expiración deslizante por inactividad — ver "Risks and Mitigations").
- NFR-03: El tiempo de respuesta de los endpoints de login y registro debe ser menor a 2 segundos
  (p95), consistente con RNF-03 del PRD-001.

## Acceptance Criteria

- AC-01 (FR-01): WHEN un usuario sin sesión activa accede a la URL del sistema, THE sistema SHALL
  mostrar la pantalla de login solicitando email y contraseña.
- AC-02 (FR-01): WHEN un usuario ingresa un email y contraseña que coinciden con una cuenta existente,
  THE sistema SHALL autenticarlo y redirigirlo a la pantalla principal.
- AC-03 (FR-01): IF el usuario ingresa credenciales incorrectas en el login, THEN THE sistema SHALL
  rechazar el acceso y mostrar un mensaje de error genérico, sin indicar si el email existe o si fue
  la contraseña la incorrecta.
- AC-04 (FR-02): IF un usuario no autenticado intenta acceder a cualquier ruta protegida del sistema,
  THEN THE sistema SHALL redirigirlo a la pantalla de login.
- AC-05 (FR-03): WHEN un usuario ingresa un email no registrado previamente junto con una contraseña
  válida en la pantalla de registro y confirma, THE sistema SHALL crear la cuenta exitosamente.
- AC-06 (FR-04): IF el email ingresado en el registro ya pertenece a un usuario existente, THEN THE
  sistema SHALL rechazar el alta e informar el error.
- AC-07 (FR-05): IF la contraseña ingresada en el registro tiene menos de 8 caracteres, THEN THE
  sistema SHALL rechazar el alta e informar el error.
- AC-08 (FR-06): WHEN un usuario se autentica exitosamente, THE sistema SHALL emitir un token JWT con
  una validez de 24 horas desde su emisión.
- AC-09 (FR-06): IF un usuario presenta un token JWT expirado o inválido al acceder a cualquier
  endpoint protegido, THEN THE sistema SHALL rechazar la petición con un error 401 y el frontend
  SHALL redirigir al usuario a la pantalla de login.
- AC-10 (FR-07): WHEN un usuario autenticado accede a cualquiera de los 4 módulos (Oficina, Taller,
  Inventario, Configuración), THE sistema SHALL conceder el acceso sin restricciones adicionales de
  rol o permiso.
- AC-11 (FR-08): WHEN un usuario autenticado navega a la ruta de un módulo aún no implementado, THE
  sistema SHALL mostrar una página placeholder indicando que el módulo está en construcción.
- AC-12 (FR-09): WHEN un usuario autenticado selecciona la opción de cerrar sesión, THE sistema SHALL
  invalidar el token en el cliente y redirigirlo a la pantalla de login.

## Out of Scope

- Recuperación / reseteo de contraseña ("forgot password") — no está contemplado en PRD-001 y queda
  fuera de este ticket.
- Roles y permisos diferenciados — explícitamente fuera de alcance por RF-19-a y por la sección
  "Fuera de Alcance" de PRD-001.
- Expiración de sesión deslizante por inactividad real — se implementa como expiración fija de 24h
  desde el login (NFR-02); una implementación fiel a "24h de inactividad" (reemisión de token en
  cada request) queda fuera de este ticket.
- Verificación de email al registrarse (confirmación por correo) — no solicitada, el registro queda
  activo inmediatamente tras el alta.
- Lógica de negocio de Oficina, Taller, Inventario y Configuración — cada módulo se implementa en su
  propio ticket (FEAT-002, FEAT-003, FEAT-004); en este ticket sus rutas son placeholders vacíos.
- Cookies httpOnly / protección CSRF — el JWT se maneja en el cliente vía localStorage (ver
  "Risks and Mitigations" sobre la exposición a XSS que esto implica).

## Risks and Mitigations

- Riesgo: un XSS en el frontend podría robar el JWT almacenado en localStorage → Mitigación: Angular
  sanitiza bindings por defecto (no usar `[innerHTML]` con contenido no confiable); se revisa en
  `daw-security-sast` durante CODE.
- Riesgo: la expiración fija de 24h (NFR-02) no refleja fielmente el requisito de "24h de inactividad"
  de RNF-05 del PRD-001 → Mitigación: decisión documentada y aceptada explícitamente en este PRD; si
  el negocio necesita expiración por inactividad real, es un ticket futuro sobre este mismo módulo.
- Riesgo: el registro público sin verificación de email permite que cualquiera con acceso a la URL
  cree una cuenta → Mitigación: aceptado para este alcance (sistema interno de la empresa, sin
  exposición pública prevista); no requiere mitigación adicional en este ticket.

## Dependencies

- Librerías declaradas en `AGENTS.md` → Stack: `passlib[bcrypt]` (hash de contraseñas),
  `python-jose` (JWT).
- Persistencia: SQLite vía SQLAlchemy ORM (modelo `User`).
- Ninguna dependencia de FEAT-002, FEAT-003 o FEAT-004 — este ticket es la base de la que los otros
  tres dependen.
