class EmailAlreadyRegisteredError(Exception):
    """Se intentó registrar un email que ya existe en la tabla users."""
