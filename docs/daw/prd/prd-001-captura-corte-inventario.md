# PRD-001: DyP LaserCore — Sistema de automatización de captura de datos técnicos para la optimización integral del inventario y el flujo productivo.

## Contexto y Problema
DyP es una empresa de procesamiento de chapas metálicas que ofrece servicios de corte láser, plegado, panelado y soldadura. Su principal problema es la dependencia de procesos manuales para la captura de datos y la codificación, lo que genera errores constantes en el inventario de chapas y recortes.

## Objetivos
Automatizar la captura de datos desde el archivo de corte (.pdf) para la generación de códigos únicos (NEST), buscando eliminar errores en carga manual y garantizar el control de stock desde el inicio del proceso.

## Requerimientos Funcionales

### Oficina
- RF-01: Un usuario autenticado debe poder subir el archivo de corte en formato PDF generado por el software CAD/CAM Salvagnini. Los datos se encuentran en tablas estructuradas (Datos Generales, Datos de Elaboración, Datos de Producción y listado de Piezas)
- RF-02: El sistema debe extraer los siguientes datos generales del archivo: multiplicidad, dimensiones, espesor, material, tiempo de ejecución estimado, y el detalle de las piezas con sus cantidades.
  - RF-02-a: El sistema debe extraer las dimensiones de los recortes sobrantes (identificados con la descripción "Saved scrap") a partir del nombre técnico del ítem en el campo 'Pieza' (ej: largo x ancho).
- RF-03: El sistema debe generar un código único NEST (secuencial).
- RF-04: El sistema debe guardar la orden de trabajo en la base de datos con estado "vigente".
  - RF-04-a: El sistema debe imprimir la orden de trabajo al confirmarla, incluyendo un código de barras que identifique el código NEST.
- RF-05: El sistema debe comprometer el stock en el maestro de productos correspondiente al material, espesor y dimensiones indicados en la orden, utilizando para la búsqueda el parámetro de tolerancia en las dimensiones. La cantidad comprometida lo determina la multiplicidad.
  - RF-05-a: El sistema debe advertir al usuario si el producto no existe en el maestro.
  - RF-05-b: El sistema debe ofrecer la creación automática del ítem utilizando los datos técnicos extraídos del PDF, quedando inicialmente con stock físico en cero, si el usuario acepta la advertencia de RF-05-a.
- RF-06: El sistema debe emitir una alerta informativa si el (Stock - Stock Comprometido) alcanza o es inferior al Punto de Pedido. Esto no impide que el proceso continúe dado que las compras están fuera del alcance actual.
- RF-07: Un usuario autenticado debe poder acceder a un listado de ordenes de trabajo, que permita filtrar por estado (vigente/cerrada)
  - RF-07-a: El sistema debe permitir buscar dentro del listado una orden de trabajo por código NEST (coincidencia parcial), en forma combinable con el filtro de estado.

### Taller
- RF-08: Un usuario autenticado debe poder escanear el código de barras de la orden de trabajo.
  - RF-08-a: El sistema debe mostrar en pantalla la orden de trabajo asociada al código escaneado.
  - RF-08-b: El sistema debe permitir opcionalmente cargar el código NEST de forma manual, como alternativa al escaneo por cámara.
- RF-09: El usuario debe poder finalizar la orden de trabajo pasando a estado "cerrada".
- RF-10: El sistema debe descontar del maestro de productos el stock previamente comprometido y el stock físico. La cantidad lo determina la multiplicidad.

*Si en la orden de trabajo se detallan recortes:*
  - RF-11-a: El sistema debe dar de alta el recorte en el maestro de producto si no existe un producto con el mismo material y espesor cuyas dimensiones se encuentren dentro del rango definido por el parámetro de tolerancia.
  - RF-11-b: El sistema debe aumentar el campo stock en la cantidad detallada si existe una coincidencia (material, espesor y dimensiones dentro del rango de tolerancia).

### Inventario
- RF-12: Un usuario autenticado debe poder crear un nuevo producto.
  - RF-12-a: El sistema debe rechazar el alta de un producto si ya existe otro con el mismo material, espesor y dimensiones (largo y ancho) exactos. Esta validación es independiente del margen de tolerancia (RF-17), que aplica a las búsquedas de coincidencia de los procesos de Oficina y Taller (RF-05, RF-11), no al alta manual desde Inventario.
- RF-13: El sistema debe registrar, al crear o editar un producto, los siguientes atributos: material (ej. SAE_1010, INOX), espesor (en mm), dimensiones (largo x ancho en mm), stock (cantidad física disponible) y Punto de pedido (valor umbral del stock para emisión de alertas).
- RF-14: El sistema debe generar automáticamente un Id único y secuencial para cada producto
- RF-15: El usuario autenticado debe poder Editar la información del producto, excepto el campo stock comprometido (lo realiza el proceso de finalización de orden de trabajo).
- RF-16: El usuario autenticado debe poder visualizar el listado de productos.

### Configuración del Sistema
- RF-17: El sistema debe contar con un apartado de configuración donde se defina el Margen de Tolerancia Dimensional (en mm). Valor por defecto: 1.0 mm.

### Seguridad y Acceso
- RF-18: El sistema debe presentar una pantalla de inicio para la autenticación de usuarios mediante Email y Contraseña.
  - RF-18-a: El sistema debe restringir el acceso a las funcionalidades únicamente a usuarios autenticados.
- RF-19: El sistema debe permitir el alta de nuevos usuarios (email y contraseña) de forma sencilla.
  - RF-19-a: El sistema debe otorgar, en esta etapa, acceso total a todos los módulos a todo usuario autenticado, dado que no existen roles ni permisos diferenciados.

## Requerimientos No Funcionales
- RNF-01: La extracción de datos del PDF debe tener una tasa de acierto superior al 98%.
- RNF-02: El procesamiento del PDF no debe demorar más de 10 segundos.
- RNF-03: El tiempo de respuesta para listados/búsquedas deberá ser menor a 2 segundos (p95).
- RNF-04: Las contraseñas deben almacenarse con hash seguro (bcrypt/argon2), nunca en texto plano.
- RNF-05: La sesión del usuario debe expirar tras 24 h de inactividad.
- RNF-06: Los códigos de barras generados para las órdenes de trabajo deben ser legibles a resoluciones de impresión estándar (300 DPI). El ancho de barra mínimo (X-dimension) no debe ser inferior a 0.3mm para garantizar la lectura con escáneres ópticos y cámaras de dispositivos móviles.

## Criterios de Aceptación
AC-01 (RF-01): Dado un archivo con extensión PDF válido, cuando el usuario lo sube al sistema, entonces el sistema debe aceptar la carga.

AC-02 (RF-01): Dado un archivo con una extensión distinta a PDF (ej: .xlsx o .jpg), cuando el usuario intenta subirlo, entonces el sistema debe rechazar la carga y mostrar un mensaje de error indicando que solo se admiten archivos PDF.

AC-03 (RF-02): Dado un archivo PDF de corte con campos "Multiplicidad: 1", "Dimensiones: 3000 x 1500", "Espesor: 2.100", "Material: SAE_1010" y "Tiempo de ejecución: 00.01:22", cuando el usuario lo sube al sistema, entonces el sistema debe extraer y mostrar esos valores exactos en los campos correspondientes para su validación.

AC-03-a (RF-02): Dado un archivo PDF de corte con un listado de piezas que incluye descripción y cantidad para cada ítem, cuando el usuario lo sube al sistema, entonces el sistema debe extraer cada pieza del listado junto con su cantidad correspondiente.

AC-04 (RF-02-a): Dado un ítem del listado de piezas con descripción "Saved scrap" y nombre técnico "800x400" en el campo 'Pieza', cuando el sistema procesa el archivo, entonces debe extraer 800 mm de largo y 400 mm de ancho como dimensiones del recorte.

AC-05 (RF-03): Dada la confirmación de los datos extraídos, cuando el usuario confirma la creación de la orden, entonces el sistema debe generar un código único secuencial NEST y asignarlo a la nueva orden de trabajo.

AC-06 (RF-04): Dada una orden de trabajo con datos confirmados, cuando el usuario finaliza la confirmación, entonces el sistema debe guardarla en la base de datos con estado "vigente".

AC-07 (RF-04-a): Dada una orden de trabajo guardada, cuando se confirma la orden, entonces el sistema debe imprimir un documento incluyendo el código de barras del código NEST y el detalle de las piezas. El código de barras debe ser decodificable por un lector estándar a resoluciones de impresión estándar (≥300 DPI) — no alcanza con que la imagen esté presente visualmente.

AC-08 (RF-05): Dada la confirmación de la orden de trabajo, cuando el sistema identifica el producto correspondiente en el maestro, entonces debe comprometer automáticamente el stock de chapa según la multiplicidad indicada.

AC-09 (RF-05-a): Dada la confirmación de la orden de trabajo, cuando el producto no existe en el maestro, entonces el sistema debe advertir al usuario de la ausencia del producto.

AC-10 (RF-05-b): Dada la advertencia de producto inexistente, cuando el usuario confirma la creación automática, entonces el sistema debe crear el ítem con los datos técnicos extraídos del PDF y stock físico en cero.

AC-11 (RF-06): Dado un producto con Stock=10 y Punto de Pedido=8, cuando se genera una orden que compromete 5 unidades, entonces el sistema debe mostrar un indicador visual de alerta en el listado, permitiendo continuar el proceso.

AC-12 (RF-07): Dado un listado de órdenes, cuando el usuario selecciona el filtro "Vigente", entonces solo deben visualizarse aquellas órdenes que aún no han sido escaneadas y cerradas en taller.

AC-13 (RF-07): Dado un listado de órdenes, cuando el usuario selecciona el filtro "Cerradas", entonces solo deben visualizarse aquellas órdenes finalizadas.

AC-14 (RF-07): Dado un listado de órdenes, cuando el usuario no seleccione ningún filtro, entonces se deben visualizar todas las ordenes.

AC-14-a (RF-07-a): Dado un listado de órdenes, cuando el usuario ingresa un texto en el buscador por código NEST, entonces el listado debe mostrar únicamente las órdenes cuyo código NEST contenga ese texto, respetando el filtro de estado activo.

AC-15 (RF-08 / RF-08-a): Dado que el usuario recibe una orden de trabajo, cuando escanea el código de barras NEST, entonces el sistema debe mostrar la orden asociada en pantalla.

AC-15-a (RF-08-b): Dado que el usuario no puede o prefiere no escanear, cuando ingresa el código NEST manualmente y confirma, entonces el sistema debe buscar y mostrar la orden asociada, igual que si lo hubiera escaneado.

AC-16 (RF-09): Dada una orden en estado "vigente", cuando el usuario confirma la finalización en la pantalla de taller, entonces el estado de la orden debe cambiar a "cerrada".

AC-17 (RF-10): Dado un escaneo exitoso, cuando el usuario finaliza el proceso de corte, entonces el sistema debe descontar del maestro de productos el stock comprometido y el stock físico, según la cantidad definida en el campo multiplicidad.

AC-18 (RF-11-a): Dado un sobrante de material detallado en el PDF sin coincidencia de producto existente (material, espesor y dimensiones dentro de tolerancia), cuando el usuario finaliza el proceso de corte, entonces el sistema debe dar de alta el recorte como nuevo registro en el maestro de producto.

AC-19 (RF-11-b): Dado un sobrante de material detallado en el PDF que coincide con un producto existente (mismo material, espesor y dimensiones dentro del margen de tolerancia), cuando el usuario finaliza el proceso de corte, entonces el sistema debe aumentar el stock de ese producto en la cantidad detallada.

AC-20 (RF-12): Dado un usuario autenticado en el módulo de Inventario, cuando completa el formulario de nuevo producto con datos válidos y confirma, entonces el sistema debe crear el producto en el maestro.

AC-20-a (RF-12-a): Dado que ya existe en el maestro un producto con un material, espesor, largo y ancho determinados, cuando el usuario intenta crear otro producto con exactamente los mismos valores en esos cuatro campos, entonces el sistema debe rechazar el alta e informar que ya existe un producto con esas características.

AC-21 (RF-14): Dado que el usuario crea un nuevo producto, cuando confirma el alta, entonces el sistema debe asignar automáticamente un Id único y secuencial.

AC-22 (RF-13): Dado que el usuario intenta confirmar el alta de un nuevo producto con algún campo obligatorio vacío (material, espesor, dimensiones, stock o punto de pedido), cuando envía el formulario, entonces el sistema debe rechazar el alta y señalar los campos faltantes.

AC-23 (RF-15): Dado que el usuario intenta editar un producto, cuando accede al formulario de edición, entonces el campo stock comprometido debe estar bloqueado para su edición.

AC-23-a (RF-15): Dado que el usuario edita un producto existente modificando un campo permitido (ej. punto de pedido) con un valor válido, cuando guarda los cambios, entonces el sistema debe persistir el nuevo valor y reflejarlo en el listado de productos.

AC-24 (RF-16): Dado un usuario autenticado en el módulo de Inventario, cuando accede a la sección de productos, entonces el sistema debe mostrar el listado completo de productos del maestro.

AC-25 (RF-17): Dado un usuario autenticado en el apartado de Configuración, cuando visualiza el Margen de Tolerancia Dimensional sin haberlo modificado previamente, entonces el sistema debe mostrar el valor por defecto de 1.0 mm.

AC-25-a (RF-17): Dado un usuario que modifica el Margen de Tolerancia Dimensional a un valor válido y lo guarda, cuando el sistema realiza una búsqueda de coincidencia de producto (RF-05 o RF-11), entonces debe utilizar el nuevo valor configurado en lugar del valor por defecto.

AC-26 (RF-18): Dado un usuario sin sesión iniciada, cuando accede a la URL del sistema, entonces el sistema debe mostrar la pantalla de login solicitando email y contraseña.

AC-27 (RF-18-a): Dado un usuario no autenticado, cuando intenta acceder a cualquier página del sistema, entonces el sistema debe redirigirlo al login.

AC-28 (RF-19): Dado un usuario que se quiere registrar, cuando el email ingresado ya pertenece a un usuario existente del sistema, entonces el sistema debe informar el error y rechazar el alta.

AC-28-a (RF-19): Dado un usuario que se quiere registrar, cuando ingresa un email no registrado previamente junto con una contraseña válida y confirma, entonces el sistema debe crear la cuenta exitosamente.

AC-29 (RF-19-a): Dado un usuario autenticado, cuando accede a cualquier módulo del sistema (Oficina, Taller, Inventario, Configuración), entonces el sistema debe conceder el acceso sin restricciones adicionales de rol o permiso.

## Fuera de Alcance
Órdenes de compra. Procesos de facturación y generación de remitos. El sistema se limita a la alerta informativa de reposición.

Configuración de roles y permisos de usuarios.

Aislamiento de datos por usuario: todos los usuarios autenticados comparten el mismo espacio de datos (workspace compartido), consistente con RF-19-a.

## Riesgos y Dependencias
- Riesgo:
  - Captura de datos erróneos → mitigación: permitir al usuario revisar, validar y editar antes de confirmar.
  - Duplicidad de productos por variaciones decimales mínimas en las dimensiones → mitigación: utilizar un margen de tolerancia en las búsquedas por dimensiones.
- Dependencia:
  - El sistema requiere una herramienta capaz de procesar archivos en formato PDF y extraer los datos necesarios.
  - El sistema requiere un generador y lector de códigos de barras formato CODE_128.
