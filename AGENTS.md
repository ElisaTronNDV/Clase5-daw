# AGENTS.md — project context

> **DAW template.** Fill in the `[...]` with what is true of YOUR project and delete what does not
> apply. This file describes **the project**; **the process** is DAW's job (phases, gates, when to
> test, when to commit). Do not mix the two: process rules written here compete with the pipeline's.
>
> It is **tool-agnostic on purpose**: Claude Code reads it through the import in `CLAUDE.md`, Codex
> CLI, Copilot CLI, Cursor and OpenCode read it directly, and Gemini CLI gets it through
> `GEMINI.md`. The same file serves whichever tool you open the repo with — which is the point:
> porting the pipeline to another tool must not mean rewriting what your project is.

---

## Language

**Always respond in the language the user writes in.** Write every artifact you produce — PRDs,
specs, ADRs, reports, commit messages, status lines — in that same language, regardless of the
language these instructions are written in.

If this project has a fixed working language, state it here and use it instead:

> Working language: `Spanish — write all artifacts in Spanish`

---

## What this project is

DyP LaserCore automatiza la captura de datos del archivo de corte (PDF) para generar códigos NEST,
controlar stock de chapas y dar de alta recortes sobrantes en el inventario. Es para DyP, una
empresa de procesamiento de chapas metálicas (corte láser, plegado, panelado y soldadura), que hoy
depende de procesos manuales de carga y codificación que generan errores constantes en el inventario.

**Reference PRD:** `docs/daw/prd/prd-001-captura-corte-inventario.md`

---

## Stack

**This is the only place the stack lives.** DAW reads it from here and generates no derived file.
Fill it in even if the repo is empty: without a stack there is nothing to plan or implement against.

If the repo already has code and this section is empty, DAW will detect the stack from your config
files and **propose the text for you to paste here**. You always confirm it.

Proyecto con dos stacks (backend + frontend separados en `backend/` y `frontend/`):

| Field | Value |
|-------|-------|
| Language | Python 3.11 (backend) · TypeScript ~6.0 (frontend, requerido por Angular 22) |
| Runtime | Node.js ^22.22.3 (o ^24.15.0 / ^26.0.0) — Angular 22 dropeó soporte de Node 20 |
| Framework | FastAPI (backend) · Angular 22 + Bootstrap 5 (frontend) |
| Database | SQLite (SQLAlchemy ORM) |
| Test runner | pytest (backend) · `ng test` (frontend) — ver nota sobre Karma/Vitest abajo |
| Linter / formatter | N/A — no configurado aún (ni ESLint/Prettier ni ruff/black) |
| Package manager | pip (backend) · npm (frontend) |

**Librerías clave:**
- `pdfplumber` — extracción de datos del PDF de corte
- `python-barcode` + `pyzbar` — generación y verificación de código de barras
- `@zxing/ngx-scanner@^22.0.0` — escaneo de código de barras desde el frontend (Clase4 usaba
  `^18.0.1`; el paquete versiona en paralelo a Angular, así que hay que subirlo a la v22 junto con
  el resto — recién se publicó compatible el 2026-06-29)
- `passlib[bcrypt]` — hash de contraseñas (RNF-04)
- `python-jose` — JWT / sesión con expiración de 24 h (RNF-05)

**Nota de migración Angular 18 → 22:**
- Angular 21+ pasó a zoneless + Vitest por defecto, pero `zone.js` y Karma/Jasmine (como en Clase4)
  siguen soportados por compatibilidad hacia atrás — no es necesario migrar el estilo de testing
  para que el proyecto funcione, pero es la ruta "legacy".
- Bootstrap 5 se usa como CSS/JS plano (sin `ng-bootstrap`), así que es agnóstico a la versión de
  Angular — no hay incompatibilidad ahí.
- El resto de paquetes `@angular/*` deben ir todos a `^22.0.0` en conjunto (no mezclar versiones
  entre ellos).

---

## Architecture conventions

**DAW validates your code against this section** during the CODE phase, via `daw-validate-arch`.
Leave it empty and that validation has nothing to compare against, so it stops being worth running.

- **Folder structure (backend):** `backend/app/` dividido en `api/` (routers), `core/` (config,
  seguridad), `db/` (sesión), `models/` (SQLAlchemy), `schemas/` (Pydantic), `services/` (lógica de
  negocio). Tests en `backend/tests/` separados en `contract/`, `integration/`, `unit/`, `performance/`.
- **Folder structure (frontend):** `frontend/src/app/<feature>/` por módulo funcional (`auth`,
  `home`, `inventario`, `oficina`, `taller`, `configuracion`), más `shared/` para lo común entre
  módulos.
- **Layer separation:** los routers de `api/` no acceden a la base de datos directamente; la lógica
  vive en `services/` y el acceso a datos en `models/` vía SQLAlchemy. El frontend no llama la API
  directo desde los componentes sin pasar por un servicio Angular.
- **Error handling:** excepciones tipadas del dominio; nunca un `except` silencioso (ver
  `test_manejo_excepciones.py` como referencia de contrato).
- **Naming:** archivos backend en snake_case; componentes/servicios Angular en kebab-case de archivo
  y PascalCase de clase (convención estándar del Angular CLI).
- **Dependencies:** no agregar librerías nuevas sin justificarlas en la spec.

---

## Code conventions

- No hardcodear el margen de tolerancia dimensional ni otros parámetros de configuración: deben
  leerse desde `configuracion` (ver RF-17), nunca quemados en el código.
- Las API keys y secretos se leen solo de variables de entorno (`.env`, nunca versionado).
- Comentarios solo cuando el *por qué* no es obvio desde el código.

---

## What NOT to do in this project

This section is worth its weight in gold: it is where the scars go, the things that already went
wrong once.

- No confirmar ni persistir una orden de trabajo sin que el usuario revise y valide/edite los datos
  extraídos del PDF (mitigación del riesgo de captura errónea).
- No almacenar contraseñas en texto plano; usar hash seguro (bcrypt/argon2) y asegurar que las API
  keys se lean solo de variables de entorno.
- No hardcodear el margen de tolerancia dimensional: debe leerse de la configuración (default 1.0 mm,
  RF-17), no quemarlo en el código.
- No implementar generación de órdenes de compra, proceso de facturación ni generación de remitos
  (fuera de alcance).
- No dar por buena la generación de un código de barras solo porque produce una imagen: verificar que
  decodifica con un lector independiente (ej. zbar/pyzbar) a resolución de impresión típica
  (≥300 DPI, ver RNF-06). Un `module_width` por debajo de ~0.3mm, o forzar un ancho/alto de imagen
  que no respete la relación de aspecto real, lo vuelve ilegible aunque se vea bien en pantalla.
- Los componentes de escaneo de código de barras (ej. ZXing/ngx-scanner) traen su propio default de
  formato soportado (típicamente solo QR) — configurar siempre explícitamente el/los formato(s)
  esperado(s) (ej. CODE_128 para los códigos NEST), o el scanner nunca va a detectar nada aunque la
  cámara y los permisos funcionen bien.

---

## Domain glossary

The terms specific to your product, so the agent uses them correctly instead of inventing synonyms.

- **NEST:** código único secuencial que identifica una orden de trabajo, generado por el sistema al
  confirmar la carga del archivo de corte.
- **Archivo de corte:** PDF generado por el software CAD/CAM Salvagnini con los datos de una orden
  (Datos Generales, Datos de Elaboración, Datos de Producción y listado de Piezas).
- **Multiplicidad:** cantidad de repeticiones del patrón de corte sobre la chapa; determina la
  cantidad de stock a comprometer/descontar.
- **Saved scrap:** ítem del listado de piezas cuyo nombre técnico (ej. "800x400") indica las
  dimensiones de un recorte sobrante a dar de alta en inventario.
- **Margen de Tolerancia Dimensional:** valor en mm (default 1.0) configurable, usado para matchear
  dimensiones al buscar/crear productos por coincidencia (no aplica al alta manual desde Inventario).
- **Stock comprometido:** cantidad reservada de un producto al confirmar una orden en Oficina, antes
  de descontarse físicamente al cerrar la orden en Taller.
- **Punto de pedido:** umbral de stock por producto que dispara una alerta informativa (no bloquea
  el proceso).
- **Orden de trabajo:** entidad con estado "vigente" (creada en Oficina) o "cerrada" (finalizada en
  Taller).

---

> ℹ️ **What does NOT belong in this file, because DAW provides it:** the order work happens in, when
> the spec gets written, when tests run, when to commit, what it takes to move between phases. All
> of that lives in `.daw/` and applies on its own.

<!-- BEGIN DAW (managed by DAW — do not edit by hand) -->
# DAW — Dilux Agentic Workflow

This repo uses **DAW**: an agent-driven development pipeline with the phases
`CLASSIFY → DEFINE → PLAN → CODE → VERIFY → RELEASE`.

Before answering, read `.daw/orchestrator.md` and run its Boot Sequence. It is a strict state
machine: it decides what you are allowed to do based on the phase recorded in `.daw-state.json`.

The project's own context — stack, architecture, domain — is elsewhere in this file. It lives here,
in `AGENTS.md`, and not in any one tool's file, on purpose: it is tool-agnostic and comes along
unchanged when the pipeline is ported to another agent.
<!-- END DAW -->
