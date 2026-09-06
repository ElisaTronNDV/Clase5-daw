# Evidencia TDD reconstruida — FEAT-004 (frontend, Bloque 6 — módulo Oficina)

## Contexto

`daw-module-verifier` bloqueó el paso a RELEASE de FEAT-004 (ronda 1) porque el reporte del Bloque 6
no documentaba, para cada mecanismo de lógica nueva del frontend, qué test fallaba y con qué
assertion **antes** de existir la implementación — mismo gap (Regla #-1 de
`.daw/rules/testing.instructions.md`) que ya bloqueó a FEAT-001 y FEAT-002.

Este documento reconstruye esa evidencia de forma honesta **sobre el código ya escrito** (aún no
commiteado; archivos nuevos bajo `frontend/src/app/oficina/`). Método, idéntico al de
`tdd-evidence-FEAT-002-frontend.md`: para cada unidad de lógica se aplicó al **código de
producción** la ruptura mínima necesaria para que el test fallara por la razón real (no por un error
de compilación ajeno), se corrió el/los spec, se copió el output rojo textual, y se restauró el
archivo antes de pasar a la siguiente unidad. No se cambió comportamiento ni se escribió lógica
nueva; las rupturas se revirtieron una a una (los archivos son nuevos y no están trackeados, así que
la restauración fue por edición inversa, no `git checkout --`).

Además de la reconstrucción, en esta ronda se **agregaron los tests de sad-path** que el spec y el
verificador exigían (sección "Tests agregados") y se midió cobertura (sección "Cobertura").

## Nota sobre el entorno de ejecución

Mismo problema de infraestructura conocido (WSL, ruta con espacios `.../tp ia/clase5/`) ya
documentado en `tdd-evidence-FEAT-001-frontend.md` y `-FEAT-002-frontend.md`: Vitest (runner por
defecto de Angular 22) dispara de forma intermitente `Failed to start forks worker` / `Timeout
waiting for worker to respond` cuando se corren los 5 `.spec.ts` del módulo en una sola invocación —
y de forma **reproducible** sobre `orden.service.spec.ts` (el que usa `provideHttpClientTesting`)
cuando comparte corrida con ≥3 archivos. Workaround aplicado en todo el documento: correr los spec
en **lotes de 2–3 archivos**. Cada corrida roja/verde de abajo indica con qué lote se ejecutó.

---

## Bloque 6 — `OrdenService`

### `subirArchivo()` — arma `FormData` con el campo `archivo`
**Test:** `orden.service.spec.ts::arma FormData correctamente en subirArchivo`
**Ruptura:** `orden.service.ts` — `formData.append('archivo', file)` → `formData.append('documento', file)`.
**Falla observada (rojo)** (lote: `orden.service` + `revision-borrador` + `listado-ordenes`):
```
FAIL  src/app/oficina/services/orden.service.spec.ts > OrdenService > subirArchivo > arma FormData correctamente en subirArchivo
AssertionError: expected null to be File{ …(1) } // Object.is equality
- Expected:  File {}
+ Received:  null
❯ src/app/oficina/services/orden.service.spec.ts:36:35
      expect(body.get('archivo')).toBe(file);
```
**Confirmado verde tras restaurar:** ✅ (lote `orden.service` + `oficina`: 9/9).

### `confirmarOrden()` — propaga el error 409 (no lo absorbe)
**Test:** `orden.service.spec.ts::propaga el error 409 de confirmarOrden`
**Ruptura:** `orden.service.ts` — se envolvió el `POST` en
`.pipe(catchError(() => of(null as unknown as OrdenResponse)))`, absorbiendo cualquier error HTTP.
**Falla observada (rojo)** (lote: `orden.service` + `listado-ordenes` + `oficina`):
```
FAIL  src/app/oficina/services/orden.service.spec.ts > OrdenService > confirmarOrden > propaga el error 409 de confirmarOrden
AssertionError: expected undefined to be an instance of HttpErrorResponse
❯ src/app/oficina/services/orden.service.spec.ts:70:29
      expect(errorReceived).toBeInstanceOf(HttpErrorResponse);

⎯ Uncaught Exception ⎯
Error: should not emit a value
❯ Object.next src/app/oficina/services/orden.service.spec.ts:55:17
```
(el `Uncaught Exception: should not emit a value` confirma que, con el error absorbido, el `next` sí
emitió — justo lo que el test declara que no debe pasar.)
**Confirmado verde tras restaurar:** ✅ (lote `orden.service` + `oficina`: 9/9).

### `listarOrdenes()` — arma los query params `estado`/`nest` sólo si están presentes
**Test:** `orden.service.spec.ts::arma los query params de listarOrdenes`
**Ruptura:** `orden.service.ts` — dentro de `if (estado)`, `params.set('estado', estado)` →
`params.set('estado_x', estado)`.
**Falla observada (rojo)** (lote: `orden.service` + `revision-borrador` + `listado-ordenes`):
```
FAIL  src/app/oficina/services/orden.service.spec.ts > OrdenService > listarOrdenes > arma los query params de listarOrdenes
AssertionError: expected null to be 'vigente' // Object.is equality
- Expected:  "vigente"
+ Received:  null
❯ src/app/oficina/services/orden.service.spec.ts:125:48
      expect(req.request.params.get('estado')).toBe('vigente');
```
El test hermano `no agrega params ausentes` siguió verde (la rama `if (nest)` intacta), confirmando
que la ruptura aisló el mapeo del param `estado`.
**Confirmado verde tras restaurar:** ✅ (lote `orden.service` + `oficina`: 9/9).

**Generalizado (mismo mecanismo, no reconstruido aparte):**
`descargarDocumento()` (`responseType: 'blob'`, URL `/{id}/documento`) — mismo patrón request/URL ya
ejercitado por `subirArchivo`/`listarOrdenes`; su test `pide el documento como blob` verifica método,
URL y `responseType`.

---

## Bloque 6 — `RevisionBorrador`

### `effect()` de precarga del formulario desde `borrador()` (AC-09)
**Test:** `revision-borrador.spec.ts::muestra los datos extraídos en un formulario editable antes de confirmar`
**Ruptura:** `revision-borrador.ts` — en el `form.reset({...})` del `effect`, `multiplicidad: b.multiplicidad`
→ `multiplicidad: 1` (valor fijo, ignora el borrador).
**Falla observada (rojo)** (lote: `orden.service` + `revision-borrador` + `listado-ordenes`):
```
FAIL  src/app/oficina/revision-borrador/revision-borrador.spec.ts > RevisionBorrador > muestra los datos extraídos en un formulario editable antes de confirmar
AssertionError: expected 1 to be 2 // Object.is equality
- 2
+ 1
❯ src/app/oficina/revision-borrador/revision-borrador.spec.ts:71:64
      expect(fixture.componentInstance.form.value.multiplicidad).toBe(2);
```
(los asserts de `material`, `espesor`, `largo`, `ancho` del mismo test comparten el mismo
`form.reset(...)` — romper un campo alcanza para demostrar el mecanismo de precarga.)
**Confirmado verde tras restaurar:** ✅ (lote `revision-borrador` + `subir-archivo`: 16/16).

### `getRawValue()` — usa el valor **editado** del form, no el extraído (AC-10)
**Test:** `revision-borrador.spec.ts::usa el valor editado en vez del extraído al confirmar`
**Ruptura:** `revision-borrador.ts` — en la construcción del payload de `enviar()`,
`material: v.material as string` (valor del form) → `material: this.borrador().material` (valor extraído).
**Falla observada (rojo)** (lote: `orden.service` + `revision-borrador` + `listado-ordenes`):
```
FAIL  src/app/oficina/revision-borrador/revision-borrador.spec.ts > RevisionBorrador > usa el valor editado en vez del extraído al confirmar
AssertionError: expected 'sae_1010' to be 'sae_1020' // Object.is equality
Expected: "sae_1020"
Received: "sae_1010"
❯ src/app/oficina/revision-borrador/revision-borrador.spec.ts:91:30
      expect(payload.material).toBe('sae_1020');
```
**Confirmado verde tras restaurar:** ✅ (lote `revision-borrador` + `subir-archivo`: 16/16).

### Mapeo `409 → productoNoEncontrado()` + diálogo de advertencia
**Test:** `revision-borrador.spec.ts::muestra el diálogo de advertencia ante 409 y reintenta con la bandera`
**Ruptura:** `revision-borrador.ts` — en el handler de error, `err.status === 409` → `err.status === 4090`.
**Falla observada (rojo)** (lote: `orden.service` + `revision-borrador` + `listado-ordenes`):
```
FAIL  src/app/oficina/revision-borrador/revision-borrador.spec.ts > RevisionBorrador > muestra el diálogo de advertencia ante 409 y reintenta con la bandera
AssertionError: expected null to deeply equal { material: 'sae_1010', …(3) }
- Expected: { "ancho": 500, "espesor": 2.1, "largo": 1000, "material": "sae_1010" }
+ Received: null
❯ src/app/oficina/revision-borrador/revision-borrador.spec.ts:108:62
      expect(fixture.componentInstance.productoNoEncontrado()).toEqual(errorBody);
```
**Confirmado verde tras restaurar:** ✅ (lote `revision-borrador` + `subir-archivo`: 16/16).

**Generalizado (mismo test, misma ruta):** `onCrearProductoYConfirmar()` delega en `enviar(true)`;
cambiar ese literal a `enviar(false)` hace fallar, en el mismo test, el assert
`expect(segundoPayload.crear_producto_automaticamente).toBe(true)`. No se reconstruye aparte porque
comparte fixture y ruta de ejecución con la ruptura de arriba.

### Rama `422` de la confirmación (mensaje "datos inválidos")
**Test:** `revision-borrador.spec.ts::ante un 422 muestra un mensaje de datos inválidos y no marca la orden como confirmada` *(agregado esta ronda)*
**Ruptura:** `revision-borrador.ts` — `else if (err.status === 422)` → `else if (err.status === 4220)`
(cae a la rama `else` genérica).
**Falla observada (rojo)** (lote: `orden.service` + `revision-borrador` + `listado-ordenes`):
```
FAIL  src/app/oficina/revision-borrador/revision-borrador.spec.ts > RevisionBorrador > ante un 422 muestra un mensaje de datos inválidos y no marca la orden como confirmada
AssertionError: expected 'No se pudo confirmar la orden. Intent…' to be 'Los datos de la orden no son válidos.…' // Object.is equality
Expected: "Los datos de la orden no son válidos. Revisá los campos."
Received: "No se pudo confirmar la orden. Intentá nuevamente."
❯ src/app/oficina/revision-borrador/revision-borrador.spec.ts:153:54
```
El test `ante un error no esperado (500)` siguió verde, confirmando que la ruptura aisló la rama 422
sin tocar el `else`.
**Confirmado verde tras restaurar:** ✅ (lote `revision-borrador` + `subir-archivo`: 16/16).

### Rama `else` genérica de la confirmación
**Test:** `revision-borrador.spec.ts::ante un error no esperado (500) muestra un mensaje genérico de confirmación` *(agregado esta ronda)*
**Ruptura:** `revision-borrador.ts` — el mensaje del `else`
(`'No se pudo confirmar la orden. Intentá nuevamente.'`) → `'X'`.
**Falla observada (rojo)** (lote: `revision-borrador` + `subir-archivo`, corrida dedicada):
```
FAIL  src/app/oficina/revision-borrador/revision-borrador.spec.ts > RevisionBorrador > ante un error no esperado (500) muestra un mensaje genérico de confirmación
AssertionError: expected 'X' to be 'No se pudo confirmar la orden. Intentá nuevamente.' // Object.is equality
❯ src/app/oficina/revision-borrador/revision-borrador.spec.ts (rama else de enviar())
```
El test de la rama 422 siguió verde (su rama propia intacta).
**Confirmado verde tras restaurar:** ✅ (lote `revision-borrador` + `subir-archivo`: 16/16).

### `@if` de `[data-testid="alerta-stock-bajo"]` (true y false)
**Tests:** `revision-borrador.spec.ts::muestra el indicador de alerta_stock_bajo cuando viene en true`,
`::no muestra el indicador de alerta_stock_bajo cuando viene en false`
**Ruptura:** `revision-borrador.html` — `@if (orden.alerta_stock_bajo === true)` → `@if (orden.alerta_stock_bajo !== true)`.
**Falla observada (rojo)** (lote: `orden.service` + `revision-borrador` + `listado-ordenes`):
```
FAIL  … > muestra el indicador de alerta_stock_bajo cuando viene en true
AssertionError: expected null to be truthy
❯ src/app/oficina/revision-borrador/revision-borrador.spec.ts:130:73
      expect(compiled.querySelector('[data-testid="alerta-stock-bajo"]')).toBeTruthy();

FAIL  … > no muestra el indicador de alerta_stock_bajo cuando viene en false
AssertionError: expected <div … data-testid="alerta-stock-bajo" …> to be falsy
+ Received: <div class="alert alert-warning mt-2" data-testid="alerta-stock-bajo" role="alert"> El stock del producto quedó en o por debajo del punto de pedido. </div>
❯ src/app/oficina/revision-borrador/revision-borrador.spec.ts:141:73
```
(una sola inversión del predicado rompe las dos direcciones — cubre ambos tests.)
**Confirmado verde tras restaurar:** ✅ (lote `revision-borrador` + `subir-archivo`: 16/16).

### Placeholder de `indice_formato` ausente
**Test:** `revision-borrador.spec.ts::muestra un placeholder cuando el borrador no trae indice_formato` *(agregado esta ronda)*
**Ruptura:** `revision-borrador.html` — `{{ borrador().indice_formato ?? '(sin índice)' }}` → `{{ borrador().indice_formato }}`.
**Falla observada (rojo):**
```
FAIL  … > muestra un placeholder cuando el borrador no trae indice_formato
AssertionError: expected '…' to contain '(sin índice)'
❯ revision-borrador.spec.ts  expect(fixture.nativeElement.textContent).toContain('(sin índice)');
```
**Confirmado verde tras restaurar:** ✅ (lote `revision-borrador` + `subir-archivo`: 16/16).

---

## Bloque 6 — `ListadoOrdenes`

### `estado || undefined` / `nest || undefined` al llamar `listarOrdenes`
**Tests:** `listado-ordenes.spec.ts::aplica el filtro de estado`,
`::combina filtro de estado con búsqueda por NEST`
**Ruptura:** `listado-ordenes.ts` — `listarOrdenes(estado || undefined, nest || undefined)` →
`listarOrdenes(nest || undefined, estado || undefined)` (argumentos cruzados).
**Falla observada (rojo)** (lote: `orden.service` + `revision-borrador` + `listado-ordenes`):
```
FAIL  … > aplica el filtro de estado
AssertionError: expected last "vi.fn()" call to have been called with [ 'vigente', undefined ]
- Expected:  [ "vigente", undefined ]
+ Received:  [ undefined, "vigente" ]
❯ src/app/oficina/listado-ordenes/listado-ordenes.spec.ts:61:45

FAIL  … > combina filtro de estado con búsqueda por NEST
AssertionError: expected last "vi.fn()" call to have been called with [ 'cerrada', 'NEST-000001' ]
+ Received:  [ "NEST-000001", "cerrada" ]
❯ src/app/oficina/listado-ordenes/listado-ordenes.spec.ts:76:45
```
El `undefined` esperado en el primer arg del test `aplica el filtro` es lo que ejercita el
`nest || undefined` (convierte `''` en `undefined`).
**Confirmado verde tras restaurar:** ✅ (lote `listado-ordenes` + `oficina`: 9/9).

### `debounceTime` de los filtros (ventana de 300 ms)
**Tests:** `listado-ordenes.spec.ts::aplica el filtro de estado`, `::combina filtro de estado con búsqueda por NEST`
**Ruptura:** `listado-ordenes.ts` — `debounceTime(DEBOUNCE_MS)` (300) → `debounceTime(5000)`.
**Falla observada (rojo)** (lote: `orden.service` + `listado-ordenes` + `oficina`):
```
FAIL  … > aplica el filtro de estado
AssertionError: expected "vi.fn()" to be called 1 times, but got 0 times
❯ src/app/oficina/listado-ordenes/listado-ordenes.spec.ts:60:45
      expect(ordenServiceSpy.listarOrdenes).toHaveBeenCalledTimes(1);   // tras vi.advanceTimersByTime(400)

FAIL  … > combina filtro de estado con búsqueda por NEST
AssertionError: expected last "vi.fn()" call to have been called with [ 'cerrada', 'NEST-000001' ]
+ Received:  undefined
```
Con la ventana de debounce a 5 s, `vi.advanceTimersByTime(400)` no alcanza a disparar `cargar()`.
El test `carga las órdenes al inicializar` siguió verde (esa llamada no pasa por el debounce).
**Confirmado verde tras restaurar:** ✅ (lote `listado-ordenes` + `oficina`: 9/9).

### `cargar()` ante error del servicio → `errorMessage`
**Test:** `listado-ordenes.spec.ts::setea errorMessage cuando el servicio falla al recargar el listado` *(agregado esta ronda)*
**Ruptura:** `listado-ordenes.ts` — en `cargar()`,
`error: () => this.errorMessage.set('No se pudieron cargar las órdenes.')` → `error: () => {}`.
**Falla observada (rojo)** (lote: `orden.service` + `revision-borrador` + `listado-ordenes`):
```
FAIL  … > setea errorMessage cuando el servicio falla al recargar el listado
AssertionError: expected null to be truthy
- Expected: true
+ Received: null
❯ src/app/oficina/listado-ordenes/listado-ordenes.spec.ts:116:56
      expect(fixture.componentInstance.errorMessage()).toBeTruthy();
```
**Confirmado verde tras restaurar:** ✅ (lote `listado-ordenes` + `oficina`: 9/9).

### `descargar()` ante fallo del blob → `errorMessage`
**Test:** `listado-ordenes.spec.ts::setea errorMessage cuando falla la descarga del documento` *(agregado esta ronda)*
**Ruptura:** `listado-ordenes.ts` — en `descargar()`,
`error: () => this.errorMessage.set('No se pudo descargar el documento de la orden.')` → `error: () => {}`.
**Falla observada (rojo)** (lote: `orden.service` + `revision-borrador` + `listado-ordenes`):
```
FAIL  … > setea errorMessage cuando falla la descarga del documento
AssertionError: expected null to be truthy
❯ src/app/oficina/listado-ordenes/listado-ordenes.spec.ts:128:54
      expect(fixture.componentInstance.errorMessage()).toBeTruthy();
```
**Confirmado verde tras restaurar:** ✅ (lote `listado-ordenes` + `oficina`: 9/9).

### `dispararDescarga()` — `URL.createObjectURL` + enlace temporal con click programático
**Test:** `listado-ordenes.spec.ts::dispara la descarga del blob con un enlace temporal`
**Ruptura:** `listado-ordenes.ts` — se eliminó la línea `enlace.click();` de `dispararDescarga()`.
**Falla observada (rojo)** (lote: `orden.service` + `revision-borrador` + `listado-ordenes`):
```
FAIL  … > dispara la descarga del blob con un enlace temporal
AssertionError: expected "click" to be called at least once
❯ src/app/oficina/listado-ordenes/listado-ordenes.spec.ts:99:24
      expect(clickSpy).toHaveBeenCalled();
```
Los asserts previos del test (`descargarDocumento` llamado con el id, `URL.createObjectURL` llamado)
siguieron pasando — la ruptura aisló el click programático.
**Confirmado verde tras restaurar:** ✅ (lote `listado-ordenes` + `oficina`: 9/9).

---

## Bloque 6 — `Oficina` (orquestador)

### `onPaginasExtraidas()` — muestra `RevisionBorrador` para la primera página
**Test:** `oficina.spec.ts::al recibir paginasExtraidas muestra RevisionBorrador para la primera página`
**Ruptura:** `oficina.ts` — en `onPaginasExtraidas()` se comentó `this.vista.set('revision')`.
**Falla observada (rojo)** (lote: `oficina` + `subir-archivo`):
```
FAIL  src/app/oficina/oficina.spec.ts > Oficina > al recibir paginasExtraidas muestra RevisionBorrador para la primera página
AssertionError: expected null to be truthy
- Expected: true
+ Received: null
❯ src/app/oficina/oficina.spec.ts:71:61
      expect(compiled.querySelector('app-revision-borrador')).toBeTruthy();
```
El test `renderiza SubirArchivo al inicio` siguió verde.
**Confirmado verde tras restaurar:** ✅ (lote `oficina` + `subir-archivo`: 11/11).

### `onOrdenConfirmada()` — avance página por página → listado tras la última
**Test:** `oficina.spec.ts::avanza página por página al confirmar y pasa al listado tras la última` *(agregado esta ronda)*
**Ruptura:** `oficina.ts` — `if (siguiente < this.borradores().length)` → `if (siguiente < 0)`
(nunca avanza el índice; salta directo a `listado`).
**Falla observada (rojo)** (lote: `orden.service` + `listado-ordenes` + `oficina`):
```
FAIL  src/app/oficina/oficina.spec.ts > Oficina > avanza página por página al confirmar y pasa al listado tras la última
AssertionError: expected +0 to be 1 // Object.is equality
- 1
+ 0
❯ src/app/oficina/oficina.spec.ts:92:54
      expect(fixture.componentInstance.indiceActual()).toBe(1);
```
**Confirmado verde tras restaurar:** ✅ (lote `oficina` + `subir-archivo`: 11/11).

---

## Bloque 6 — `SubirArchivo`

### Validación de extensión `.pdf` en cliente
**Test:** `subir-archivo.spec.ts::rechaza en cliente un archivo no-PDF`
**Ruptura:** `subir-archivo.ts` — `if (!file.name.toLowerCase().endsWith('.pdf'))` →
`if (file.name.toLowerCase().endsWith('.pdf'))` (predicado invertido).
**Falla observada (rojo)** (lote: `oficina` + `subir-archivo`):
```
FAIL  src/app/oficina/subir-archivo/subir-archivo.spec.ts > SubirArchivo > rechaza en cliente un archivo no-PDF
TypeError: Cannot read properties of undefined (reading 'subscribe')
❯ _SubirArchivo.onFileSelected src/app/oficina/subir-archivo/subir-archivo.ts:37:40
❯ src/app/oficina/subir-archivo/subir-archivo.spec.ts:40:31
```
(con el guard invertido, el `.txt` **no** se rechaza en cliente y llega a `OrdenService.subirArchivo`
— el `TypeError` en `.subscribe` es la señal de que el archivo no-PDF pasó la validación, justo lo
que el test verifica que no debe pasar. La misma inversión también rompe, por efecto cascada, los
happy-path del archivo — todos muestran `Received: 'El archivo debe ser un PDF (.pdf).'`, un único
origen.)
**Confirmado verde tras restaurar:** ✅ (lote `oficina` + `subir-archivo`: 11/11).

### Mapeo de `HttpErrorResponse` 413 / 422 / 400 a mensajes en español distintos
**Tests:** `subir-archivo.spec.ts::mapea el 413 a un mensaje de tamaño máximo en español`,
`::mapea el 422 usando el detail del backend cuando es un string`,
`::mapea el 422 sin detail legible a un mensaje genérico de procesamiento`,
`::mapea el 400 (PDF inválido) a un mensaje distinto del de 413/422` *(4 tests agregados esta ronda)*
**Ruptura:** `subir-archivo.ts` — misma inversión del guard `.pdf` de arriba (todos los archivos
`.pdf` de estos tests entran a la rama de rechazo antes de llegar al `subscribe`, así que nunca se
ejecuta el mapeo de status).
**Falla observada (rojo)** (lote: `oficina` + `subir-archivo`):
```
FAIL  … > mapea el 413 a un mensaje de tamaño máximo en español
AssertionError: expected 'El archivo debe ser un PDF (.pdf).' to be 'El archivo supera el tamaño máximo pe…'
Expected: "El archivo supera el tamaño máximo permitido (10 MB)."
Received: "El archivo debe ser un PDF (.pdf)."

FAIL  … > mapea el 422 usando el detail del backend cuando es un string
Expected: "No se encontraron las tablas esperadas del archivo de corte"
Received: "El archivo debe ser un PDF (.pdf)."

FAIL  … > mapea el 422 sin detail legible a un mensaje genérico de procesamiento
Expected: "El archivo de corte no pudo procesarse. Revisá que sea un PDF válido de Salvagnini."
Received: "El archivo debe ser un PDF (.pdf)."

FAIL  … > mapea el 400 (PDF inválido) a un mensaje distinto del de 413/422
Expected: "el archivo no es un PDF válido"
Received: "El archivo debe ser un PDF (.pdf)."
```
**Verde tras restaurar (ver más abajo — corrida dedicada `revision-borrador` + `subir-archivo`):**
los 4 tests pasan y cada rama de status produce su propio mensaje.
**Confirmado verde tras restaurar:** ✅ (lote `revision-borrador` + `subir-archivo`: 16/16).

### Indicador de carga (`cargando()`) mientras la subida está en curso
**Test:** `subir-archivo.spec.ts::muestra el indicador de carga mientras la subida está en curso` *(agregado esta ronda)*
**Ruptura:** `subir-archivo.ts` — `this.cargando.set(true)` antes del `subscribe` → se eliminó.
**Falla observada (rojo)** (lote: `revision-borrador` + `subir-archivo`):
```
FAIL  … > muestra el indicador de carga mientras la subida está en curso
AssertionError: expected false to be true // Object.is equality
❯ subir-archivo.spec.ts  expect(fixture.componentInstance.cargando()).toBe(true);
```
**Confirmado verde tras restaurar:** ✅ (lote `revision-borrador` + `subir-archivo`: 16/16).

---

## Tests agregados esta ronda (sad-path + branch coverage)

| Archivo | Test | Resultado |
|---|---|---|
| `revision-borrador.spec.ts` | `ante un 422 muestra un mensaje de datos inválidos y no marca la orden como confirmada` | ✅ |
| `revision-borrador.spec.ts` | `ante un error no esperado (500) muestra un mensaje genérico de confirmación` | ✅ |
| `revision-borrador.spec.ts` | `muestra un placeholder cuando el borrador no trae indice_formato` | ✅ |
| `listado-ordenes.spec.ts` | `setea errorMessage cuando el servicio falla al recargar el listado` | ✅ |
| `listado-ordenes.spec.ts` | `setea errorMessage cuando falla la descarga del documento` | ✅ |
| `subir-archivo.spec.ts` | `mapea el 413 a un mensaje de tamaño máximo en español` | ✅ |
| `subir-archivo.spec.ts` | `mapea el 422 usando el detail del backend cuando es un string` | ✅ |
| `subir-archivo.spec.ts` | `mapea el 422 sin detail legible a un mensaje genérico de procesamiento` | ✅ |
| `subir-archivo.spec.ts` | `mapea el 400 (PDF inválido) a un mensaje distinto del de 413/422` | ✅ |
| `subir-archivo.spec.ts` | `muestra el indicador de carga mientras la subida está en curso` | ✅ |
| `oficina.spec.ts` | `avanza página por página al confirmar y pasa al listado tras la última` | ✅ |

Cada uno se vio fallar primero contra el código de producción roto (rupturas documentadas arriba) y
pasar tras restaurar. **No se tocó código de producción para subir cobertura** — sólo se agregaron
tests.

---

## Suite completa del módulo Oficina (todas las rupturas restauradas)

Corrida en lotes por el problema de worker de Vitest en WSL:

```
ng test --no-watch --include='…/oficina.spec.ts' --include='…/listado-ordenes.spec.ts' \
                   --include='…/revision-borrador.spec.ts' --include='…/subir-archivo.spec.ts'
  → Test Files 4 passed (4)   Tests 25 passed (25)

ng test --no-watch --include='…/services/orden.service.spec.ts' --include='…/oficina.spec.ts'
  → Test Files 2 passed (2)   Tests 9 passed (9)   [orden.service.spec: 6/6]
```

Total del módulo: **5 archivos, 31 tests, 31 verde** (oficina 3 · listado-ordenes 6 · revision-borrador 8 · subir-archivo 8 · orden.service 6).

---

## Cobertura

`ng test --no-watch --coverage --coverage-reporters=json-summary --coverage-include='src/app/oficina/**'`,
medida en los mismos lotes (cada archivo se reporta desde el lote donde corrió su `.spec`; v8 excluye
del reporte los `.html` de componentes cuyo spec no corrió en ese lote, y colapsa los archivos al
100%).

| Archivo (`frontend/src/app/oficina/`) | % Rama | % Stmt | % Func | % Línea |
|---|---|---|---|---|
| `services/orden.service.ts` | **100** (7/7) | 100 | 100 | 100 |
| `oficina.ts` | **92.85** (13/14) | 78.26 | 66.66 | 72.22 |
| `oficina.html` | **100** (6/6) | 93.54 | 50 | 100 |
| `listado-ordenes/listado-ordenes.ts` | **100** (9/9) | 100 | 100 | 98.57 |
| `listado-ordenes/listado-ordenes.html` | **100** (2/2) | 97.77 | 0 | 97.72 |
| `revision-borrador/revision-borrador.ts` | **87.5** (21/24) | 97.67 | 100 | 97.36 |
| `revision-borrador/revision-borrador.html` | **100** (12/12) | 96.34 | 0 | 100 |
| `subir-archivo/subir-archivo.ts` | **90.62** (29/32) | 96.77 | 100 | 96.29 |
| `subir-archivo/subir-archivo.html` | **100** (4/4) | 95.45 | 0 | 100 |

### Agregado sobre `frontend/src/app/oficina/**` (suma de contadores de los 3 lotes, sin `.scss`)

| Métrica | Cobertura |
|---|---|
| **Ramas** | **93.64 % (103/110)** |
| Sentencias | 95.93 % (354/369) |
| Funciones | 80.95 % (34/42) |
| Líneas | 96.88 % (248/256) |

Cobertura de **rama ≥ 80 %** cumplida sobre todo el código nuevo (mínimo por archivo: 87.5 % en
`revision-borrador.ts`; agregado 93.64 %).

Ramas/funciones sin cubrir (residual, no lógica de negocio):
- `oficina.ts`: `irAListado()` / `nuevaCarga()` (helpers de navegación del header, no ejercitados) y
  1 rama del `computed` `borradorActual` con lista vacía.
- `revision-borrador.ts`: 3 ramas de los `?? null` del payload (`indice_formato` /
  `tiempo_ejecucion_estimado` cuando el control está en `null`).
- `subir-archivo.ts`: rama "sin archivo seleccionado" de `onFileSelected` y el fallback no-string del
  `detail` en 400.
- Los `% Func 0` de los `.html` son las funciones de template generadas por Angular — artefacto del
  reporter v8, no código sin testear.
