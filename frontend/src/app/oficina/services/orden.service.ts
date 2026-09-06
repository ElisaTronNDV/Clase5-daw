import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import type {
  OrdenBorrador,
  OrdenConfirmarRequest,
  OrdenListItem,
  OrdenResponse,
} from '../models/orden.models';

@Injectable({ providedIn: 'root' })
export class OrdenService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/ordenes`;

  subirArchivo(file: File): Observable<{ paginas: OrdenBorrador[] }> {
    const formData = new FormData();
    formData.append('archivo', file);
    return this.http.post<{ paginas: OrdenBorrador[] }>(`${this.baseUrl}/extraer`, formData);
  }

  confirmarOrden(payload: OrdenConfirmarRequest): Observable<OrdenResponse> {
    return this.http.post<OrdenResponse>(`${this.baseUrl}/confirmar`, payload);
  }

  listarOrdenes(estado?: string, nest?: string): Observable<{ ordenes: OrdenListItem[] }> {
    let params = new HttpParams();
    if (estado) {
      params = params.set('estado', estado);
    }
    if (nest) {
      params = params.set('nest', nest);
    }
    return this.http.get<{ ordenes: OrdenListItem[] }>(this.baseUrl, { params });
  }

  descargarDocumento(id: number): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/${id}/documento`, { responseType: 'blob' });
  }
}
