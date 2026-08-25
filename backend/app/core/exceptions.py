class EmailAlreadyRegisteredError(Exception):
    """Se intentó registrar un email que ya existe en la tabla users."""


class ProductAlreadyExistsError(Exception):
    """Se intentó crear/editar un producto duplicado (mismo material case-insensitive,
    espesor, largo y ancho que otro producto ya existente)."""


class ProductNotFoundError(Exception):
    """Se buscó/editó un producto por id que no existe en la tabla products."""
