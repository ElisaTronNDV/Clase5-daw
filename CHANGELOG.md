# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

### Added

- [FEAT-001] Autenticación y estructura base del proyecto: scaffold backend FastAPI + SQLAlchemy con
  modelo `User`, endpoints de registro/login/`/me` con JWT (HS256, expiración 24h), hash de
  contraseñas con bcrypt; scaffold frontend Angular 22 con flujo de login/registro, guard de rutas,
  interceptor HTTP y shell de navegación con los 4 módulos (Oficina, Taller, Inventario,
  Configuración) como placeholders.
- [FEAT-002] Gestión de inventario (CRUD de productos): modelo `Product` y endpoints
  `POST/GET/GET-by-id/PUT /api/products` con rechazo de duplicados case-insensitive por
  material+espesor+dimensiones (al crear y al editar) y `stock_comprometido` protegido contra
  escritura del cliente; reemplaza el placeholder de Inventario por un listado real y un formulario
  reactivo compartido entre alta y edición, con `stock_comprometido` de solo lectura.
