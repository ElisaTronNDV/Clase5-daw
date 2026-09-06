import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpErrorResponse } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { OrdenService } from './orden.service';
import { environment } from '../../../environments/environment';
import type { OrdenConfirmarRequest, OrdenListItem, OrdenResponse } from '../models/orden.models';

describe('OrdenService', () => {
  let service: OrdenService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [OrdenService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(OrdenService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('subirArchivo', () => {
    it('arma FormData correctamente en subirArchivo', () => {
      const file = new File(['contenido'], 'ejemplo.pdf', { type: 'application/pdf' });

      service.subirArchivo(file).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/ordenes/extraer`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toBeInstanceOf(FormData);
      const body = req.request.body as FormData;
      expect(body.get('archivo')).toBe(file);
      req.flush({ paginas: [] });
    });
  });

  describe('confirmarOrden', () => {
    it('propaga el error 409 de confirmarOrden', () => {
      const payload: OrdenConfirmarRequest = {
        multiplicidad: 1,
        material: 'sae_1010',
        espesor: 2.1,
        largo: 1000,
        ancho: 500,
        piezas: [],
      };
      let errorReceived: unknown;

      service.confirmarOrden(payload).subscribe({
        next: () => {
          throw new Error('should not emit a value');
        },
        error: (err: unknown) => {
          errorReceived = err;
        },
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/ordenes/confirmar`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(payload);
      req.flush(
        { material: 'sae_1010', espesor: 2.1, largo: 1000, ancho: 500 },
        { status: 409, statusText: 'Conflict' },
      );

      expect(errorReceived).toBeInstanceOf(HttpErrorResponse);
      expect((errorReceived as HttpErrorResponse).status).toBe(409);
      expect((errorReceived as HttpErrorResponse).error).toEqual({
        material: 'sae_1010',
        espesor: 2.1,
        largo: 1000,
        ancho: 500,
      });
    });

    it('emite OrdenResponse en un 201 exitoso', () => {
      const payload: OrdenConfirmarRequest = {
        multiplicidad: 1,
        material: 'sae_1010',
        espesor: 2.1,
        largo: 1000,
        ancho: 500,
        piezas: [],
      };
      const response: OrdenResponse = {
        id: 1,
        nest_code: 'NEST-000001',
        estado: 'vigente',
        multiplicidad: 1,
        material: 'sae_1010',
        espesor: 2.1,
        largo: 1000,
        ancho: 500,
        tiempo_ejecucion_estimado: null,
        indice_formato: null,
        product_id: 1,
        created_at: '2026-08-26T00:00:00Z',
        piezas: [],
        alerta_stock_bajo: false,
      };
      let emitted: OrdenResponse | undefined;

      service.confirmarOrden(payload).subscribe((res) => (emitted = res));

      const req = httpMock.expectOne(`${environment.apiUrl}/ordenes/confirmar`);
      req.flush(response);

      expect(emitted).toEqual(response);
    });
  });

  describe('listarOrdenes', () => {
    it('arma los query params de listarOrdenes', () => {
      const response: { ordenes: OrdenListItem[] } = { ordenes: [] };

      service.listarOrdenes('vigente', 'NEST-000001').subscribe();

      const req = httpMock.expectOne(
        (r) => r.url === `${environment.apiUrl}/ordenes` && r.method === 'GET',
      );
      expect(req.request.params.get('estado')).toBe('vigente');
      expect(req.request.params.get('nest')).toBe('NEST-000001');
      req.flush(response);
    });

    it('no agrega params ausentes', () => {
      service.listarOrdenes().subscribe();

      const req = httpMock.expectOne(
        (r) => r.url === `${environment.apiUrl}/ordenes` && r.method === 'GET',
      );
      expect(req.request.params.has('estado')).toBe(false);
      expect(req.request.params.has('nest')).toBe(false);
      req.flush({ ordenes: [] });
    });
  });

  describe('descargarDocumento', () => {
    it('pide el documento como blob', () => {
      const blob = new Blob(['%PDF-1.4'], { type: 'application/pdf' });
      let emitted: Blob | undefined;

      service.descargarDocumento(1).subscribe((res) => (emitted = res));

      const req = httpMock.expectOne(`${environment.apiUrl}/ordenes/1/documento`);
      expect(req.request.method).toBe('GET');
      expect(req.request.responseType).toBe('blob');
      req.flush(blob);

      expect(emitted).toEqual(blob);
    });
  });
});
