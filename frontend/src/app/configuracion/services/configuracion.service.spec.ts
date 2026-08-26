import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { ConfiguracionService } from './configuracion.service';
import { environment } from '../../../environments/environment';
import type { ConfiguracionOut, ConfiguracionUpdate } from '../models/configuracion.models';

describe('ConfiguracionService', () => {
  let service: ConfiguracionService;
  let httpMock: HttpTestingController;

  const configuracion: ConfiguracionOut = { margen_tolerancia_dimensional: 1.0 };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfiguracionService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ConfiguracionService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('get', () => {
    it('obtiene el valor actual de configuración', () => {
      let emitted: ConfiguracionOut | undefined;

      service.get().subscribe((res: ConfiguracionOut) => {
        emitted = res;
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/configuracion`);
      expect(req.request.method).toBe('GET');
      req.flush(configuracion);

      expect(emitted).toEqual(configuracion);
    });

    it('con error propaga el error', () => {
      let errorReceived: unknown;

      service.get().subscribe({
        next: () => {
          throw new Error('should not emit a value');
        },
        error: (err: unknown) => {
          errorReceived = err;
        },
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/configuracion`);
      req.flush({ detail: 'unauthorized' }, { status: 401, statusText: 'Unauthorized' });

      expect(errorReceived).toBeTruthy();
    });
  });

  describe('update', () => {
    it('envía el body correcto y emite el valor actualizado', () => {
      const body: ConfiguracionUpdate = { margen_tolerancia_dimensional: 2.5 };
      const response: ConfiguracionOut = { margen_tolerancia_dimensional: 2.5 };
      let emitted: ConfiguracionOut | undefined;

      service.update(body).subscribe((res: ConfiguracionOut) => {
        emitted = res;
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/configuracion`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual(body);
      req.flush(response);

      expect(emitted).toEqual(response);
    });

    it('con 422 propaga el error', () => {
      const body: ConfiguracionUpdate = { margen_tolerancia_dimensional: -1 };
      let errorReceived: unknown;

      service.update(body).subscribe({
        next: () => {
          throw new Error('should not emit a value');
        },
        error: (err: unknown) => {
          errorReceived = err;
        },
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/configuracion`);
      req.flush({ detail: 'invalid value' }, { status: 422, statusText: 'Unprocessable Entity' });

      expect(errorReceived).toBeTruthy();
    });
  });
});
