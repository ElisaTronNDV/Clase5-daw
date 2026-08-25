export interface ProductCreate {
  material: string;
  espesor: number;
  largo: number;
  ancho: number;
  stock: number;
  punto_pedido: number;
}

export interface ProductUpdate {
  material: string;
  espesor: number;
  largo: number;
  ancho: number;
  stock: number;
  punto_pedido: number;
}

export interface ProductOut {
  id: number;
  material: string;
  espesor: number;
  largo: number;
  ancho: number;
  stock: number;
  stock_comprometido: number;
  punto_pedido: number;
}
