export interface PiezaExtraida {
  ref: string | null;
  cantidad: number;
  pieza: string;
  descripcion: string;
  es_recorte: boolean;
  largo_mm: number | null;
  ancho_mm: number | null;
}

export interface OrdenBorrador {
  indice_formato: string | null;
  multiplicidad: number;
  material: string;
  espesor: number;
  largo: number;
  ancho: number;
  tiempo_ejecucion_estimado: string | null;
  piezas: PiezaExtraida[];
}

export interface PiezaConfirmar {
  ref?: string | null;
  cantidad: number;
  pieza: string;
  descripcion: string;
  es_recorte?: boolean;
  largo_mm?: number | null;
  ancho_mm?: number | null;
}

export interface OrdenConfirmarRequest {
  indice_formato?: string | null;
  multiplicidad: number;
  material: string;
  espesor: number;
  largo: number;
  ancho: number;
  tiempo_ejecucion_estimado?: string | null;
  piezas: PiezaConfirmar[];
  crear_producto_automaticamente?: boolean;
}

export interface PiezaResponse {
  id: number;
  ref: string | null;
  cantidad: number;
  pieza: string;
  descripcion: string;
  es_recorte: boolean;
  largo_mm: number | null;
  ancho_mm: number | null;
}

export interface OrdenResponse {
  id: number;
  nest_code: string;
  estado: string;
  multiplicidad: number;
  material: string;
  espesor: number;
  largo: number;
  ancho: number;
  tiempo_ejecucion_estimado: string | null;
  indice_formato: string | null;
  product_id: number;
  created_at: string;
  piezas: PiezaResponse[];
  alerta_stock_bajo: boolean;
}

export interface OrdenListItem {
  id: number;
  nest_code: string;
  estado: string;
  material: string;
  espesor: number;
  largo: number;
  ancho: number;
  multiplicidad: number;
  created_at: string;
}

/** Body del error 409 de `POST /api/ordenes/confirmar` cuando no hay producto que matchee. */
export interface ProductoSinCoincidencia {
  material: string;
  espesor: number;
  largo: number;
  ancho: number;
}
