# Evidencia TDD reconstruida — FEAT-001 (backend, Bloques 1 y 2)

**Contexto:** los commits `90948ee` (Block 1) y `b01079b` (Block 2) declararon "TDD rojo→verde" sin
registrar la evidencia real exigida por la Regla #-1 de `.daw/rules/testing.instructions.md`. Este
documento reconstruye esa evidencia de forma honesta: por cada unidad de lógica se rompió
temporalmente la implementación ya existente y commiteada, se corrió el/los test(s) relevante(s) con
`pytest -v` observando la falla real, se restauró el archivo con `git checkout --` y se confirmó el
verde. No se escribió código nuevo ni se cambió comportamiento: el código final es idéntico al que
ya estaba commiteado.

**Entorno:** `backend/.venv/bin/pytest`, ejecutado directo (reconstrucción de evidencia, no gate de
cierre del pipeline).

**Estado final:** árbol de trabajo de `backend/` limpio (`git status --porcelain -- backend/` sin
salida) y suite completa en verde: `19 passed`.

---

## Block 1 — DB + modelo User

### `backend/app/models/user.py`::`User` (columnas del modelo)
**Test(s):** `backend/tests/unit/test_db_setup.py::test_users_table_created`
**Cómo se rompió temporalmente:** se dejó solo la columna `id`, eliminando `email`,
`hashed_password` y `created_at` de la clase `User`.
**Falla observada (rojo):**
```
>       assert set(columns) == {"id", "email", "hashed_password", "created_at"}
E       AssertionError: assert {'id'} == {'created_at'...ssword', 'id'}
E
E         Extra items in the right set:
E         'email'
E         'created_at'
E         'hashed_password'
../../../../Desktop/Tp ia/Clase5/backend/tests/unit/test_db_setup.py:11: AssertionError
FAILED tests/unit/test_db_setup.py::test_users_table_created - AssertionError...
1 failed, 1 warning in 5.66s
```
**Confirmado verde tras restaurar:** ✅ `1 passed, 1 warning in 0.44s`

### `backend/app/main.py`::endpoint `/health`
**Test(s):** `backend/tests/integration/test_health.py::test_health_returns_ok`
**Cómo se rompió temporalmente:** el handler devolvía `{"status": "broken"}` en vez de
`{"status": "ok"}`.
**Falla observada (rojo):**
```
E       AssertionError: assert {'status': 'broken'} == {'status': 'ok'}
E
E         Differing items:
E         {'status': 'broken'} != {'status': 'ok'}
../../../../Desktop/Tp ia/Clase5/backend/tests/integration/test_health.py:5: AssertionError
FAILED tests/integration/test_health.py::test_health_returns_ok - AssertionEr...
1 failed, 2 warnings in 10.43s
```
**Confirmado verde tras restaurar:** ✅ `1 passed, 2 warnings in 3.49s`

---

## Block 2 — Seguridad + endpoints de autenticación

### `backend/app/core/security.py`::`hash_password` / `verify_password`
**Test(s):** `backend/tests/unit/test_security.py::test_hash_and_verify_password_roundtrip`
**Cómo se rompió temporalmente:** `verify_password` se reemplazó por `return True` incondicional.
**Falla observada (rojo):**
```
>       assert security.verify_password("wrong-password", hashed) is False
E       AssertionError: assert True is False
E        +  where True = <function verify_password at 0x7e23f9d02ac0>('wrong-password', '$2b$12$cWwk7IHkYZrfoh6fx.2T7eT7B7eCAUymOdPQ6Qv2itre4Eff4mXj.')
../../../../Desktop/Tp ia/Clase5/backend/tests/unit/test_security.py:16: AssertionError
FAILED tests/unit/test_security.py::test_hash_and_verify_password_roundtrip
1 failed, 2 warnings in 8.46s
```
**Confirmado verde tras restaurar:** ✅ `1 passed, 2 warnings in 3.41s`

### `backend/app/core/security.py`::`create_access_token` (claims mínimos)
**Test(s):** `backend/tests/unit/test_security.py::test_create_and_decode_token_roundtrip`
**Cómo se rompió temporalmente:** se agregó un claim extra (`"extra_claim": "leaked"`) al payload
del token, violando el contrato de "claims mínimos" (mitigación #3 del threat model).
**Falla observada (rojo):**
```
E       AssertionError: assert {'exp', 'extra_claim', 'sub'} == {'exp', 'sub'}
E
E         Extra items in the left set:
E         'extra_claim'
../../../../Desktop/Tp ia/Clase5/backend/tests/unit/test_security.py:26: AssertionError
FAILED tests/unit/test_security.py::test_create_and_decode_token_roundtrip - ...
1 failed, 2 warnings in 9.68s
```
**Confirmado verde tras restaurar:** ✅ `1 passed, 2 warnings in 2.49s`

### `backend/app/core/security.py`::`decode_access_token` (expiración)
**Test(s):** `backend/tests/unit/test_security.py::test_decode_expired_token_raises`
**Cómo se rompió temporalmente:** se agregó `options={"verify_exp": False}` a `jwt.decode`,
desactivando la validación de expiración.
**Falla observada (rojo):**
```
        with pytest.raises(JWTError):
>           security.decode_access_token(expired_token)
E       Failed: DID NOT RAISE <class 'jose.exceptions.JWTError'>
../../../../Desktop/Tp ia/Clase5/backend/tests/unit/test_security.py:39: Failed
FAILED tests/unit/test_security.py::test_decode_expired_token_raises - Failed...
1 failed, 2 warnings in 9.23s
```
**Confirmado verde tras restaurar:** ✅ `1 passed, 2 warnings in 2.30s`

### `backend/app/core/security.py`::`decode_access_token` (algoritmo fijo)
**Test(s):** `backend/tests/unit/test_security.py::test_decode_token_wrong_algorithm_is_rejected`
**Cómo se rompió temporalmente:** se agregó `"HS512"` a la lista `algorithms=[...]` de
`jwt.decode`, aceptando un algoritmo distinto al usado por `create_access_token` (violando la
mitigación #1 del threat model: nunca confiar en el `alg` que declara el propio token).
**Falla observada (rojo):**
```
        with pytest.raises(JWTError):
>           security.decode_access_token(token_signed_hs512)
E       Failed: DID NOT RAISE <class 'jose.exceptions.JWTError'>
../../../../Desktop/Tp ia/Clase5/backend/tests/unit/test_security.py:53: Failed
FAILED tests/unit/test_security.py::test_decode_token_wrong_algorithm_is_rejected
1 failed, 2 warnings in 10.13s
```
**Confirmado verde tras restaurar:** ✅ suite completa `test_security.py` → `4 passed, 2 warnings in 4.51s`

### `backend/app/services/auth_service.py`::`register_user` (email duplicado)
**Test(s):** `backend/tests/integration/test_auth_register.py::test_register_duplicate_email_400`
**Cómo se rompió temporalmente:** se eliminó el chequeo `if get_user_by_email(...) is not None:
raise EmailAlreadyRegisteredError(...)` previo a la creación del usuario.
**Falla observada (rojo):** el segundo `INSERT` con el mismo email ya no es interceptado a nivel de
aplicación y llega crudo a la base, rompiendo el constraint `UNIQUE` de SQLite (un 500 no controlado
en vez del 400 esperado por contrato):
```
E       sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: users.email
E       [SQL: INSERT INTO users (email, hashed_password, created_at) VALUES (?, ?, ?)]
E       [parameters: ('duplicado@dyp.com', '$2b$12$WVAKmZF1.ukDfz9PelhBb.TQhgXLTAN1VBSXf/K/gU9Tef3M498mW', '2026-08-24 23:11:16.141377')]
../../../../Desktop/Tp ia/Clase5/backend/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py:952: IntegrityError
FAILED tests/integration/test_auth_register.py::test_register_duplicate_email_400
1 failed, 4 warnings in 26.95s
```
**Confirmado verde tras restaurar:** ✅ `test_auth_register.py` → `3 passed, 4 warnings in 3.54s`

### `backend/app/schemas/user.py`::`UserCreate.password` (validación de longitud mínima)
**Test(s):** `backend/tests/integration/test_auth_register.py::test_register_password_too_short_422`
**Cómo se rompió temporalmente:** se quitó `Field(min_length=8)` del campo `password` de
`UserCreate`, dejándolo como `str` sin restricción.
**Falla observada (rojo):**
```
>       assert response.status_code == 422
E       assert 201 == 422
../../../../Desktop/Tp ia/Clase5/backend/tests/integration/test_auth_register.py:30: AssertionError
FAILED tests/integration/test_auth_register.py::test_register_password_too_short_422
1 failed, 3 warnings in 12.20s
```
**Confirmado verde tras restaurar:** ✅ `test_auth_register.py` → `3 passed, 4 warnings in 4.94s`

### `backend/app/services/auth_service.py`::`authenticate_user` (password incorrecta / email inexistente)
**Test(s):**
`backend/tests/integration/test_auth_login.py::test_login_wrong_password_401_generic_message`,
`backend/tests/integration/test_auth_login.py::test_login_nonexistent_email_401_same_generic_message`
**Cómo se rompió temporalmente:** `authenticate_user` se redujo a `return
get_user_by_email(db, email)`, eliminando el chequeo de `user is None` y la verificación de
password (`security.verify_password`).
**Falla observada (rojo):**
```
>       assert response.status_code == 401
E       assert 200 == 401
../../../../Desktop/Tp ia/Clase5/backend/tests/integration/test_auth_login.py:29: AssertionError
FAILED tests/integration/test_auth_login.py::test_login_wrong_password_401_generic_message

        assert response_nonexistent.status_code == 401
>       assert response_nonexistent.json() == response_wrong_password.json()
E       AssertionError: assert {'detail': 'i... credentials'} == {'access_toke...pe': 'bearer'}
../../../../Desktop/Tp ia/Clase5/backend/tests/integration/test_auth_login.py:41: AssertionError
FAILED tests/integration/test_auth_login.py::test_login_nonexistent_email_401_same_generic_message
2 failed, 1 passed, 5 warnings in 13.29s
```
(el tercer test, `test_login_success_200_returns_token`, siguió pasando porque no ejercita ninguna
de las dos ramas eliminadas — es el resultado esperado, no un falso verde.)
**Confirmado verde tras restaurar:** ✅ `test_auth_login.py` → `3 passed, 5 warnings in 7.07s`

### `backend/app/api/deps.py`::`get_current_user` (sin token → 401)
**Test(s):** `backend/tests/integration/test_auth_me.py::test_me_missing_token_401`
**Cómo se rompió temporalmente:** se eliminó el `if credentials is None: raise HTTPException(401,
...)` inicial, dejando que el flujo intente usar `credentials.credentials` directo.
**Falla observada (rojo):** falla con un error real (no controlado) en vez del 401 esperado por
contrato — confirma que la guarda explícita es la que sostiene el comportamiento:
```
    def get_current_user(...):
        try:
>           payload = security.decode_access_token(credentials.credentials)
E           AttributeError: 'NoneType' object has no attribute 'credentials'
app/api/deps.py:31: AttributeError
FAILED tests/integration/test_auth_me.py::test_me_missing_token_401 - Attribu...
1 failed, 2 warnings in 12.20s
```
**Confirmado verde tras restaurar:** ✅ `1 passed, 2 warnings in 3.80s`

### `backend/app/api/deps.py`::`get_current_user` (token expirado/inválido → 401)
**Test(s):** `backend/tests/integration/test_auth_me.py::test_me_expired_or_invalid_token_401`
**Cómo se rompió temporalmente:** en la rama `except (JWTError, KeyError, ValueError, TypeError)`
se reemplazó el `raise HTTPException(401, ...)` por la construcción de un `User` fantasma
(`User(id=0, email="ghost@example.com", ...)`) sin pasar por la base, simulando un bypass de
autenticación.
**Falla observada (rojo):**
```
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
>       assert response.status_code == 401
E       assert 200 == 401
../../../../Desktop/Tp ia/Clase5/backend/tests/integration/test_auth_me.py:48: AssertionError
FAILED tests/integration/test_auth_me.py::test_me_expired_or_invalid_token_401
1 failed, 2 warnings in 8.68s
```
**Confirmado verde tras restaurar:** ✅ `1 passed, 2 warnings in 3.80s` (verificado junto al test anterior)

### `backend/app/api/deps.py`::`get_current_user` (token válido → 200, usuario correcto)
**Test(s):** `backend/tests/integration/test_auth_me.py::test_me_valid_token_200`
**Cómo se rompió temporalmente:** se cambió `auth_service.get_user_by_id(db, user_id)` por
`auth_service.get_user_by_id(db, user_id + 1)` (off-by-one), para verificar que el lookup
efectivamente depende del `sub` del token y no de un ID hardcodeado o coincidente por casualidad.
**Falla observada (rojo):**
```
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
>       assert response.status_code == 200
E       assert 401 == 200
../../../../Desktop/Tp ia/Clase5/backend/tests/integration/test_auth_me.py:23: AssertionError
FAILED tests/integration/test_auth_me.py::test_me_valid_token_200 - assert 40...
1 failed, 3 warnings in 12.11s
```
**Confirmado verde tras restaurar:** ✅ `test_auth_me.py` (los 3 tests) → `3 passed, 3 warnings in 4.46s`

### `backend/app/schemas/user.py`::`UserOut` (nunca expone `hashed_password`)
**Test(s):**
`backend/tests/contract/test_auth_contracts.py::test_register_response_never_includes_hashed_password`
**Cómo se rompió temporalmente:** se agregó el campo `hashed_password: str` al schema `UserOut`.
**Falla observada (rojo):**
```
>       assert "hashed_password" not in response.json()
E       AssertionError: assert 'hashed_password' not in {'email': 'contract@dyp.com', 'hashed_password': '$2b$12$qP/mQqU7RBbsCfPfThT2sOYqvT4YhbW/H0jbAU1A9lLZhpOYUXPWy', 'id': 1}
../../../../Desktop/Tp ia/Clase5/backend/tests/contract/test_auth_contracts.py:8: AssertionError
FAILED tests/contract/test_auth_contracts.py::test_register_response_never_includes_hashed_password
1 failed, 3 warnings in 13.01s
```
**Confirmado verde tras restaurar:** ✅ `test_auth_contracts.py` → `2 passed, 4 warnings in 4.73s`

---

## Notas

- No se reconstruyó evidencia rojo→verde para `backend/tests/performance/test_auth_performance.py`
  (excluido explícitamente del pedido) ni de forma aislada para
  `test_login_response_shape_matches_token_schema` — ambos quedan cubiertos transitivamente por las
  unidades de arriba (contrato de `Token` y flujo de login), tal como habilitó el pedido original
  ("priorizá cobertura real sobre exhaustividad mecánica").
- Cada ruptura se aplicó y restauró de forma aislada (una unidad a la vez, `git checkout --
  <archivo>` inmediatamente después de capturar la falla) para que la evidencia de cada test sea
  atribuible a una única causa.
- Verificación final de integridad: `19 passed` en la suite completa (`backend/tests/`) y
  `git status --porcelain -- backend/` sin salida (árbol limpio, ningún archivo de `backend/app/`
  quedó modificado).
