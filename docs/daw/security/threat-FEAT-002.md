# Threat Model FEAT-002: Gestión de inventario (CRUD de productos)

| Field | Value |
|-------|-------|
| Ticket | FEAT-002 |
| Date | 2026-08-25 |
| Componentes analizados | `POST/GET /api/products`, `GET/PUT /api/products/{id}`, `product_service.py`, tabla `products`, `product-form.ts`, `product.service.ts` |

## Componentes y su rol (F-TM-01, F-TM-06)

| Componente | Rol |
|---|---|
| `POST /api/products` | Crea un producto — primer punto donde entra input de usuario no confiable a este módulo |
| `PUT /api/products/{id}` | Edita un producto existente — mismo input, más el riesgo de sobre-escribir campos que no debería |
| `GET /api/products`, `GET /api/products/{id}` | Lectura — expone el maestro completo a cualquier usuario autenticado (por diseño, RF-19-a) |
| `product_service.py` | Capa de negocio: normalización de `material`, chequeo de duplicados, construcción del modelo |
| Tabla `products` (SQLite) | Persistencia — mismo motor y mismo patrón de acceso que `users` en FEAT-001 |
| `product-form.ts` / `product.service.ts` | Cliente Angular — arma el request, nunca llama `HttpClient` directo desde el componente |

## Límites de confianza (F-TM-02)

Reutiliza los mismos límites ya declarados en `docs/daw/security/threat-FEAT-001.md`:
1. **Navegador ↔ API backend** — toda request a `/api/products/*` cruza este límite; se protege con
   el mismo `get_current_user` (Bearer JWT) que ya audita FEAT-001.
2. **API backend ↔ SQLite** — se decide acá si la query está parametrizada.

No hay límites nuevos: este ticket no agrega autenticación propia ni un servicio externo — reutiliza
el mecanismo de FEAT-001 tal cual.

## Análisis STRIDE por componente

### `POST /api/products` y `PUT /api/products/{id}` (input de usuario)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Spoofing | N/A — cubierto por `get_current_user`, ya mitigado en FEAT-001 | — | — | Reutiliza la mitigación existente (algoritmo HS256 fijado) |
| Tampering | 🟠 Un cliente envía `stock_comprometido` en el body de `POST`/`PUT` intentando setearlo directamente — es el único campo que un módulo futuro (Oficina) debería poder modificar, nunca el usuario a mano | Medium | High | **Mitigación obligatoria**: `ConfigDict(extra="forbid")` en **`ProductCreate` Y `ProductUpdate`** (el plan original solo lo tenía en Update — se corrige acá) → 422 ante cualquier campo no reconocido |
| Tampering | Inyección SQL | Low | Critical | SQLAlchemy ORM, sin SQL crudo — mismo patrón que `users` |
| Repudiation | Sin registro de quién creó/editó un producto (`created_by`/`updated_by`) | — | — | No es una regresión de este ticket: ningún módulo del proyecto audita todavía (consistente con FEAT-001); fuera de alcance de este PRD |
| Information Disclosure | N/A — `ProductOut` solo expone datos de negocio, sin PII | — | — | — |
| Denial of Service | N/A — operación de una sola fila, sin llamadas externas, mismo perfil que los endpoints de auth | — | — | NFR-01 (<2s p95) ya cubierto por diseño |
| Elevation of Privilege | Sin RBAC — cualquier usuario autenticado puede crear/editar cualquier producto | — | — | **Accepted risk heredado, ya documentado en `threat-FEAT-001.md`** ("Elevation of Privilege | N/A — no hay roles/permisos (RF-19-a)") y en PRD-001 ("Fuera de Alcance: Configuración de roles y permisos"). No se re-evalúa acá porque es una decisión de producto, no un gap de este ticket. |

### `GET /api/products`, `GET /api/products/{id}` (lectura)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Information Disclosure | N/A — datos de negocio compartidos por diseño (workspace único, RF-19-a) | — | — | — |
| Elevation of Privilege (IDOR) | N/A — no hay concepto de "dueño" del producto; cualquier usuario autenticado puede ver cualquier id, por diseño | — | — | Mismo accepted risk que arriba |

### `product_service.py` — normalización y chequeo de duplicados

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Tampering (integridad de datos, no exploit) | 🟢 Si la normalización (`.strip().lower()` de `material`) no se centraliza, create y update podrían aplicar el chequeo de forma inconsistente y dejar pasar duplicados | Low | Low | Un único helper `_normalize_material()` en `product_service.py`, usado por `create_product` y `update_product` |

### Frontend (`product-form.ts`, `product.service.ts`)

| STRIDE | Riesgo | Likelihood | Impact | Mitigación |
|---|---|---|---|---|
| Tampering (XSS) | N/A — sin `[innerHTML]` planeado, binding por defecto de Angular sanitiza | — | — | Mismo patrón ya limpio en SAST de FEAT-001 |
| Tampering (CSRF) | N/A — auth Bearer, no cookies de sesión | — | — | Igual que FEAT-001 |

## Clasificación de datos sensibles (F-TM-05)

`material`, `espesor`, `largo`, `ancho`, `stock`, `stock_comprometido`, `punto_pedido`: datos de
negocio (inventario de chapas), **no PII, no credenciales, no financieros**. No requieren
cifrado adicional (F-TM-07 no aplica — no hay PII ni credenciales nuevas en este ticket).

## Mitigaciones a incorporar en la spec

1. **`ConfigDict(extra="forbid")` en `ProductCreate` Y `ProductUpdate`** (corrección respecto al
   plan presentado: originalmente solo se había previsto en Update) — bloquea que `stock_comprometido`
   se setee desde el cliente en cualquiera de los dos endpoints.
2. Helper único de normalización de `material` (`.strip().lower()`) compartido entre `create_product`
   y `update_product`.

## Resultado

```
┌─────────────────────────────────────────────────────────┐
│  /daw-threat-modeling — PASSED                           │
├─────────────────────────────────────────────────────────┤
│  Attack surfaces identified: 4 (POST, PUT, GET, GET/{id})│
│  Trust boundaries declared: 2 (reutilizados de FEAT-001) │
│  Risks: C:0 H:0 M:0 L:2 (normalización, sin auditoría)    │
│  🟠 1 mitigación obligatoria (extra="forbid" en ambos      │
│     schemas) — ya incorporada a la spec antes de escribir │
│     código, no queda como riesgo abierto                  │
│  Report: docs/daw/security/threat-FEAT-002.md            │
└─────────────────────────────────────────────────────────┘
```
