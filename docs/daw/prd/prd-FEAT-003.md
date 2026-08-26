# PRD FEAT-003: Configuración del sistema (margen de tolerancia dimensional)

| Field | Value |
|-------|-------|
| Ticket | FEAT-003 |
| Tracker | none |
| Date | 2026-08-26 |
| PRD loops | 1 |

## Context and Problem

`docs/daw/prd/prd-001-captura-corte-inventario.md` (RF-17) exige un apartado de Configuración donde
se defina el Margen de Tolerancia Dimensional: el valor en mm que Oficina y Taller usarán para
matchear productos por dimensiones (RF-05, RF-11) en lugar de exigir una coincidencia exacta. Ese
valor no debe quedar hardcodeado en el código (regla explícita de `AGENTS.md`, sección "What NOT to
do in this project") ni vivir solo en memoria: tiene que persistir server-side para que cualquier
módulo futuro lo lea de un único lugar.

Oficina y Taller (los módulos que efectivamente van a *usar* este valor para buscar coincidencias)
todavía no existen en el sistema. Este ticket construye el punto único de configuración y su
persistencia — el consumo del valor en búsquedas de coincidencia queda para cuando esos módulos se
implementen, mismo patrón que `stock_comprometido` en FEAT-002 (se protege y se deja listo antes de
que exista quien lo use).

## Goals

- Un usuario autenticado puede ver y modificar el Margen de Tolerancia Dimensional desde un apartado
  de Configuración.
- El valor persiste server-side, es único y global (workspace compartido, consistente con RF-19-a —
  no hay configuración por usuario).
- Si nunca se configuró, el sistema expone el valor por defecto (1.0 mm) sin necesitar una fila
  precargada en la base de datos.

## Functional Requirements

- FR-01: Un usuario autenticado debe poder obtener el valor actual del Margen de Tolerancia
  Dimensional.
- FR-02: Si el valor nunca fue configurado, el sistema debe devolver el valor por defecto (1.0 mm)
  sin requerir un registro previo en la base de datos.
- FR-03: Un usuario autenticado debe poder actualizar el Margen de Tolerancia Dimensional a un nuevo
  valor.
- FR-04: El sistema debe rechazar una actualización cuyo valor no sea un número positivo (> 0).
- FR-05: El valor configurado debe persistir server-side y ser el mismo para todos los usuarios
  autenticados (configuración global, no por usuario).
- FR-06: Todas las operaciones de este módulo requieren autenticación.

## Non-Functional Requirements

- NFR-01: El tiempo de respuesta de obtener y actualizar el valor de configuración debe ser menor a
  2 segundos (p95), consistente con RNF-03 del PRD-001.

## Acceptance Criteria

- AC-01 (FR-01, FR-02): WHEN un usuario autenticado abre el apartado de Configuración sin haber
  modificado antes el Margen de Tolerancia Dimensional, THE system SHALL mostrar el valor por
  defecto de 1.0 mm.
- AC-02 (FR-03, FR-05): WHEN un usuario autenticado actualiza el Margen de Tolerancia Dimensional a
  un valor numérico positivo válido y confirma, THE system SHALL persistir el nuevo valor.
- AC-03 (FR-04): IF un usuario autenticado intenta guardar un valor menor o igual a 0, THEN THE
  system SHALL rechazar la actualización y mostrar un error de validación, sin modificar el valor
  persistido.
- AC-04 (FR-04): IF un usuario autenticado intenta guardar un valor no numérico o un campo vacío,
  THEN THE system SHALL rechazar la actualización y mostrar un error de validación.
- AC-05 (FR-01, FR-05): WHEN un usuario autenticado vuelve a abrir el apartado de Configuración
  después de haber guardado un valor previamente, THE system SHALL mostrar ese último valor
  guardado, no el valor por defecto.
- AC-06 (FR-06): IF un usuario no autenticado intenta obtener o actualizar el Margen de Tolerancia
  Dimensional, THEN THE system SHALL responder con un error de autenticación (401) sin exponer ni
  modificar el valor.

## Out of Scope

- El consumo real del Margen de Tolerancia Dimensional en búsquedas de coincidencia de producto
  (RF-05, RF-11) — depende de Oficina y Taller, que todavía no existen. Este ticket solo expone y
  persiste el valor.
- Historial de cambios o auditoría de quién modificó el valor y cuándo — no lo pide el PRD-001 y no
  hay ningún otro módulo del proyecto que audite cambios todavía (mismo criterio ya documentado en
  `docs/daw/security/threat-FEAT-001.md`).
- Cualquier otro parámetro de configuración además del Margen de Tolerancia Dimensional — RF-17 es
  el único requerimiento de Configuración declarado en el PRD-001; no se agregan campos
  especulativos.
- Configuración por usuario o por rol — el PRD-001 establece un workspace compartido (RF-19-a), sin
  roles ni permisos diferenciados.

## Risks and Mitigations

- Riesgo: que la validación del valor (> 0) se implemente solo en el frontend y un cliente pueda
  enviar un valor inválido directo a la API → Mitigación: la validación se aplica siempre
  server-side (AC-03, AC-04), el frontend es una ayuda de UX, no la única barrera.
- Riesgo: al ser una configuración global sin control de concurrencia, dos usuarios podrían
  sobrescribirse el valor uno al otro → Mitigación: aceptado como riesgo de bajo impacto, consistente
  con el modelo de workspace compartido sin aislamiento por usuario ya definido en el PRD-001; no se
  implementa optimistic locking en este ticket.

## Dependencies

Ninguna — módulo independiente de Oficina/Taller (que todavía no existen) e independiente de
Inventario (FEAT-002). Reutiliza el mecanismo de autenticación de FEAT-001 (`get_current_user`).
