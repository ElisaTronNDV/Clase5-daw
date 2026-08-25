# PRD FEAT-002: Gestión de inventario (CRUD de productos)

| Field | Value |
|-------|-------|
| Ticket | FEAT-002 |
| Tracker | none |
| Date | 2026-08-25 |
| PRD loops | 0 |

## Context and Problem

El PRD-001 (`docs/daw/prd/prd-001-captura-corte-inventario.md`) define el módulo de Inventario
(RF-12 a RF-16) como el maestro de productos (chapas y recortes) que los módulos de Oficina y
Taller van a consumir para comprometer y descontar stock. Ese maestro todavía no existe: sin él, no
hay nada contra qué buscar coincidencias por material/espesor/dimensiones, ni un lugar donde dar de
alta manualmente un producto. Este ticket construye ese maestro de forma autónoma, sin depender de
que Oficina o Taller estén implementados.

## Goals

Permitir a un usuario autenticado dar de alta, editar y consultar productos (chapas) en el maestro
de inventario, con las validaciones que evitan duplicados y datos inconsistentes, y dejar reservado
el campo `stock_comprometido` que usará el futuro módulo de Oficina.

## Functional Requirements

- FR-01: El sistema debe permitir a un usuario autenticado crear un nuevo producto ingresando
  material, espesor, largo, ancho, stock y punto de pedido.
- FR-02: El sistema debe rechazar el alta de un producto si ya existe otro con el mismo material
  (sin distinguir mayúsculas/minúsculas), espesor, largo y ancho exactos.
- FR-03: El sistema debe validar que espesor, largo, ancho, stock y punto de pedido sean valores
  numéricos mayores a cero, y que ningún campo obligatorio quede vacío, tanto al crear como al
  editar.
- FR-04: El sistema debe asignar automáticamente un id único y secuencial a cada producto creado.
- FR-05: El sistema debe inicializar el stock comprometido en 0 al crear un producto.
- FR-06: El sistema debe permitir a un usuario autenticado editar material, espesor, largo, ancho,
  stock y punto de pedido de un producto existente, aplicando las mismas validaciones que en el
  alta.
- FR-07: El sistema debe impedir la edición del campo stock comprometido, mostrándolo como de solo
  lectura.
- FR-08: El sistema debe permitir a un usuario autenticado visualizar el listado completo de
  productos del maestro.
- FR-09: El sistema debe rechazar cualquier operación sobre productos (crear, editar, listar) si el
  usuario no está autenticado.

## Non-Functional Requirements

- NFR-01: El tiempo de respuesta para crear, editar y listar productos debe ser menor a 2 segundos
  (p95), consistente con RNF-03 de PRD-001.

## Acceptance Criteria

- AC-01 (FR-01, FR-04): WHEN un usuario autenticado envía el formulario de alta con material,
  espesor, largo, ancho, stock y punto de pedido válidos, THE sistema SHALL crear el producto
  asignándole un id único y secuencial.
- AC-02 (FR-02): IF el usuario intenta crear un producto con el mismo material (sin distinguir
  mayúsculas/minúsculas), espesor, largo y ancho que un producto ya existente, THEN THE sistema
  SHALL rechazar el alta e informar que ya existe un producto con esas características.
- AC-03 (FR-03): IF el usuario intenta confirmar el alta o la edición con material, espesor, largo,
  ancho, stock o punto de pedido vacíos, THEN THE sistema SHALL rechazar la operación y señalar los
  campos faltantes.
- AC-04 (FR-03): IF el usuario ingresa un valor menor o igual a cero en espesor, largo, ancho,
  stock o punto de pedido, THEN THE sistema SHALL rechazar la operación e informar que el valor
  debe ser mayor a cero.
- AC-05 (FR-05): WHEN se crea un producto, THE sistema SHALL inicializar su stock comprometido en
  0.
- AC-06 (FR-06): WHEN un usuario autenticado edita un producto existente modificando material,
  espesor, largo, ancho, stock o punto de pedido con valores válidos, THE sistema SHALL persistir
  los cambios y reflejarlos en el listado.
- AC-07 (FR-07): WHEN un usuario accede al formulario de edición de un producto, THE sistema SHALL
  mostrar el campo stock comprometido como de solo lectura, sin permitir su modificación.
- AC-08 (FR-08): WHEN un usuario autenticado accede a la sección de productos, THE sistema SHALL
  mostrar el listado completo de productos con material, espesor, largo, ancho, stock, stock
  comprometido y punto de pedido.
- AC-09 (FR-09): IF un usuario no autenticado intenta crear, editar o listar productos, THEN THE
  sistema SHALL rechazar la petición con 401.

## Out of Scope

- Eliminar o dar de baja productos (no hay ningún RF de baja en PRD-001; confirmado explícitamente
  con el usuario).
- Descuento de stock por cierre de orden de trabajo (Taller, RF-10) — ahí el stock SÍ puede quedar
  en negativo, a diferencia de la validación de este ticket (que exige valores > 0 al crear/editar
  manualmente). Es un flujo distinto, de un módulo futuro.
- Alta automática de productos desde Oficina con stock físico en cero (RF-05-b) — ese flujo lo
  implementa el ticket de Oficina, no este.
- Compromiso de stock al confirmar una orden de trabajo (RF-05) — este ticket solo deja el campo
  `stock_comprometido` listo (inicializado en 0, de solo lectura); no lo modifica nadie todavía.
- Filtros o búsqueda en el listado de productos (RF-16 no los pide) — se agregarían en una
  iteración futura si hace falta.
- El Margen de Tolerancia Dimensional (RF-17) — la búsqueda de coincidencias de este ticket
  (RF-12-a) es por igualdad exacta de material/espesor/dimensiones, no por tolerancia; el margen
  solo aplica a las búsquedas de Oficina/Taller (aclarado explícitamente en PRD-001).

## Risks and Mitigations

- Riesgo: al ser `material` texto libre, variantes con espacios extra o tildes distintas podrían no
  detectarse como el mismo material en el chequeo de duplicados (FR-02).
  Mitigación: normalizar (trim + comparación case-insensitive) antes de comparar en el backend.
- Riesgo: exponer `stock_comprometido` antes de que el módulo de Oficina exista podría confundir al
  usuario si lo ve en el listado sin contexto de para qué sirve.
  Mitigación: mostrarlo en el listado y como solo-lectura en la edición, sin ningún flujo que lo
  modifique todavía — su valor será siempre 0 hasta que Oficina se implemente.

## Dependencies

- Depende de la autenticación JWT ya implementada en FEAT-001: todos los endpoints de este módulo
  requieren un usuario autenticado, sin restricción de rol (RF-19-a de PRD-001).
- Deja preparado el campo `stock_comprometido` que usará el futuro módulo de Oficina (RF-05) para
  comprometer stock al confirmar órdenes de trabajo.
- Referencia: `docs/daw/prd/prd-001-captura-corte-inventario.md` (RF-12 a RF-16, AC-20 a AC-24).
