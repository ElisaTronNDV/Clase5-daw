import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { ProductService } from './product.service';
import { environment } from '../../../environments/environment';
import type { ProductCreate, ProductOut, ProductUpdate } from '../models/product.models';

describe('ProductService', () => {
  let service: ProductService;
  let httpMock: HttpTestingController;

  const product: ProductOut = {
    id: 1,
    material: 'sae_1010',
    espesor: 2.1,
    largo: 3000,
    ancho: 1500,
    stock: 10,
    stock_comprometido: 0,
    punto_pedido: 5,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ProductService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ProductService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  describe('list', () => {
    it('obtiene el listado completo de productos', () => {
      const response: ProductOut[] = [product];
      let emitted: ProductOut[] | undefined;

      service.list().subscribe((res: ProductOut[]) => {
        emitted = res;
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/products`);
      expect(req.request.method).toBe('GET');
      req.flush(response);

      expect(emitted).toEqual(response);
    });
  });

  describe('getById', () => {
    it('obtiene un producto por id', () => {
      let emitted: ProductOut | undefined;

      service.getById(1).subscribe((res: ProductOut) => {
        emitted = res;
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/products/1`);
      expect(req.request.method).toBe('GET');
      req.flush(product);

      expect(emitted).toEqual(product);
    });

    it('con 404 propaga el error', () => {
      let errorReceived: unknown;

      service.getById(999).subscribe({
        next: () => {
          throw new Error('should not emit a value');
        },
        error: (err: unknown) => {
          errorReceived = err;
        },
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/products/999`);
      req.flush({ detail: 'product not found' }, { status: 404, statusText: 'Not Found' });

      expect(errorReceived).toBeTruthy();
    });
  });

  describe('create', () => {
    it('envía el body correcto y emite ProductOut', () => {
      const body: ProductCreate = {
        material: 'sae_1010',
        espesor: 2.1,
        largo: 3000,
        ancho: 1500,
        stock: 10,
        punto_pedido: 5,
      };
      let emitted: ProductOut | undefined;

      service.create(body).subscribe((res: ProductOut) => {
        emitted = res;
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/products`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(body);
      req.flush(product);

      expect(emitted).toEqual(product);
    });

    it('con 400 propaga el error', () => {
      const body: ProductCreate = {
        material: 'sae_1010',
        espesor: 2.1,
        largo: 3000,
        ancho: 1500,
        stock: 10,
        punto_pedido: 5,
      };
      let errorReceived: unknown;

      service.create(body).subscribe({
        next: () => {
          throw new Error('should not emit a value');
        },
        error: (err: unknown) => {
          errorReceived = err;
        },
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/products`);
      req.flush(
        { detail: 'product already exists with this material, thickness and dimensions' },
        { status: 400, statusText: 'Bad Request' },
      );

      expect(errorReceived).toBeTruthy();
    });
  });

  describe('update', () => {
    it('envía el body correcto y emite ProductOut', () => {
      const body: ProductUpdate = {
        material: 'sae_1010',
        espesor: 2.1,
        largo: 3000,
        ancho: 1500,
        stock: 20,
        punto_pedido: 5,
      };
      let emitted: ProductOut | undefined;

      service.update(1, body).subscribe((res: ProductOut) => {
        emitted = res;
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/products/1`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual(body);
      req.flush({ ...product, stock: 20 });

      expect(emitted).toEqual({ ...product, stock: 20 });
    });

    it('con 400 propaga el error', () => {
      const body: ProductUpdate = {
        material: 'sae_1010',
        espesor: 2.1,
        largo: 3000,
        ancho: 1500,
        stock: 20,
        punto_pedido: 5,
      };
      let errorReceived: unknown;

      service.update(1, body).subscribe({
        next: () => {
          throw new Error('should not emit a value');
        },
        error: (err: unknown) => {
          errorReceived = err;
        },
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/products/1`);
      req.flush(
        { detail: 'product already exists with this material, thickness and dimensions' },
        { status: 400, statusText: 'Bad Request' },
      );

      expect(errorReceived).toBeTruthy();
    });
  });
});
