# PRD FEAT-004: Módulo Oficina — carga de archivo de corte y generación de orden de trabajo

| Field | Value |
|-------|-------|
| Ticket | FEAT-004 |
| Tracker | none |
| Date | 2026-08-26 |
| PRD loops | 0 |

## Context and Problem

El PRD-001 (`docs/daw/prd/prd-001-captura-corte-inventario.md`) define el módulo de Oficina
(RF-01 a RF-07) como el punto de entrada del sistema: un usuario sube el archivo de corte PDF que
genera el software Salvagnini, el sistema extrae sus datos, genera un código NEST único y compromete
stock en el maestro de productos. Hoy ese proceso es manual y genera errores constantes de
codificación y de inventario — exactamente el problema que motiva todo el proyecto.

Ya existen las dos piezas de las que Oficina depende: el maestro de productos con `stock_comprometido`
(FEAT-002) y el Margen de Tolerancia Dimensional configurable (FEAT-003). Este ticket construye el
flujo de carga, extracción, revisión, confirmación y listado de órdenes de trabajo que los consume.

Se revisaron 3 archivos de corte reales de ejemplo (`docs/Archivos de Corte/Ejemplo 1.pdf`,
`Ejemplo 2.pdf`, `Ejemplo 3.pdf`) para definir la estructura exacta a parsear. Hallazgo relevante:
un mismo archivo PDF puede tener **varias páginas**, cada una con su propio "Índice formato"
(ej. "1/3", "2/3", "3/3"), su propio nombre de nest y su propio listado de piezas — es decir, cada
página representa una hoja de chapa física distinta, cortada de forma independiente. Se confirmó
con el usuario que cada página genera su propia orden de trabajo con su propio NEST.

También se confirmó en los ejemplos el formato real de los "Saved scrap" (RF-02-a): son filas del
listado de piezas sin valor en la columna "Ref.", con "Descripción" = "Saved scrap" y el campo
"Pieza" con el patrón `{largo}x{ancho}_RECT_SCRAP` (ej. `955.00x559.16_RECT_SCRAP`).

## Goals

Permitir a un usuario autenticado subir un archivo de corte PDF, revisar y validar/editar los datos
extraídos por página antes de confirmarlos, generar un código NEST único por cada página confirmada,
persistir la orden como "vigente", comprometer stock en el maestro de productos usando el margen de
tolerancia configurado, alertar sobre stock bajo, generar el documento imprimible con código de
barras, y listar/filtrar/buscar las órdenes de trabajo existentes.

## Functional Requirements

- FR-01: El sistema debe permitir a un usuario autenticado subir un archivo en formato PDF como
  archivo de corte, y debe rechazar cualquier archivo que no tenga extensión `.pdf`.
- FR-02: El sistema debe rechazar la subida de un archivo PDF que exceda los 10 MB de tamaño.
- FR-03: El sistema debe extraer, de cada página del archivo de corte, los siguientes datos:
  multiplicidad, dimensiones (largo x ancho del formato), espesor, material y tiempo de ejecución
  estimado.
- FR-04: El sistema debe extraer, de cada página, el listado de piezas con su referencia, cantidad,
  nombre de pieza y descripción.
- FR-05: El sistema debe identificar, dentro del listado de piezas de cada página, las filas cuya
  descripción sea exactamente "Saved scrap", y extraer el largo y el ancho del recorte a partir del
  patrón `{largo}x{ancho}` presente en el campo "Pieza" de esa fila.
- FR-06: El sistema debe rechazar un archivo PDF válido que no contenga las tablas de "Datos
  generales" y de listado de "Piezas" esperadas, informando que el archivo no es un archivo de corte
  reconocido.
- FR-07: El sistema debe tratar cada página de un archivo de corte con más de una página como un
  borrador de orden de trabajo independiente, con sus propios datos extraídos.
- FR-08: El sistema debe mostrar al usuario los datos extraídos de cada borrador de orden en un
  formulario editable, y debe permitir confirmar cada borrador de forma individual.
- FR-09: El sistema debe usar el valor editado por el usuario, en lugar del valor originalmente
  extraído, para cualquier campo que el usuario modifique antes de confirmar un borrador.
- FR-10: El sistema debe generar un código NEST único y secuencial al confirmar cada borrador de
  orden.
- FR-11: El sistema debe persistir la orden de trabajo confirmada con estado "vigente", incluyendo
  el código NEST, los datos generales (editados o extraídos) y el listado de piezas.
- FR-12: El sistema debe buscar, al confirmar una orden, un producto en el maestro de inventario
  cuyo material y espesor coincidan exactamente con los de la orden y cuyas dimensiones se
  encuentren dentro del Margen de Tolerancia Dimensional configurado (RF-17 de PRD-001).
- FR-13: El sistema debe incrementar el stock comprometido del producto encontrado en FR-12 en la
  cantidad indicada por la multiplicidad de la orden.
- FR-14: El sistema debe advertir al usuario, antes de completar la confirmación, si no encuentra
  ningún producto que cumpla FR-12.
- FR-15: El sistema debe ofrecer, ante la advertencia de FR-14, la creación automática del producto
  usando los datos técnicos extraídos del PDF (material, espesor, dimensiones), con stock físico en
  cero, y debe aplicar FR-13 sobre el producto recién creado si el usuario acepta.
- FR-16: El sistema debe mostrar un indicador visual de alerta para un producto cuando, tras
  aplicar FR-13, el resultado de (stock físico - stock comprometido) sea menor o igual a su punto de
  pedido.
- FR-17: El sistema debe generar, al confirmar una orden, un documento PDF descargable con el
  detalle de las piezas de la orden y un código de barras CODE_128 que codifique el código NEST.
- FR-18: El sistema debe permitir a un usuario autenticado listar las órdenes de trabajo,
  filtrando opcionalmente por estado ("vigente" o "cerrada").
- FR-19: El sistema debe permitir a un usuario autenticado buscar dentro del listado de órdenes por
  coincidencia parcial de código NEST, de forma combinable con el filtro de estado activo.
- FR-20: El sistema debe rechazar cualquier operación de este módulo (subir, confirmar, listar,
  buscar) si el usuario no está autenticado.

## Non-Functional Requirements

- NFR-01: La extracción de datos de una página de archivo de corte debe completarse en menos de 3
  segundos (p95).
- NFR-02: El código de barras generado debe ser decodificable por un lector independiente (pyzbar)
  a una resolución de impresión de 300 DPI o superior.
- NFR-03: El tiempo de respuesta para listar y buscar órdenes de trabajo debe ser menor a 2 segundos
  (p95), consistente con RNF-03 de PRD-001.

## Acceptance Criteria

- AC-01 (FR-01): WHEN un usuario autenticado sube un archivo con extensión `.pdf`, THE sistema SHALL
  aceptar la carga e iniciar la extracción.
- AC-02 (FR-01): IF el usuario intenta subir un archivo con una extensión distinta a `.pdf`, THEN
  THE sistema SHALL rechazar la carga e informar que solo se admiten archivos PDF.
- AC-03 (FR-02): IF el archivo PDF subido supera los 10 MB, THEN THE sistema SHALL rechazar la
  carga con un error 413 indicando el tamaño máximo permitido.
- AC-04 (FR-03): WHEN se sube un archivo de corte con multiplicidad, dimensiones, espesor, material
  y tiempo de ejecución estimado presentes en la tabla "Datos generales" de una página, THE sistema
  SHALL extraer esos valores exactos para esa página.
- AC-05 (FR-04): WHEN una página contiene un listado de piezas con referencia, cantidad, pieza y
  descripción, THE sistema SHALL extraer cada fila con esos cuatro campos.
- AC-06 (FR-05): WHEN una fila del listado de piezas tiene descripción "Saved scrap" y el campo
  "Pieza" con el patrón `955.00x559.16_RECT_SCRAP`, THE sistema SHALL extraer 955.00 mm de largo y
  559.16 mm de ancho como dimensiones del recorte.
- AC-07 (FR-06): IF el archivo subido es un PDF válido pero no contiene las tablas de "Datos
  generales" ni de "Piezas" esperadas, THEN THE sistema SHALL rechazarlo e informar que el archivo
  no es un archivo de corte reconocido.
- AC-08 (FR-07): WHEN el archivo de corte subido tiene más de una página, THE sistema SHALL generar
  un borrador de orden de trabajo independiente por cada página, con los datos extraídos de esa
  página únicamente.
- AC-09 (FR-08): WHEN finaliza la extracción de un borrador de orden, THE sistema SHALL mostrar sus
  datos extraídos en un formulario editable antes de permitir su confirmación.
- AC-10 (FR-09): IF el usuario modifica un campo extraído antes de confirmar un borrador, THEN THE
  sistema SHALL usar el valor editado en lugar del valor originalmente extraído al crear la orden.
- AC-11 (FR-10, FR-11): WHEN el usuario confirma un borrador de orden, THE sistema SHALL generar un
  código NEST único y secuencial y persistir la orden con estado "vigente".
- AC-12 (FR-12, FR-13): WHEN se confirma una orden y existe un producto en el maestro cuyo material
  y espesor coinciden exactamente con los de la orden y cuyas dimensiones están dentro del margen de
  tolerancia configurado, THE sistema SHALL incrementar el stock comprometido de ese producto en la
  cantidad indicada por la multiplicidad de la orden.
- AC-13 (FR-14): IF no existe ningún producto que cumpla la condición de AC-12 al confirmar una
  orden, THEN THE sistema SHALL advertir al usuario de la ausencia del producto antes de completar
  la confirmación.
- AC-14 (FR-15): WHEN el usuario acepta la advertencia de AC-13 y confirma la creación automática,
  THE sistema SHALL crear el producto con los datos técnicos extraídos del PDF y stock físico en
  cero, y luego aplicar sobre él el incremento de stock comprometido de AC-12.
- AC-15 (FR-16): WHEN tras incrementar el stock comprometido de un producto el resultado de (stock
  físico - stock comprometido) es menor o igual a su punto de pedido, THE sistema SHALL mostrar un
  indicador visual de alerta para ese producto.
- AC-16 (FR-17): WHEN se confirma una orden, THE sistema SHALL generar un documento PDF descargable
  con el detalle de las piezas de la orden y un código de barras CODE_128 que codifique el código
  NEST.
- AC-17 (NFR-02): WHEN se genera el documento de AC-16, THE sistema SHALL producir un código de
  barras decodificable por un lector independiente (pyzbar) a 300 DPI de resolución de impresión.
- AC-18 (FR-18): WHEN un usuario selecciona el filtro "vigente" o "cerrada" en el listado de
  órdenes, THE sistema SHALL mostrar únicamente las órdenes que coincidan con ese estado.
- AC-19 (FR-18): WHEN el usuario no selecciona ningún filtro de estado, THE sistema SHALL mostrar
  todas las órdenes de trabajo.
- AC-20 (FR-19): WHEN el usuario ingresa un texto en el buscador por código NEST, THE sistema SHALL
  mostrar únicamente las órdenes cuyo código NEST contenga ese texto, respetando el filtro de estado
  activo.
- AC-21 (FR-20): IF un usuario no autenticado intenta subir, confirmar, listar o buscar órdenes de
  trabajo, THEN THE sistema SHALL rechazar la petición con 401.

## Out of Scope

- Escaneo de código de barras y pantalla de Taller (RF-08 a RF-11 de PRD-001): finalizar la orden,
  cerrarla y descontar stock físico/comprometido — es el siguiente ticket, depende de que existan
  órdenes creadas por este.
- Impresión física directa a una impresora: este ticket genera un PDF descargable/imprimible desde
  el navegador (confirmado con el usuario); no hay integración con drivers de impresora.
- Confirmación en bloque de todas las páginas de un archivo de varias páginas a la vez: en este
  ticket cada página se revisa y confirma individualmente (confirmado con el usuario).
- Edición o eliminación de una orden de trabajo ya confirmada ("vigente"): no hay ningún RF de
  edición/baja de órdenes en PRD-001; el único cambio de estado posterior es el cierre en Taller
  (RF-09), fuera de este ticket.
- Notificación proactiva del punto de pedido (email, push): RF-06 solo pide un indicador visual en
  el listado, no un canal de notificación activo.
- Compras, reposición de stock o generación de órdenes de compra: explícitamente fuera de alcance
  de PRD-001.
- Validación de multiplicidad negativa, cero o no entera: se asume que el archivo de corte siempre
  trae un valor entero positivo (así en los 3 ejemplos revisados); un valor fuera de ese rango se
  trata como riesgo documentado, no como un flujo de validación implementado.

## Risks and Mitigations

- Riesgo: la estructura real de las tablas del PDF puede variar entre plantillas o versiones de
  Salvagnini (columnas, idioma, orden de las secciones), y el parser basado en `pdfplumber` podría
  no encontrar una tabla esperada.
  Mitigación: validar explícitamente la presencia de las tablas "Datos generales" y "Piezas" antes
  de dar por buena la extracción (AC-07), en vez de continuar silenciosamente con datos parciales o
  vacíos.
- Riesgo: ninguno de los 3 archivos de ejemplo disponibles tiene multiplicidad mayor a 1, dejando sin
  cubrir con datos reales el caso de compromiso de stock por más de una unidad.
  Mitigación: cubrir el caso multiplicidad > 1 con un test unitario usando datos sintéticos además de
  los PDFs de ejemplo.
- Riesgo: generar el código de barras con un `module_width` insuficiente o un tamaño de imagen que no
  respete la relación de aspecto real lo vuelve ilegible aunque se vea bien en pantalla (riesgo
  explícito documentado en AGENTS.md, sección "What NOT to do").
  Mitigación: verificar el código con un decodificador independiente (pyzbar) como parte de los
  tests (AC-17), a resolución de impresión típica (≥300 DPI), no solo validar que se generó una
  imagen.
- Riesgo: al tratar cada página de un PDF multi-página como una orden independiente, un archivo con
  muchas páginas genera muchos NESTs de una sola vez y el usuario podría perder de vista a qué hoja
  física corresponde cada borrador durante la revisión.
  Mitigación: mostrar el "Índice formato" original de la página (ej. "2/3") junto a cada borrador
  durante su revisión, para que el usuario pueda correlacionarlo con la hoja física correspondiente.

## Dependencies

- Depende de la autenticación JWT ya implementada en FEAT-001: todos los endpoints de este módulo
  requieren un usuario autenticado, sin restricción de rol (RF-19-a de PRD-001).
- Depende del maestro de productos de FEAT-002 (Inventario): busca coincidencias y actualiza el
  campo `stock_comprometido` que ese ticket dejó preparado, y usa su mismo modelo de producto para
  la creación automática (RF-05-b).
- Depende del Margen de Tolerancia Dimensional de FEAT-003 (Configuración): la búsqueda de
  coincidencia de producto (FR-12) usa el valor allí configurado, no un valor fijo.
- Introduce dos librerías nuevas ya declaradas en el Stack de AGENTS.md: `pdfplumber` (extracción de
  datos del PDF) y `python-barcode` + `pyzbar` (generación y verificación del código de barras
  CODE_128).
- Referencia: `docs/daw/prd/prd-001-captura-corte-inventario.md` (RF-01 a RF-07, AC-01 a AC-14).
- Referencia de datos reales: `docs/Archivos de Corte/Ejemplo 1.pdf`, `Ejemplo 2.pdf`, `Ejemplo 3.pdf`
  (usados para definir la estructura de extracción de este PRD).
