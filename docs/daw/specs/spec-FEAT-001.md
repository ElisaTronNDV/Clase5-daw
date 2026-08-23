# Spec FEAT-001: Autenticación y estructura base del proyecto

| Field | Value |
|-------|-------|
| Ticket | FEAT-001 |
| PRD | docs/daw/prd/prd-FEAT-001.md |
| Tier | FEATURE |
| Date | 2026-08-23 |
| Spec loops | 0 |

## Summary

Se construye el esqueleto del proyecto desde cero: backend FastAPI con el modelo `User` y los
endpoints de autenticación (registro, login, `/me`), y frontend Angular 22 con el flujo de
login/registro, un guard de rutas, un interceptor HTTP que adjunta el JWT, y un shell de navegación
con las 4 páginas de módulo como placeholders. La autenticación es JWT stateless (HS256, expiración
fija de 24h) guardado en `localStorage`. Se avanza en 4 bloques: DB+modelo → seguridad+endpoints →
servicios Angular → páginas+routing, cada uno construido sobre el anterior.

## Coverage: PRD → blocks

| Requirement | Covered by |
|---|---|
| FR-01 (pantalla de login) | Block 4 |
| FR-02 (redirigir no autenticados) | Block 3 (guard), Block 4 (routing con guard) |
| FR-03 (registro) | Block 2 (endpoint), Block 4 (página) |
| FR-04 (rechazar email duplicado) | Block 2 |
| FR-05 (rechazar password <8) | Block 2 |
| FR-06 (emitir JWT 24h) | Block 2 |
| FR-07 (acceso sin restricción a los 4 módulos) | Block 4 (routing), Block 2 (auth sin roles) |
| FR-08 (shell con placeholders) | Block 4 |
| FR-09 (logout) | Block 3 (servicio), Block 4 (botón en shell) |
| NFR-01 (hash bcrypt≥12) | Strategy: Block 2, `core/security.py` con `passlib[bcrypt]`, cost factor 12 |
| NFR-02 (JWT expira a las 24h exactas) | Strategy: Block 2, `JWT_EXPIRE_MINUTES=1440` fijo en `Settings`, sin lógica de sliding |
| NFR-03 (login/registro <2s p95) | Strategy: Block 2, tests de performance con assert de wall-clock; sin llamadas externas ni I/O costoso en el camino crítico |

Bloques sin FR directo (enablers técnicos, W-SPEC-01): `GET /health`, CORS, `.gitignore`, algoritmo
JWT fijado — necesarios para que el resto funcione de forma segura, justificados en el threat model
`docs/daw/security/threat-FEAT-001.md`.

## Dependencies between blocks

Block 1 (independiente) → Block 2 (necesita DB + modelo User) → Block 3 (necesita el contrato de API
de Block 2) → Block 4 (necesita `AuthService`/`AuthGuard`/`AuthInterceptor` de Block 3).

---

## Block 1 — Backend: scaffold, configuración, DB y modelo User

**Files**
- `backend/requirements.txt` (new) — fastapi, uvicorn, sqlalchemy, pydantic-settings, passlib[bcrypt], python-jose[cryptography], pytest, httpx
- `backend/.env.example` (new) — plantilla con `DATABASE_URL`, `JWT_SECRET` (con instrucción `# generar con: openssl rand -hex 32`), `JWT_EXPIRE_MINUTES=1440`, `PASSWORD_MIN_LENGTH=8`, `ALLOWED_ORIGINS=http://localhost:4200`, `DEBUG=false`
- `backend/app/__init__.py` (new)
- `backend/app/main.py` (new) — instancia FastAPI; `CORSMiddleware` con `allow_origins=settings.ALLOWED_ORIGINS` (nunca `*`); `docs_url`/`redoc_url` en `None` cuando `settings.DEBUG` es `False`; `GET /health` → `{"status": "ok"}`; evento de startup que llama a `init_db()`
- `backend/app/core/__init__.py` (new)
- `backend/app/core/config.py` (new) — `Settings(BaseSettings)`: `DATABASE_URL: str`, `JWT_SECRET: str`, `JWT_EXPIRE_MINUTES: int = 1440`, `PASSWORD_MIN_LENGTH: int = 8`, `ALLOWED_ORIGINS: list[str]`, `DEBUG: bool = False`. Sin valores por defecto para `JWT_SECRET`/`DATABASE_URL` en el código — se leen exclusivamente de `.env` (mitigación del threat model #2)
- `backend/app/db/__init__.py` (new)
- `backend/app/db/base.py` (new) — `Base = declarative_base()`
- `backend/app/db/session.py` (new) — `engine`, `SessionLocal`, `init_db()` (llama `Base.metadata.create_all(bind=engine)`; sin Alembic, es el primer schema de una base nueva)
- `backend/app/models/__init__.py` (new)
- `backend/app/models/user.py` (new) — modelo `User`
- `backend/tests/__init__.py`, `backend/tests/conftest.py` (new) — fixture de DB de test (SQLite en memoria) y `TestClient`
- `backend/tests/unit/__init__.py`, `backend/tests/integration/__init__.py`, `backend/tests/contract/__init__.py`, `backend/tests/performance/__init__.py` (new)
- `.gitignore` (modified, en la raíz del repo) — se agregan las entradas: `.env`, `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `*.db`, `*.sqlite3` (gap detectado por el impact-scan; Angular CLI genera su propio `frontend/.gitignore` con `node_modules/`/`dist/`/`.angular/` al scaffoldear en el Bloque 3, así que no hace falta duplicarlo acá)

**Logic**
Setup del proyecto backend. `init_db()` crea la tabla `users` al arrancar. `CORSMiddleware` y el
apagado condicional de `/docs` son las mitigaciones del threat model que corresponden a este bloque
(items 4 y 5 de "Mitigaciones obligatorias").

**API contract**

`GET /health`
- Request: sin parámetros
- Response 200: `{"status": "ok"}`
- Errores: ninguno (no depende de la DB ni de input)
- Auth: ninguna (público)

**Data model**
- Entidad `User` (`backend/app/models/user.py`):
  - `id`: `Integer`, primary key, autoincrement
  - `email`: `String(255)`, `unique=True`, `nullable=False`, `index=True`
  - `hashed_password`: `String(255)`, `nullable=False`
  - `created_at`: `DateTime`, `nullable=False`, `default=datetime.utcnow`

**Input validation**
N/A — este bloque no expone endpoints que reciban input de usuario (`/health` no toma parámetros).

**Error handling**
Fallo de conexión a la base de datos al iniciar → la app no levanta (fail-fast); es el comportamiento
por defecto de SQLAlchemy/uvicorn ante un `DATABASE_URL` inválido, sin lógica propia que agregar ni
testear — es un error de configuración de despliegue, no un caso de uso en runtime.

**Required tests**
- [ ] `tests/integration/test_health.py::test_health_returns_ok` — `GET /health` responde 200
  `{"status":"ok"}`
- [ ] `tests/unit/test_db_setup.py::test_users_table_created` — tras `init_db()`, `User.__table__` existe
  en los metadatos de SQLAlchemy con las columnas esperadas

**Completion criterion**
`uvicorn app.main:app` levanta sin error; `GET /health` devuelve 200; la tabla `users` existe tras el
startup; `git diff .gitignore` muestra las nuevas entradas.

---

## Block 2 — Backend: seguridad y endpoints de autenticación

**Files**
- `backend/app/core/security.py` (new) — `hash_password(password: str) -> str` (passlib, bcrypt, cost=12), `verify_password(plain: str, hashed: str) -> bool`, `create_access_token(subject: int) -> str` (jose, claims mínimos `{"sub": str(subject), "exp": ...}`, `algorithm="HS256"`, expira a `settings.JWT_EXPIRE_MINUTES`), `decode_access_token(token: str) -> dict` (jose, `algorithms=["HS256"]` fijado explícitamente — mitigación #1 del threat model — levanta `jose.JWTError` si es inválido/expirado)
- `backend/app/core/exceptions.py` (new) — `EmailAlreadyRegisteredError(Exception)`, `InvalidCredentialsError(Exception)` (excepciones tipadas de dominio, por convención de AGENTS.md)
- `backend/app/schemas/__init__.py` (new)
- `backend/app/schemas/user.py` (new) — `UserCreate(email: EmailStr, password: str = Field(min_length=8))`, `UserLogin(email: EmailStr, password: str)`, `UserOut(id: int, email: str)` (`model_config = ConfigDict(from_attributes=True)`, nunca incluye `hashed_password`), `Token(access_token: str, token_type: str = "bearer")`
- `backend/app/services/__init__.py` (new)
- `backend/app/services/auth_service.py` (new) — `get_user_by_email(db, email) -> User | None`, `get_user_by_id(db, user_id) -> User | None`, `register_user(db, data: UserCreate) -> User` (levanta `EmailAlreadyRegisteredError` si ya existe), `authenticate_user(db, email, password) -> User | None` (devuelve `None` si el email no existe o la password no matchea — mismo camino para ambos casos)
- `backend/app/api/__init__.py` (new)
- `backend/app/api/deps.py` (new) — `get_db()` (generador de sesión SQLAlchemy), `get_current_user(token, db) -> User` (extrae el Bearer token, llama a `security.decode_access_token`, resuelve el usuario vía `auth_service.get_user_by_id` — nunca consulta `models.User` directo, para no romper la separación de capas — levanta `HTTPException(401)` si el token es inválido/expirado o el usuario no existe)
- `backend/app/api/routes/__init__.py` (new)
- `backend/app/api/routes/auth.py` (new) — `POST /register`, `POST /login`, `GET /me`
- `backend/app/api/router.py` (new) — `api_router = APIRouter(prefix="/api")`, incluye `auth.router` con `prefix="/auth"`
- `backend/app/main.py` (modified) — incluye `api_router` (creado en Block 1)

**Logic**
Los routers no acceden a la DB ni implementan lógica de negocio directamente (regla de AGENTS.md):
delegan a `auth_service`, que a su vez usa `models.User` para el acceso a datos. `get_current_user`
sigue la misma regla — no toca `models.User` directo (corrección del arch-auditor).

**API contract**

`POST /api/auth/register`
- Request: `{"email": "user@dyp.com", "password": "secret123"}` (`email: EmailStr`, `password: str`, min 8 caracteres)
- Response 201: `{"id": 1, "email": "user@dyp.com"}`
- Errores: `400 {"detail": "email already registered"}` · `422` (automático de Pydantic) si el email no tiene formato válido o la password tiene menos de 8 caracteres
- Auth: ninguna (público)

`POST /api/auth/login`
- Request: `{"email": "user@dyp.com", "password": "secret123"}`
- Response 200: `{"access_token": "<jwt>", "token_type": "bearer"}`
- Errores: `401 {"detail": "invalid credentials"}` — mismo mensaje genérico si el email no existe o si la
  password no matchea (AC-03, evita distinguir el caso)
- Auth: ninguna (público)

`GET /api/auth/me`
- Headers: `Authorization: Bearer <token>`
- Response 200: `{"id": 1, "email": "user@dyp.com"}`
- Errores: `401 {"detail": "invalid or expired token"}` — token ausente, con firma inválida, con
  algoritmo distinto a HS256, o expirado
- Auth: Bearer JWT requerido

**Data model**
Ninguno nuevo (usa `User` de Block 1).

**Input validation**
`email` vía `EmailStr` de Pydantic (formato RFC 5322); `password` en `UserCreate` vía
`Field(min_length=8)`. `UserLogin` no exige longitud mínima (si no matchea ninguna cuenta real, el
resultado es igual el 401 genérico).

**Error handling**
- `EmailAlreadyRegisteredError` (service) → capturada en la ruta → `HTTPException(400, "email already registered")`
- `authenticate_user` devuelve `None` (email inexistente o password incorrecta) → la ruta levanta
  `HTTPException(401, "invalid credentials")`
- `jose.JWTError` en `get_current_user` (token ausente, inválido, algoritmo no permitido, o expirado)
  → `HTTPException(401, "invalid or expired token")`
- Excepción no controlada → sube sin interceptarse; con `DEBUG=False` (Block 1) FastAPI no expone el
  traceback en la respuesta

**Required tests**
- [ ] `tests/unit/test_security.py::test_hash_and_verify_password_roundtrip`
- [ ] `tests/unit/test_security.py::test_create_and_decode_token_roundtrip`
- [ ] `tests/unit/test_security.py::test_decode_expired_token_raises`
- [ ] `tests/unit/test_security.py::test_decode_token_wrong_algorithm_is_rejected` — valida la mitigación #1 del threat model
- [ ] `tests/integration/test_auth_register.py::test_register_success_201`
- [ ] `tests/integration/test_auth_register.py::test_register_duplicate_email_400` — AC-06
- [ ] `tests/integration/test_auth_register.py::test_register_password_too_short_422` — AC-07
- [ ] `tests/integration/test_auth_login.py::test_login_success_200_returns_token` — AC-08
- [ ] `tests/integration/test_auth_login.py::test_login_wrong_password_401_generic_message` — AC-03
- [ ] `tests/integration/test_auth_login.py::test_login_nonexistent_email_401_same_generic_message` — AC-03
- [ ] `tests/integration/test_auth_me.py::test_me_valid_token_200`
- [ ] `tests/integration/test_auth_me.py::test_me_missing_token_401` — AC-09
- [ ] `tests/integration/test_auth_me.py::test_me_expired_or_invalid_token_401` — AC-09
- [ ] `tests/contract/test_auth_contracts.py::test_register_response_never_includes_hashed_password`
- [ ] `tests/contract/test_auth_contracts.py::test_login_response_shape_matches_token_schema`
- [ ] `tests/performance/test_auth_performance.py::test_login_responds_under_2s` — NFR-03
- [ ] `tests/performance/test_auth_performance.py::test_register_responds_under_2s` — NFR-03

**Completion criterion**
Los 3 endpoints funcionan de punta a punta vía `TestClient`; `hashed_password` no aparece en ninguna
respuesta; un token firmado con un algoritmo distinto a HS256 es rechazado por `GET /me`.

---

## Block 3 — Frontend: scaffold Angular + servicios de autenticación

**Files**
- Scaffold: `ng new frontend --routing --style=scss --ssr=false` (genera el workspace Angular 22 completo, incluyendo `frontend/.gitignore` propio con `node_modules/`, `dist/`, `.angular/` — no se duplica en el `.gitignore` raíz)
- `frontend/src/environments/environment.ts`, `environment.development.ts` (new) — `apiUrl`
- `frontend/src/app/auth/models/auth.models.ts` (new) — `LoginRequest`, `RegisterRequest`, `TokenResponse`, `UserOut`
- `frontend/src/app/auth/services/auth.service.ts` (new)
- `frontend/src/app/auth/services/auth.service.spec.ts` (new)
- `frontend/src/app/auth/guards/auth.guard.ts` (new)
- `frontend/src/app/auth/guards/auth.guard.spec.ts` (new)
- `frontend/src/app/auth/interceptors/auth.interceptor.ts` (new)
- `frontend/src/app/auth/interceptors/auth.interceptor.spec.ts` (new)
- `frontend/src/app/app.config.ts` (modified) — `provideHttpClient(withInterceptors([authInterceptor]))`

**Logic**
- `AuthService`: `login(email, password): Observable<TokenResponse>` (POST a `auth/login`, guarda el
  token en `localStorage` bajo la key `dyp_lasercore_token` si la respuesta es exitosa);
  `register(email, password): Observable<UserOut>` (POST a `auth/register`, no toca `localStorage`,
  no hace auto-login); `logout(): void` (borra la key de `localStorage`); `getToken(): string | null`;
  `isAuthenticated(): boolean` (decodifica el payload del JWT — sin validar la firma, eso es
  responsabilidad exclusiva del backend — y compara el claim `exp` contra la hora actual).
- `authGuard` (functional `CanActivateFn`): si `authService.isAuthenticated()` es `true`, permite:
  si no, `router.navigate(['/login'])` y devuelve `false`.
- `authInterceptor` (functional `HttpInterceptorFn`): si hay token, clona el request agregando
  `Authorization: Bearer <token>`; en `catchError`, si el status es 401, llama a
  `authService.logout()` y navega a `/login`, y siempre relanza el error.

**Input validation**
N/A a nivel de servicio — la validación de formulario ocurre en los componentes del Block 4; el
servicio no valida nada, delega al backend.

**Error handling**
`AuthService` no atrapa errores de HTTP — los propaga como error del `Observable` para que el
componente decida el mensaje. `authInterceptor` solo actúa sobre 401 (logout + redirect); cualquier
otro status se relanza sin modificar.

**Required tests**
- [ ] `auth.service.spec.ts::login éxito guarda el token y emite TokenResponse`
- [ ] `auth.service.spec.ts::login con 401 no guarda token y propaga el error`
- [ ] `auth.service.spec.ts::register éxito emite UserOut sin tocar localStorage`
- [ ] `auth.service.spec.ts::register con 400 propaga el error`
- [ ] `auth.service.spec.ts::isAuthenticated true con token válido no expirado`
- [ ] `auth.service.spec.ts::isAuthenticated false sin token`
- [ ] `auth.service.spec.ts::isAuthenticated false con token expirado`
- [ ] `auth.service.spec.ts::logout limpia localStorage`
- [ ] `auth.guard.spec.ts::permite la navegación si isAuthenticated es true`
- [ ] `auth.guard.spec.ts::redirige a /login y bloquea si isAuthenticated es false`
- [ ] `auth.interceptor.spec.ts::agrega el header Authorization cuando hay token`
- [ ] `auth.interceptor.spec.ts::no agrega el header cuando no hay token`
- [ ] `auth.interceptor.spec.ts::en 401 llama logout y navega a /login`

**Completion criterion**
`ng test` pasa para los 3 spec files, cubriendo el camino exitoso y el de error de cada método
público.

---

## Block 4 — Frontend: páginas y routing

**Files**
- `frontend/src/app/auth/login/login.component.ts` / `.html` / `.scss` / `.spec.ts` (new)
- `frontend/src/app/auth/register/register.component.ts` / `.html` / `.scss` / `.spec.ts` (new)
- `frontend/src/app/shared/shell/shell.component.ts` / `.html` / `.scss` / `.spec.ts` (new) — navbar
  con los 4 módulos + botón de logout + `<router-outlet>`
- `frontend/src/app/home/home.component.ts` / `.html` / `.spec.ts` (new) — landing tras login, con
  links a los 4 módulos
- `frontend/src/app/oficina/oficina.component.ts` / `.html` / `.spec.ts` (new) — placeholder "Módulo en construcción"
- `frontend/src/app/taller/taller.component.ts` / `.html` / `.spec.ts` (new) — placeholder
- `frontend/src/app/inventario/inventario.component.ts` / `.html` / `.spec.ts` (new) — placeholder
- `frontend/src/app/configuracion/configuracion.component.ts` / `.html` / `.spec.ts` (new) — placeholder
- `frontend/src/app/app.routes.ts` (new) — `/login`, `/register` públicas; `/` (shell, `canActivate: [authGuard]`) con hijas `''→home`, `oficina`, `taller`, `inventario`, `configuracion`; `**` redirige a `/`
- `frontend/src/app/app.component.html` (modified) — solo `<router-outlet>`

**Logic**
`LoginComponent`/`RegisterComponent` usan reactive forms y llaman a `AuthService` — nunca a `HttpClient`
directo (regla de AGENTS.md). Tras login exitoso, navega a `/`. Tras registro exitoso, navega a
`/login` (no hace auto-login; decisión tomada en PLAN, no cambia ningún AC del PRD). `ShellComponent`
expone el botón de logout que llama a `authService.logout()` y navega a `/login`.

**Input validation**
`LoginComponent`: `email` (`Validators.required`, `Validators.email`), `password`
(`Validators.required`). `RegisterComponent`: `email` (`Validators.required`, `Validators.email`),
`password` (`Validators.required`, `Validators.minLength(8)`). El botón de submit está deshabilitado
mientras el form es inválido.

**Error handling**
`LoginComponent`: error 401 del `AuthService.login` → "Email o contraseña incorrectos"; cualquier otro
error → "No se pudo conectar con el servidor". `RegisterComponent`: error 400 → "Ese email ya está
registrado"; error 422 → "La contraseña debe tener al menos 8 caracteres"; cualquier otro error →
mensaje genérico de error.

**Required tests**
- [ ] `login.component.spec.ts::renderiza el formulario con los campos email y password` — AC-01
- [ ] `login.component.spec.ts::el submit está deshabilitado con el form inválido`
- [ ] `login.component.spec.ts::submit válido llama a AuthService.login y navega a / en éxito`
- [ ] `login.component.spec.ts::muestra el mensaje de error en 401`
- [ ] `login.component.spec.ts::muestra un mensaje genérico ante un error no esperado (ej. red)`
- [ ] `register.component.spec.ts::el submit está deshabilitado con el form inválido`
- [ ] `register.component.spec.ts::submit válido llama a AuthService.register y navega a /login en éxito`
- [ ] `register.component.spec.ts::muestra el mensaje de error en email duplicado (400)`
- [ ] `register.component.spec.ts::muestra el mensaje de error si la contraseña es muy corta (422)`
- [ ] `shell.component.spec.ts::muestra los 4 links de módulo`
- [ ] `shell.component.spec.ts::el botón de logout llama a AuthService.logout y navega a /login`
- [ ] `home.component.spec.ts::renderiza los links a los 4 módulos`
- [ ] `oficina.component.spec.ts::renderiza el mensaje "módulo en construcción"` — AC-11
- [ ] `taller.component.spec.ts::renderiza el mensaje "módulo en construcción"` — AC-11
- [ ] `inventario.component.spec.ts::renderiza el mensaje "módulo en construcción"` — AC-11
- [ ] `configuracion.component.spec.ts::renderiza el mensaje "módulo en construcción"` — AC-11
- [ ] `app.routes.spec.ts::las rutas oficina/taller/inventario/configuracion están definidas como hijas de la ruta protegida, sin ninguna restricción adicional entre ellas` — AC-10

**Completion criterion**
`ng test` pasa; navegar a `/oficina` sin sesión redirige a `/login` (AC-04); tras un login exitoso el
usuario ve el shell en `/` con los 4 links de módulo (AC-02); cada uno de los 4 módulos es accesible
sin restricción adicional una vez autenticado (AC-10) y muestra su placeholder (AC-11); el logout
limpia la sesión y vuelve a `/login` (AC-12).

---

## Final verification

Con los 4 bloques completos: un usuario nuevo puede registrarse, loguearse, ver el shell con los 4
módulos como placeholders, navegar entre ellos sin perder la sesión, y cerrar sesión — y ninguna ruta
protegida es accesible sin un JWT válido, ni del lado del cliente (guard) ni del servidor
(`get_current_user`, que es la validación real). `docs/daw/security/threat-FEAT-001.md` cubre las
mitigaciones de seguridad incorporadas; ver "Riesgos aceptados" ahí para lo que queda deliberadamente
fuera de este ticket (rate-limiting, enumeración de emails).
