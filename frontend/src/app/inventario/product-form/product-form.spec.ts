import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { ProductForm } from './product-form';
import { ProductService } from '../services/product.service';
import type { ProductOut } from '../models/product.models';

describe('ProductForm', () => {
  let productServiceSpy: {
    getById: ReturnType<typeof vi.fn>;
    create: ReturnType<typeof vi.fn>;
    update: ReturnType<typeof vi.fn>;
  };
  let router: Router;

  const product: ProductOut = {
    id: 7,
    material: 'sae_1010',
    espesor: 2.1,
    largo: 3000,
    ancho: 1500,
    stock: 10,
    stock_comprometido: 3,
    punto_pedido: 5,
  };

  function configureTestBed(routeId: string | null): void {
    productServiceSpy = {
      getById: vi.fn().mockReturnValue(of(product)),
      create: vi.fn(),
      update: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [ProductForm],
      providers: [
        provideRouter([]),
        { provide: ProductService, useValue: productServiceSpy },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap(routeId ? { id: routeId } : {}) } },
        },
      ],
    });

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
  }

  function fillValidForm(fixture: ReturnType<typeof TestBed.createComponent<ProductForm>>): void {
    fixture.componentInstance.form.setValue({
      material: 'sae_1010',
      espesor: 2.1,
      largo: 3000,
      ancho: 1500,
      stock: 10,
      punto_pedido: 5,
    });
  }

  describe('modo alta', () => {
    beforeEach(() => {
      configureTestBed(null);
    });

    it('renderiza el formulario vacío con los 6 campos', () => {
      const fixture = TestBed.createComponent(ProductForm);
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;

      expect(compiled.querySelector('#material')).toBeTruthy();
      expect(compiled.querySelector('#espesor')).toBeTruthy();
      expect(compiled.querySelector('#largo')).toBeTruthy();
      expect(compiled.querySelector('#ancho')).toBeTruthy();
      expect(compiled.querySelector('#stock')).toBeTruthy();
      expect(compiled.querySelector('#punto_pedido')).toBeTruthy();
      expect(fixture.componentInstance.form.value.material).toBe('');
      expect(productServiceSpy.getById).not.toHaveBeenCalled();
    });

    it('el submit está deshabilitado con el form inválido', () => {
      const fixture = TestBed.createComponent(ProductForm);
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      const button = compiled.querySelector('button[type="submit"]') as HTMLButtonElement;

      expect(button.disabled).toBe(true);
    });

    it('modo alta — el submit está deshabilitado si un campo numérico es ≤ 0', () => {
      const fixture = TestBed.createComponent(ProductForm);
      fixture.detectChanges();
      fillValidForm(fixture);
      fixture.componentInstance.form.patchValue({ espesor: -1 });
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      const button = compiled.querySelector('button[type="submit"]') as HTMLButtonElement;

      expect(fixture.componentInstance.form.invalid).toBe(true);
      expect(button.disabled).toBe(true);
    });

    it('submit válido llama a ProductService.create y navega a /inventario', () => {
      productServiceSpy.create.mockReturnValue(of(product));

      const fixture = TestBed.createComponent(ProductForm);
      fixture.detectChanges();
      fillValidForm(fixture);
      fixture.detectChanges();

      fixture.componentInstance.onSubmit();

      expect(productServiceSpy.create).toHaveBeenCalledWith({
        material: 'sae_1010',
        espesor: 2.1,
        largo: 3000,
        ancho: 1500,
        stock: 10,
        punto_pedido: 5,
      });
      expect(router.navigate).toHaveBeenCalledWith(['/inventario']);
    });

    it('muestra el mensaje de error en 400 (duplicado)', () => {
      productServiceSpy.create.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 400 })),
      );

      const fixture = TestBed.createComponent(ProductForm);
      fixture.detectChanges();
      fillValidForm(fixture);
      fixture.detectChanges();

      fixture.componentInstance.onSubmit();
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(fixture.componentInstance.errorMessage()).toBe(
        'Ya existe un producto con ese material, espesor y dimensiones',
      );
      expect(compiled.textContent).toContain(
        'Ya existe un producto con ese material, espesor y dimensiones',
      );
    });

    it('muestra un mensaje genérico ante un error no esperado (ej. red)', () => {
      productServiceSpy.create.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 0 })),
      );

      const fixture = TestBed.createComponent(ProductForm);
      fixture.detectChanges();
      fillValidForm(fixture);
      fixture.detectChanges();

      fixture.componentInstance.onSubmit();
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(fixture.componentInstance.errorMessage()).toBeTruthy();
      expect(fixture.componentInstance.errorMessage()).not.toBe(
        'Ya existe un producto con ese material, espesor y dimensiones',
      );
      expect(compiled.textContent).toContain(fixture.componentInstance.errorMessage());
    });
  });

  describe('modo edición', () => {
    beforeEach(() => {
      configureTestBed('7');
    });

    it('precarga los valores del producto vía ProductService.getById', () => {
      const fixture = TestBed.createComponent(ProductForm);
      fixture.detectChanges();

      expect(productServiceSpy.getById).toHaveBeenCalledWith(7);
      expect(fixture.componentInstance.form.value.material).toBe('sae_1010');
      expect(fixture.componentInstance.form.value.espesor).toBe(2.1);
      expect(fixture.componentInstance.form.value.stock).toBe(10);
    });

    it('el campo stock_comprometido se muestra de solo lectura, sin input editable', () => {
      const fixture = TestBed.createComponent(ProductForm);
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;

      expect(compiled.querySelector('input[formcontrolname="stock_comprometido"]')).toBeFalsy();
      expect(compiled.querySelector('#stock_comprometido')).toBeFalsy();
      expect(compiled.textContent).toContain('3');
    });

    it('submit válido llama a ProductService.update y navega a /inventario', () => {
      productServiceSpy.update.mockReturnValue(of(product));

      const fixture = TestBed.createComponent(ProductForm);
      fixture.detectChanges();
      fillValidForm(fixture);
      fixture.detectChanges();

      fixture.componentInstance.onSubmit();

      expect(productServiceSpy.update).toHaveBeenCalledWith(7, {
        material: 'sae_1010',
        espesor: 2.1,
        largo: 3000,
        ancho: 1500,
        stock: 10,
        punto_pedido: 5,
      });
      expect(router.navigate).toHaveBeenCalledWith(['/inventario']);
    });

    it('producto no encontrado (404) muestra un mensaje y navega a /inventario', () => {
      productServiceSpy.getById.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 404 })),
      );

      const fixture = TestBed.createComponent(ProductForm);
      fixture.detectChanges();

      expect(fixture.componentInstance.errorMessage()).toBeTruthy();
      expect(router.navigate).toHaveBeenCalledWith(['/inventario']);
    });
  });
});
