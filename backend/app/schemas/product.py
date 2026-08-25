from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    # extra="forbid": mitigación obligatoria del threat model (docs/daw/security/threat-FEAT-002.md)
    # — sin esto, un cliente podría enviar stock_comprometido en el body y setearlo directamente.
    model_config = ConfigDict(extra="forbid")

    material: str = Field(min_length=1, max_length=255)
    espesor: float = Field(gt=0)
    largo: float = Field(gt=0)
    ancho: float = Field(gt=0)
    stock: int = Field(gt=0)
    punto_pedido: int = Field(gt=0)


class ProductUpdate(BaseModel):
    # extra="forbid": misma mitigación que ProductCreate — stock_comprometido es de solo
    # lectura también al editar (AC-07).
    model_config = ConfigDict(extra="forbid")

    material: str = Field(min_length=1, max_length=255)
    espesor: float = Field(gt=0)
    largo: float = Field(gt=0)
    ancho: float = Field(gt=0)
    stock: int = Field(gt=0)
    punto_pedido: int = Field(gt=0)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    material: str
    espesor: float
    largo: float
    ancho: float
    stock: int
    stock_comprometido: int
    punto_pedido: int
