import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import type { ProductCreate, ProductOut, ProductUpdate } from '../models/product.models';

@Injectable({ providedIn: 'root' })
export class ProductService {
  private readonly http = inject(HttpClient);

  list(): Observable<ProductOut[]> {
    return this.http.get<ProductOut[]>(`${environment.apiUrl}/products`);
  }

  getById(id: number): Observable<ProductOut> {
    return this.http.get<ProductOut>(`${environment.apiUrl}/products/${id}`);
  }

  create(data: ProductCreate): Observable<ProductOut> {
    return this.http.post<ProductOut>(`${environment.apiUrl}/products`, data);
  }

  update(id: number, data: ProductUpdate): Observable<ProductOut> {
    return this.http.put<ProductOut>(`${environment.apiUrl}/products/${id}`, data);
  }
}
