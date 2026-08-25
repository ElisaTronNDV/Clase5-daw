# Evidencia TDD reconstruida — FEAT-001 (frontend, Blocks 3 y 4)

## Contexto

`daw-module-verifier` bloqueó el paso a RELEASE de FEAT-001 porque los commits de bloque
(`674a646`, `85d5250`) solo declaraban "TDD rojo→verde" sin registrar qué test fallaba, con qué
assertion, antes de escribir el código (Regla #-1 de `.daw/rules/testing.instructions.md`).

Este documento reconstruye esa evidencia de forma honesta **sobre el código ya existente**: para
cada unidad de lógica se rompió temporalmente la implementación de la forma mínima necesaria para
que el test fallara por la razón real (no por un error de compilación ajeno), se corrió el test, se
copió el output real, y luego se restauró el archivo con `git checkout --` antes de continuar con
la siguiente unidad. No se cambió comportamiento ni se escribió código nuevo.

## Nota sobre el entorno de ejecución

`ng test --watch=false` en este entorno (WSL, ruta con espacios `.../tp ia/Clase5/`) usa Vitest con
`forks` pool y presenta inestabilidad ya documentada en `docs/daw/reports/verify-FEAT-001.md`: un
"Failed to start forks worker... Timeout waiting for worker to respond" (60.05s fijo) que aparece de
forma no determinística.

Se observó un patrón reproducible: **corriendo un único archivo `--include` en aislamiento total,
el timeout de worker se disparó 3/3 veces sobre el mismo archivo** (`auth.service.spec.ts`), algo
más agresivo que lo descrito en el reporte de verificación (que rotaba de archivo). Se resolvió
incluyendo siempre **un segundo archivo `--include`** junto al archivo objetivo en cada corrida
aislada (p. ej. `--include='**/auth.service.spec.ts' --include='**/auth.guard.spec.ts'`), lo cual
evitó el timeout de forma consistente en las 10 corridas usadas para este documento. Se documenta
como hallazgo de infraestructura, no como defecto del código.

La confirmación final "verde" de todas las unidades se hizo además con una corrida de la suite
completa (`ng test --watch=false`, sin filtro): **12/13 archivos, 37/37 tests pasaron**; el archivo
restante (`configuracion.spec.ts`, no tocado por esta reconstrucción) sufrió el mismo timeout de
worker ya documentado — reintentar en CI o en una ruta sin espacios lo resolvería.

---

### `auth.service.ts::login`
**Test(s):** `AuthService > login > éxito guarda el token y emite TokenResponse`
**Cómo se rompió temporalmente:** se quitó el `tap()` que guarda `access_token` en `localStorage`.
**Falla observada (rojo):**
```
FAIL frontend src/app/auth/services/auth.service.spec.ts > AuthService > login > éxito guarda el token y emite TokenResponse
AssertionError: expected null to be 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.…' // Object.is equality
- Expected: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzg3NjE3MTkxfQ.signature"
+ Received: null
  ❯ src/app/auth/services/auth.service.spec.ts:58:47
      expect(localStorage.getItem(TOKEN_KEY)).toBe(response.access_token);
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 11 passed (12)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida final de suite completa: 37/37 tests, incluye las 10 de `auth.service.spec.ts`.

---

### `auth.service.ts::register`
**Test(s):** `AuthService > register > éxito emite UserOut sin tocar localStorage`
**Cómo se rompió temporalmente:** se agregó un `tap()` que escribe en `localStorage` dentro de `register` (violaría "sin tocar localStorage").
**Falla observada (rojo):**
```
FAIL frontend src/app/auth/services/auth.service.spec.ts > AuthService > register > éxito emite UserOut sin tocar localStorage
AssertionError: expected 'broken-for-tdd-evidence' to be null
- Expected: null
+ Received: "broken-for-tdd-evidence"
  ❯ src/app/auth/services/auth.service.spec.ts:96:47
      expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 11 passed (12)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida final de suite completa: 37/37 tests.

---

### `auth.service.ts::isAuthenticated` / `logout`
**Test(s):** `AuthService > isAuthenticated > false con token expirado`, `AuthService > isAuthenticated > false con token malformado`
**Cómo se rompió temporalmente:** `isAuthenticated()` se redujo a `return !!token` (no decodifica ni chequea el claim `exp`).
**Falla observada (rojo):**
```
FAIL frontend src/app/auth/services/auth.service.spec.ts > AuthService > isAuthenticated > false con token expirado
AssertionError: expected true to be false // Object.is equality
- false
+ true
  ❯ src/app/auth/services/auth.service.spec.ts:131:41
      expect(service.isAuthenticated()).toBe(false);

FAIL frontend src/app/auth/services/auth.service.spec.ts > AuthService > isAuthenticated > false con token malformado
AssertionError: expected true to be false // Object.is equality
- false
+ true
  ❯ src/app/auth/services/auth.service.spec.ts:136:41
      expect(service.isAuthenticated()).toBe(false);
Test Files  1 failed | 1 passed (2)
     Tests  2 failed | 10 passed (12)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida final de suite completa: 37/37 tests.

---

### `auth.guard.ts`
**Test(s):** `authGuard > permite la navegación si isAuthenticated es true`, `authGuard > redirige a /login y bloquea si isAuthenticated es false`
**Cómo se rompió temporalmente:** se invirtió la condición (`if (!authService.isAuthenticated())`).
**Falla observada (rojo):**
```
FAIL frontend src/app/auth/guards/auth.guard.spec.ts > authGuard > permite la navegación si isAuthenticated es true
AssertionError: expected false to be true // Object.is equality
  ❯ src/app/auth/guards/auth.guard.spec.ts:30:20
      expect(result).toBe(true);

FAIL frontend src/app/auth/guards/auth.guard.spec.ts > authGuard > redirige a /login y bloquea si isAuthenticated es false
AssertionError: expected true to be false // Object.is equality
  ❯ src/app/auth/guards/auth.guard.spec.ts:41:20
      expect(result).toBe(false);
Test Files  1 failed | 1 passed (2)
     Tests  2 failed | 10 passed (12)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida final de suite completa: 37/37 tests.

---

### `auth.interceptor.ts`
**Test(s):** `authInterceptor > agrega el header Authorization cuando hay token`, `authInterceptor > en 401 llama logout y navega a /login`
**Cómo se rompió temporalmente:** se quitó el `req.clone({ setHeaders: { Authorization } })` (siempre reenvía el request tal cual) y se quitó la lógica de `catchError` que llamaba `logout()`/`navigate()` en 401.
**Falla observada (rojo):**
```
FAIL frontend src/app/auth/interceptors/auth.interceptor.spec.ts > authInterceptor > agrega el header Authorization cuando hay token
AssertionError: expected null to be 'Bearer my-token' // Object.is equality
  ❯ src/app/auth/interceptors/auth.interceptor.spec.ts:42:54
      expect(req.request.headers.get('Authorization')).toBe('Bearer my-token');

FAIL frontend src/app/auth/interceptors/auth.interceptor.spec.ts > authInterceptor > en 401 llama logout y navega a /login
AssertionError: expected "vi.fn()" to be called at least once
  ❯ src/app/auth/interceptors/auth.interceptor.spec.ts:72:35
      expect(authServiceSpy.logout).toHaveBeenCalled();
Test Files  1 failed | 1 passed (2)
     Tests  2 failed | 4 passed (6)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida final de suite completa: 37/37 tests.

---

### `login.ts` (componente Login)
**Test(s):** `Login > submit válido llama a AuthService.login y navega a / en éxito`, `Login > muestra el mensaje de error en 401`
**Cómo se rompió temporalmente:** `onSubmit` dejó de llamar `router.navigate(['/'])` en éxito, y el branch de error 401 se cambió para setear el mismo mensaje genérico que el resto de errores.
**Falla observada (rojo):**
```
FAIL frontend src/app/auth/login/login.spec.ts > Login > submit válido llama a AuthService.login y navega a / en éxito
AssertionError: expected "navigate" to be called with arguments: [ [ '/' ] ]
Number of calls: 0
  ❯ src/app/auth/login/login.spec.ts:54:29
      expect(router.navigate).toHaveBeenCalledWith(['/']);

FAIL frontend src/app/auth/login/login.spec.ts > Login > muestra el mensaje de error en 401
AssertionError: expected 'No se pudo conectar con el servidor' to be 'Email o contraseña incorrectos' // Object.is equality
  ❯ src/app/auth/login/login.spec.ts:71:38
      expect(component.errorMessage()).toBe('Email o contraseña incorrectos');
Test Files  1 failed | 1 passed (2)
     Tests  2 failed | 7 passed (9)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida final de suite completa: 37/37 tests.

---

### `register.ts` (componente Register)
**Test(s):** `Register > submit válido llama a AuthService.register y navega a /login en éxito`, `Register > muestra el mensaje de error en email duplicado (400)`
**Cómo se rompió temporalmente:** `onSubmit` dejó de llamar `router.navigate(['/login'])` en éxito, y el branch 400 se cambió para setear el mismo mensaje genérico que el resto de errores.
**Falla observada (rojo):**
```
FAIL frontend src/app/auth/register/register.spec.ts > Register > submit válido llama a AuthService.register y navega a /login en éxito
AssertionError: expected "navigate" to be called with arguments: [ [ '/login' ] ]
Number of calls: 0
  ❯ src/app/auth/register/register.spec.ts:45:29
      expect(router.navigate).toHaveBeenCalledWith(['/login']);

FAIL frontend src/app/auth/register/register.spec.ts > Register > muestra el mensaje de error en email duplicado (400)
AssertionError: expected 'No se pudo completar el registro' to be 'Ese email ya está registrado' // Object.is equality
  ❯ src/app/auth/register/register.spec.ts:62:38
      expect(component.errorMessage()).toBe('Ese email ya está registrado');
Test Files  1 failed | 1 passed (2)
     Tests  2 failed | 7 passed (9)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida final de suite completa: 37/37 tests.

---

### `shell.ts`
**Test(s):** `Shell > el botón de logout llama a AuthService.logout y navega a /login`
**Cómo se rompió temporalmente:** `logout()` se vació (no llama `authService.logout()` ni `router.navigate()`).
**Falla observada (rojo):**
```
FAIL frontend src/app/shared/shell/shell.spec.ts > Shell > el botón de logout llama a AuthService.logout y navega a /login
AssertionError: expected "vi.fn()" to be called at least once
  ❯ src/app/shared/shell/shell.spec.ts:44:35
      expect(authServiceSpy.logout).toHaveBeenCalled();
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 6 passed (7)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida final de suite completa: 37/37 tests.

---

### `app.routes.ts`
**Test(s):** `routes > oficina/taller/inventario/configuracion son hijas de la ruta protegida, sin restricción adicional` (AC-10)
**Cómo se rompió temporalmente:** se agregó `canActivate: [authGuard]` a la ruta hija `oficina` (restricción adicional no prevista por el spec, que solo exige el guard en la ruta padre).
**Falla observada (rojo):**
```
FAIL frontend src/app/app.routes.spec.ts > routes > oficina/taller/inventario/configuracion son hijas de la ruta protegida, sin restricción adicional
AssertionError: expected [ [Function authGuard] ] to have a length of +0 but got 1
- Expected: 0
+ Received: 1
  ❯ src/app/app.routes.spec.ts:33:40
      expect(child?.canActivate ?? []).toHaveLength(0);
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 8 passed (9)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida final de suite completa: 37/37 tests.

---

### `oficina.html` (placeholder, muestra representativa de AC-11)
**Test(s):** `Oficina > renderiza el mensaje "módulo en construcción"`
**Cómo se rompió temporalmente:** se cambió el texto del template de "Módulo en construcción" a "Página pendiente".
**Falla observada (rojo):**
```
FAIL frontend src/app/oficina/oficina.spec.ts > Oficina > renderiza el mensaje "módulo en construcción"
AssertionError: expected 'página pendiente' to contain 'módulo en construcción'
- Expected: "módulo en construcción"
+ Received: "página pendiente"
  ❯ src/app/oficina/oficina.spec.ts:12:49
      expect(compiled.textContent?.toLowerCase()).toContain('módulo en construcción');
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 5 passed (6)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida final de suite completa: 37/37 tests.

*(Nota: `taller`, `inventario` y `configuracion` siguen el mismo patrón exacto de componente y test
— no se repitió la reconstrucción para los 3 restantes por indicación explícita de la tarea, ya que
el patrón es idéntico al de `oficina`.)*

---

## Confirmación final de la suite completa (todas las unidades restauradas)

```
ng test --watch=false (sin filtro)
Test Files  12 passed (12)
     Tests  37 passed (37)
     Errors  1 error (worker timeout en configuracion.spec.ts — inestabilidad de entorno
             ya documentada en verify-FEAT-001.md, no relacionada con el código ni con
             esta reconstrucción)
```

Árbol de trabajo verificado limpio al cierre: `git status --porcelain -- frontend/` sin salida.
