from pydantic import BaseModel, ConfigDict, Field


class ConfiguracionUpdate(BaseModel):
    # extra="forbid": mismo patrón de protección que ProductCreate/ProductUpdate
    # (docs/daw/security/threat-FEAT-003.md) — previene que un cliente envíe cualquier
    # campo no reconocido en el body.
    model_config = ConfigDict(extra="forbid")

    margen_tolerancia_dimensional: float = Field(gt=0)


class ConfiguracionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    margen_tolerancia_dimensional: float
