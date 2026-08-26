import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import type { ConfiguracionOut, ConfiguracionUpdate } from '../models/configuracion.models';

@Injectable({ providedIn: 'root' })
export class ConfiguracionService {
  private readonly http = inject(HttpClient);

  get(): Observable<ConfiguracionOut> {
    return this.http.get<ConfiguracionOut>(`${environment.apiUrl}/configuracion`);
  }

  update(data: ConfiguracionUpdate): Observable<ConfiguracionOut> {
    return this.http.put<ConfiguracionOut>(`${environment.apiUrl}/configuracion`, data);
  }
}
