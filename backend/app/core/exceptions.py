class EmailAlreadyRegisteredError(Exception):
    """Se intentó registrar un email que ya existe en la tabla users."""


class ProductAlreadyExistsError(Exception):
    """Se intentó crear/editar un producto duplicado (mismo material case-insensitive,
    espesor, largo y ancho que otro producto ya existente)."""


class ProductNotFoundError(Exception):
    """Se buscó/editó un producto por id que no existe en la tabla products."""


class ArchivoCorteInvalidoError(Exception):
    """El archivo de corte (PDF) no se pudo procesar: faltan las tablas esperadas,
    supera el límite de páginas, un campo numérico no parsea, un patrón de "Saved
    scrap" está corrupto, o pdfplumber lanzó una excepción interna al parsearlo."""


class ProductoSinCoincidenciaError(Exception):
    """No se encontró ningún producto que matchee por tolerancia dimensional al
    confirmar una orden, y no se solicitó alta automática."""


class OrdenNotFoundError(Exception):
    """Se buscó una orden por id que no existe en la tabla ordenes."""
