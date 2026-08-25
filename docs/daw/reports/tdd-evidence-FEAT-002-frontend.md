# Evidencia TDD reconstruida — FEAT-002 (frontend, Blocks 2 y 3)

## Contexto

`daw-module-verifier` bloqueó el paso a RELEASE de FEAT-002 (ronda 1,
`docs/daw/reports/verify-FEAT-002.md`) porque ningún commit ni reporte documentaba qué test fallaba
(con qué assertion) antes de escribir el código, para ninguno de los 3 bloques — mismo gap (Regla
#-1 de `.daw/rules/testing.instructions.md`) que ya bloqueó a FEAT-001. Este documento reconstruye
esa evidencia de forma honesta **sobre el código ya existente y commiteado** (commits `9769e10`
Block 2, `6fc1991` Block 3): para cada unidad de lógica se rompió temporalmente la implementación
de la forma mínima necesaria para que el test fallara por la razón real (no por un error de
compilación ajeno), se corrió el test, se copió el output real, y se restauró el archivo con
`git checkout --` antes de continuar con la siguiente unidad. No se cambió comportamiento ni se
escribió código nuevo.

## Nota sobre el entorno de ejecución

Mismo problema de infraestructura conocido en este entorno (WSL, ruta con espacios `.../tp ia/
Clase5/`) documentado en `docs/daw/reports/tdd-evidence-FEAT-001-frontend.md`: `ng test
--watch=false` sobre un único archivo `--include` en aislamiento total puede disparar un timeout de
worker de Vitest ("Failed to start forks worker..."). Se aplicó el mismo workaround: incluir siempre
un **segundo archivo `--include`** ya verde junto al archivo objetivo en cada corrida aislada (p.
ej. `--include='**/inventario.spec.ts' --include='**/product.service.spec.ts'`), lo cual evitó el
timeout en las ~13 corridas usadas para este documento.

La confirmación final "verde" de todas las unidades se hizo con una corrida conjunta de los 4
archivos de FEAT-002 (`inventario.spec.ts`, `product-form.spec.ts`, `product.service.spec.ts`,
`app.routes.spec.ts`): **4/4 archivos, 25/25 tests pasaron**.

## Alcance de la reconstrucción

El spec pide 7 tests para Block 2 (`product.service.spec.ts`) y 13 para Block 3
(`inventario.spec.ts`, `product-form.spec.ts`, `app.routes.spec.ts`). Varios comparten el mismo
mecanismo (p. ej. los dos tests de "submit deshabilitado" del form dependen del mismo binding
`[disabled]="form.invalid"`; los dos "submit válido navega" de alta y edición dependen de la misma
rama `next: () => this.router.navigate(...)`). Se reconstruyó en detalle **una unidad por cada
mecanismo distinto** (13 unidades) y se generaliza explícitamente el resto.

---

## Block 2 — `ProductService`

### `list()` — URL/endpoint correcto
**Test:** `product.service.spec.ts::list obtiene el listado completo de productos`
**Ruptura:** `` `${environment.apiUrl}/products` `` → `` `${environment.apiUrl}/product-list` ``.
**Falla observada (rojo):**
```
FAIL frontend src/app/inventario/services/product.service.spec.ts > ProductService > list > obtiene el listado completo de productos
Error: Expected one matching request for criteria "Match URL: http://localhost:8000/api/products", found none. Requests received are: GET http://localhost:8000/api/product-list.
❯ src/app/inventario/services/product.service.spec.ts:45:28
Test Files  1 failed | 1 passed (2)
     Tests  7 failed | 3 passed (10)
```
(los otros 6 fallos del archivo son un efecto cascada esperado: al no consumirse el `GET` mockeado,
`httpMock.verify()` del `afterEach` revienta y arrastra los tests siguientes del mismo `TestBed` —
no son fallas independientes, sino la consecuencia del mismo error raíz.)
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 10/10.

### `getById()` — propagación de error (404)
**Test:** `product.service.spec.ts::getById con 404 propaga el error`
**Ruptura:** se agregó `.pipe(catchError(() => of({} as ProductOut)))` a `getById`, absorbiendo
cualquier error HTTP en vez de propagarlo.
**Falla observada (rojo):**
```
FAIL frontend src/app/inventario/services/product.service.spec.ts > ProductService > getById > con 404 propaga el error
AssertionError: expected undefined to be truthy
❯ src/app/inventario/services/product.service.spec.ts:83:29
Uncaught Exception: Error: should not emit a value
❯ Object.next src/app/inventario/services/product.service.spec.ts:73:17
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 9 passed (10)
```
(el `Uncaught Exception` confirma que, con el error absorbido, el `next` sí llegó a emitir un valor
— exactamente lo que el test dice "no debería pasar".)
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 10/10.

### `create()` — body enviado sin campos extra
**Test:** `product.service.spec.ts::create envía el body correcto y emite ProductOut`
**Ruptura:** se agregó `stock_comprometido: 0` al body enviado por `create()`.
**Falla observada (rojo):**
```
FAIL frontend src/app/inventario/services/product.service.spec.ts > ProductService > create > envía el body correcto y emite ProductOut
AssertionError: expected { material: 'sae_1010', …(6) } to deeply equal { material: 'sae_1010', …(5) }
+   "stock_comprometido": 0,
❯ src/app/inventario/services/product.service.spec.ts:105:32
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 9 passed (10)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 10/10.

### `update()` — método HTTP correcto (PUT)
**Test:** `product.service.spec.ts::update envía el body correcto y emite ProductOut`
**Ruptura:** `this.http.put(...)` → `this.http.post(...)` en `update()`.
**Falla observada (rojo):**
```
FAIL frontend src/app/inventario/services/product.service.spec.ts > ProductService > update > envía el body correcto y emite ProductOut
AssertionError: expected 'POST' to be 'PUT' // Object.is equality
❯ src/app/inventario/services/product.service.spec.ts:158:34
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 9 passed (10)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 10/10.

---

## Block 3 — `Inventario` y `ProductForm`

### `Inventario.ngOnInit()` — renderiza el listado obtenido del servicio (AC-08)
**Tests:** `inventario.spec.ts::renderiza el listado de productos obtenido del servicio`,
`inventario.spec.ts::cada producto del listado tiene un botón de edición`
**Ruptura:** `this.productService.list().subscribe((products) => this.products.set(products))` →
`.subscribe(() => this.products.set([]))` (ignora la respuesta del servicio).
**Falla observada (rojo):**
```
FAIL frontend src/app/inventario/inventario.spec.ts > Inventario > renderiza el listado de productos obtenido del servicio
AssertionError: expected 'InventarioNuevo productoMaterialEspes…' to contain 'sae_1010'
❯ src/app/inventario/inventario.spec.ts:50:34

FAIL frontend src/app/inventario/inventario.spec.ts > Inventario > cada producto del listado tiene un botón de edición
AssertionError: expected null to be truthy
❯ src/app/inventario/inventario.spec.ts:68:70
Test Files  1 failed | 1 passed (2)
     Tests  2 failed | 8 passed (10)
```
(ambos tests dependen del mismo binding `@for (product of products(); ...)`: sin datos en la señal,
no hay filas — se rompió una sola vez, cubre los dos.)
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 10/10.

### `inventario.html` — botón "Nuevo producto" apunta a la ruta correcta
**Test:** `inventario.spec.ts::muestra un botón para crear un nuevo producto`
**Ruptura:** `routerLink="/inventario/nuevo"` → `routerLink="/inventario/crear"`.
**Falla observada (rojo):**
```
FAIL frontend src/app/inventario/inventario.spec.ts > Inventario > muestra un botón para crear un nuevo producto
AssertionError: expected null to be truthy
❯ src/app/inventario/inventario.spec.ts:60:18
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 9 passed (10)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 10/10.

### `product-form.html` — estructura del formulario (6 campos, AC-03/AC-04)
**Test:** `product-form.spec.ts::modo alta — renderiza el formulario vacío con los 6 campos`
**Ruptura:** `id="punto_pedido"` → `id="puntoPedido"` en el input correspondiente (se mantiene el
`formControlName` intacto para no romper la compilación por un control inexistente — la ruptura
apunta específicamente al selector que usa el test, no a la estructura del `FormGroup`).
**Falla observada (rojo):**
```
FAIL frontend src/app/inventario/product-form/product-form.spec.ts > ProductForm > modo alta > renderiza el formulario vacío con los 6 campos
AssertionError: expected null to be truthy
❯ src/app/inventario/product-form/product-form.spec.ts:78:55
      expect(compiled.querySelector('#punto_pedido')).toBeTruthy();
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 16 passed (17)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 17/17.

### `product-form.html` — submit deshabilitado con form inválido (AC-03/AC-04)
**Tests:** `product-form.spec.ts::modo alta — el submit está deshabilitado con el form inválido`,
`product-form.spec.ts::modo alta — el submit está deshabilitado si un campo numérico es ≤ 0`
**Ruptura:** `[disabled]="form.invalid"` → `[disabled]="false"`.
**Falla observada (rojo):**
```
FAIL frontend > ProductForm > modo alta > el submit está deshabilitado con el form inválido
AssertionError: expected false to be true // Object.is equality
❯ src/app/inventario/product-form/product-form.spec.ts:89:31

FAIL frontend > ProductForm > modo alta > modo alta — el submit está deshabilitado si un campo numérico es ≤ 0
AssertionError: expected false to be true // Object.is equality
❯ src/app/inventario/product-form/product-form.spec.ts:102:31
Test Files  1 failed | 1 passed (2)
     Tests  2 failed | 15 passed (17)
```
(ambos dependen del mismo binding; se rompió una sola vez, cubre los dos — AC-03 y AC-04.)
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 17/17.

### `ProductForm.onSubmit()` — navega a `/inventario` en éxito (alta y edición, AC-01/AC-06)
**Tests:** `product-form.spec.ts::modo alta — submit válido llama a ProductService.create y navega
a /inventario`, `product-form.spec.ts::modo edición — submit válido llama a ProductService.update y
navega a /inventario`
**Ruptura:** `next: () => this.router.navigate(['/inventario'])` → `next: () => {}`.
**Falla observada (rojo):**
```
FAIL frontend > ProductForm > modo alta > submit válido llama a ProductService.create y navega a /inventario
AssertionError: expected "navigate" to be called with arguments: [ [ '/inventario' ] ]
Number of calls: 0
❯ src/app/inventario/product-form/product-form.spec.ts:123:31

FAIL frontend > ProductForm > modo edición > submit válido llama a ProductService.update y navega a /inventario
AssertionError: expected "navigate" to be called with arguments: [ [ '/inventario' ] ]
Number of calls: 0
❯ src/app/inventario/product-form/product-form.spec.ts:213:31
Test Files  1 failed | 1 passed (2)
     Tests  2 failed | 15 passed (17)
```
(la llamada a `create`/`update` con el body correcto ya se verificaba antes de este assert y seguía
pasando — la ruptura aísla específicamente la navegación post-éxito, común a ambos modos.)
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 17/17.

### `ProductForm.onSubmit()` — mensaje de error en 400 (duplicado, AC-02)
**Test:** `product-form.spec.ts::muestra el mensaje de error en 400 (duplicado)`
**Ruptura:** en la rama `err.status === 400`, el mensaje se cambió al genérico ("No se pudo guardar
el producto") en vez del específico de duplicado.
**Falla observada (rojo):**
```
FAIL frontend > ProductForm > modo alta > muestra el mensaje de error en 400 (duplicado)
AssertionError: expected 'No se pudo guardar el producto' to be 'Ya existe un producto con ese materia…' // Object.is equality
❯ src/app/inventario/product-form/product-form.spec.ts:140:56
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 16 passed (17)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 17/17.

### `ProductForm.ngOnInit()` — precarga y solo-lectura de `stock_comprometido` en modo edición (AC-06/AC-07)
**Tests:** `product-form.spec.ts::modo edición — precarga los valores del producto vía
ProductService.getById`, `product-form.spec.ts::modo edición — el campo stock_comprometido se
muestra de solo lectura, sin input editable`
**Ruptura:** el `next` de `getById(...)` en `ngOnInit` se vació (`next: () => {}`), sin
`patchValue` ni `stockComprometido.set(...)`.
**Falla observada (rojo):**
```
FAIL frontend > ProductForm > modo edición > precarga los valores del producto vía ProductService.getById
AssertionError: expected '' to be 'sae_1010' // Object.is equality
❯ src/app/inventario/product-form/product-form.spec.ts:180:61

FAIL frontend > ProductForm > modo edición > el campo stock_comprometido se muestra de solo lectura, sin input editable
AssertionError: expected 'Editar productoMaterialEspesorLargoAn…' to contain '3'
❯ src/app/inventario/product-form/product-form.spec.ts:192:36
Test Files  1 failed | 1 passed (2)
     Tests  2 failed | 15 passed (17)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 17/17.

### `ProductForm.ngOnInit()` — producto no encontrado (404) en modo edición navega
**Test:** `product-form.spec.ts::modo edición — producto no encontrado (404) muestra un mensaje y
navega a /inventario`
**Ruptura:** el `error` de `getById(...)` se redujo a `() => { this.errorMessage.set('No se pudo
cargar el producto'); }`, sin distinguir 404 ni navegar.
**Falla observada (rojo):**
```
FAIL frontend > ProductForm > modo edición > producto no encontrado (404) muestra un mensaje y navega a /inventario
AssertionError: expected "navigate" to be called with arguments: [ [ '/inventario' ] ]
Number of calls: 0
❯ src/app/inventario/product-form/product-form.spec.ts:225:31
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 16 passed (17)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 17/17.

### `app.routes.ts` — rutas de `ProductForm` sin `canActivate` propio (heredan el guard del padre)
**Test:** `app.routes.spec.ts::inventario/nuevo e inventario/:id/editar están definidas como hijas
de la ruta protegida, sin canActivate propio`
**Ruptura:** se agregó `canActivate: [authGuard]` a la ruta hija `inventario/nuevo` (restricción
adicional no prevista por el spec).
**Falla observada (rojo):**
```
FAIL frontend src/app/app.routes.spec.ts > routes > inventario/nuevo e inventario/:id/editar están definidas como hijas de la ruta protegida, sin canActivate propio
AssertionError: expected [ [Function authGuard] ] to have a length of +0 but got 1
❯ src/app/app.routes.spec.ts:46:43
Test Files  1 failed | 1 passed (2)
     Tests  1 failed | 11 passed (12)
```
**Confirmado verde tras restaurar:** ✅ `git checkout --` + corrida conjunta: 12/12.

---

## Mecanismos generalizados (no reconstruidos individualmente, mismo patrón que la unidad cubierta)

- `product.service.spec.ts::getById obtiene un producto por id`, `create con 400 propaga el error`:
  mismo mecanismo de request/URL/propagación de error ya ejercitado por las unidades de `list`,
  `getById` (404) y `create` de arriba.
- `product-form.spec.ts::muestra un mensaje genérico ante un error no esperado (ej. red)`: mismo
  `if/else if/else` de mapeo de status ya cubierto por la unidad de "mensaje de error en 400" — el
  `else` es la rama complementaria, no un mecanismo distinto.
- `inventario.spec.ts` ya cubre las 3 assertions requeridas por el spec del listado (ver Task 2 de
  este mismo ciclo, que además refuerza la primera para las 7 columnas, no solo `material`).

## Confirmación final de la suite completa (todas las unidades restauradas)

```
ng test --watch=false --include='**/inventario.spec.ts' --include='**/product-form.spec.ts' \
  --include='**/product.service.spec.ts' --include='**/app.routes.spec.ts'

Test Files  4 passed (4)
     Tests  25 passed (25)
```

Árbol de trabajo verificado limpio al cierre: `git status --porcelain -- frontend/src` sin salida
antes de aplicar los cambios de la Tarea 2 (WARNs).
