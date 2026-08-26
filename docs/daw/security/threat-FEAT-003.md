# Threat Model FEAT-003: Configuración del sistema (margen de tolerancia dimensional)

| Field | Value |
|-------|-------|
| Ticket | FEAT-003 |
| Date | 2026-08-26 |
| Componentes analizados | `GET/PUT /api/configuracion`, `configuracion_service.py`, tabla `configuracion`, `configuracion.ts`, `configuracion.service.ts` |

## Componentes y su rol (F-TM-01, F-TM-06)

| Componente | Rol |
|---|---|
| `GET /api/configuracion` | Lee el margen de tolerancia dimensional actual (o el default 1.0 si nunca se configuró) |
| `PUT /api/configuracion` | Actualiza el margen — único punto de entrada de input de usuario de este ticket |
| `configuracion_service.py` | Capa de negocio: garantiza que la tabla `configuracion` nunca tenga más de una fila (upsert) |
| Tabla `configuracion` (SQLite) | Persistencia — mismo motor y patrón de acceso que `users`/`products` |
| `configuracion.ts` / `configuracion.service.ts` | Cliente Angular — arma el request, nunca llama `HttpClient` directo desde el componente |

## Límites de confianza (F-TM-02)

Reutiliza los mismos límites ya declarados en `docs/daw/security/threat-FEAT-001.md` y
`threat-FEAT-002.md`:
1. **Navegador ↔ API backend** — toda request a `/api/configuracion/*` cruza este límite; se protege
   con el mismo `get_current_user` (Bearer JWT) que ya audita FEAT-001.
2. **API backend ↔ SQLite** — se decide acá si la query está parametrizada.

No hay límites nuevos: este ticket no agrega autenticación propia ni un servicio externo.

## Análisis STRIDE por componente

### `PUT /api/configuracion` (input de usuario)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Spoofing | N/A — cubierto por `get_current_user`, ya mitigado en FEAT-001 | — | — | Reutiliza la mitigación existente |
| Tampering | Inyección SQL | Low | Critical | SQLAlchemy ORM, sin SQL crudo — mismo patrón que `users`/`products` |
| Tampering | 🟢 El PRD no define un límite superior para el margen — un valor absurdamente grande (ej. 1e9) pasaría `Field(gt=0)` | Low | Low | Aceptado: no hay ningún consumidor todavía (Oficina/Taller no existen) que pueda verse afectado por un valor extremo; ya documentado como fuera de alcance en el PRD. Si Oficina/Taller lo consumen en un ticket futuro, ese ticket es quien debe decidir si necesita un límite superior según su propio caso de uso — no corresponde inventarlo acá sin ese contexto |
| Repudiation | Sin registro de quién modificó el margen y cuándo | — | — | No es una regresión de este ticket: ningún módulo del proyecto audita todavía (consistente con FEAT-001/002); fuera de alcance de este PRD (sección "Out of Scope") |
| Information Disclosure | N/A — el valor es un dato de negocio, no PII/credencial | — | — | — |
| Denial of Service | N/A — una sola fila, sin llamadas externas, mismo perfil que auth/products | — | — | NFR-01 (<2s p95) ya cubierto por diseño |
| Elevation of Privilege | Sin RBAC — cualquier usuario autenticado puede modificar la configuración global | — | — | **Accepted risk heredado**, ya documentado en `threat-FEAT-001.md`/`threat-FEAT-002.md` y en PRD-001 ("Fuera de Alcance: Configuración de roles y permisos") — coherente con que sea, por diseño, una configuración de workspace compartido (RF-19-a), no por usuario |

### `GET /api/configuracion` (lectura)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Information Disclosure | N/A — dato de negocio no sensible, compartido por diseño | — | — | — |

### `configuracion_service.py` — garantía de singleton (upsert)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Tampering (integridad de datos, no exploit) | 🟡 Si el upsert se implementa como "buscar la primera fila e insertar si no existe" sin una clave fija, dos requests `PUT` concurrentes podrían insertar dos filas en una condición de carrera (SQLite sin lock explícito), y `get_margen_tolerancia` empezaría a leer una fila arbitraria | Low (single-workspace, tráfico interno bajo, ya aceptado en el PRD como riesgo de bajo impacto) | Low | **Mitigación incorporada al spec** (no es solo un riesgo aceptado, es gratis de resolver): la fila usa una clave fija conocida (`id=1`) en vez de "la primera fila por orden de inserción" — `get_margen_tolerancia` hace `db.get(Configuracion, 1)`, `update_margen_tolerancia` hace lo mismo y crea la fila con `id=1` si no existe. Esto elimina la ambigüedad sin agregar ningún control de concurrencia adicional (no lo pide el PRD, que ya documenta el riesgo residual de carrera como aceptado) |

### Frontend (`configuracion.ts`, `configuracion.service.ts`)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Tampering (XSS) | N/A — sin `[innerHTML]` planeado, binding por defecto de Angular sanitiza | — | — | Mismo patrón ya limpio en SAST de FEAT-001/FEAT-002 |
| Tampering (CSRF) | N/A — auth Bearer, no cookies de sesión | — | — | Igual que FEAT-001/FEAT-002 |

## Clasificación de datos sensibles (F-TM-05)

`margen_tolerancia_dimensional`: dato de negocio (parámetro de configuración numérico), **no PII, no
credenciales, no financiero**. No requiere cifrado adicional (F-TM-07 no aplica).

## Mitigaciones a incorporar en la spec

1. **Clave fija `id=1` para la fila de configuración** (en vez de "primera fila por orden de
   inserción") — elimina la ambigüedad de concurrencia del upsert sin agregar control de concurrencia
   adicional, que el PRD no pide.

## Resultado

```
┌─────────────────────────────────────────────────────────┐
│  /daw-threat-modeling — PASSED                           │
├─────────────────────────────────────────────────────────┤
│  Attack surfaces identified: 2 (GET, PUT)                │
│  Trust boundaries declared: 2 (reutilizados de FEAT-001/002) │
│  Risks: C:0 H:0 M:0 L:2 (valor sin límite superior,       │
│  ambigüedad de upsert sin clave fija — ambos de bajo       │
│  impacto, el segundo se resuelve gratis en el diseño)      │
│  Report: docs/daw/security/threat-FEAT-003.md            │
└─────────────────────────────────────────────────────────┘
```
