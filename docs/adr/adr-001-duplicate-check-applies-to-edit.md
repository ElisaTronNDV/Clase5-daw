# ADR-001: El chequeo de duplicados de producto aplica también al editar

| Field | Value |
|-------|-------|
| Date | 2026-08-25 |
| Ticket | FEAT-002 |
| Status | Accepted |

## Context

El PRD-001 (RF-12-a) y el PRD de FEAT-002 (FR-02/AC-02) redactan el chequeo de duplicados
(mismo material + espesor + largo + ancho) como una validación del **alta** de producto. El texto
no dice qué debe pasar si, al **editar** un producto existente, los nuevos valores terminan
coincidiendo con otro producto ya existente en el maestro.

## Options considered

### Option 1: Validar duplicados solo al crear (lectura literal del PRD)
- **Pros:** implementación más simple; se ciñe exactamente a lo que el texto del PRD dice.
- **Cons:** permite terminar con dos productos con los mismos valores si se llega a esa coincidencia
  editando en vez de creando — el objetivo del chequeo (mantener el maestro sin duplicados) queda
  incompleto.

### Option 2: Validar duplicados también al editar, excluyendo el propio id
- **Pros:** el maestro de productos queda consistente sin duplicados sin importar por qué camino se
  llega a la coincidencia (alta o edición); mismo mensaje de error que en el alta, sin sorpresas para
  el usuario.
- **Cons:** una regla más para implementar y testear (excluir el propio registro al comparar, para
  no marcar un producto como "duplicado de sí mismo").

## Decision

Se adopta la **Opción 2**. Confirmado explícitamente con el usuario durante PLAN: el objetivo de
FR-02 es evitar duplicados en el maestro, no solo en el momento del alta — dejarlo sin validar en la
edición sería una brecha que contradice el propósito de la regla, aunque el texto original del PRD
no lo mencionara explícitamente.

## Consequences

- `product_service.update_product` reutiliza el mismo chequeo de `create_product`
  (`_normalize_material` + comparación de espesor/largo/ancho), excluyendo el propio `id` de la
  búsqueda.
- `PUT /api/products/{id}` puede devolver `400` con el mismo mensaje que `POST /api/products`.
- Tests nuevos en `spec-FEAT-002.md` Block 1: `test_update_product_duplicate_against_other_product_raises`
  y `test_update_product_no_false_positive_against_itself`.
- Sin límite: no había ningún consumidor del comportamiento anterior (el endpoint todavía no existe),
  así que no hay impacto de compatibilidad hacia atrás que considerar.
