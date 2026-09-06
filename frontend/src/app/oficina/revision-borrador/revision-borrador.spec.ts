import { TestBed } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { RevisionBorrador } from './revision-borrador';
import { OrdenService } from '../services/orden.service';
import type { OrdenBorrador, OrdenConfirmarRequest, OrdenResponse } from '../models/orden.models';

describe('RevisionBorrador', () => {
  let ordenServiceSpy: { confirmarOrden: ReturnType<typeof vi.fn> };

  const borrador: OrdenBorrador = {
    indice_formato: '1/3',
    multiplicidad: 2,
    material: 'sae_1010',
    espesor: 2.1,
    largo: 1000,
    ancho: 500,
    tiempo_ejecucion_estimado: '00:15:00',
    piezas: [
      {
        ref: 'A1',
        cantidad: 3,
        pieza: 'Tapa',
        descripcion: 'Tapa lateral',
        es_recorte: false,
        largo_mm: null,
        ancho_mm: null,
      },
    ],
  };

  const respuestaExitosa: OrdenResponse = {
    id: 10,
    nest_code: 'NEST-000010',
    estado: 'vigente',
    multiplicidad: 2,
    material: 'sae_1010',
    espesor: 2.1,
    largo: 1000,
    ancho: 500,
    tiempo_ejecucion_estimado: '00:15:00',
    indice_formato: '1/3',
    product_id: 5,
    created_at: '2026-08-26T00:00:00Z',
    piezas: [],
    alerta_stock_bajo: false,
  };

  function createFixture() {
    ordenServiceSpy = { confirmarOrden: vi.fn() };

    TestBed.configureTestingModule({
      imports: [RevisionBorrador],
      providers: [{ provide: OrdenService, useValue: ordenServiceSpy }],
    });

    const fixture = TestBed.createComponent(RevisionBorrador);
    fixture.componentRef.setInput('borrador', borrador);
    fixture.componentRef.setInput('indiceActual', 0);
    fixture.componentRef.setInput('totalPaginas', 3);
    fixture.detectChanges();
    return fixture;
  }

  it('muestra los datos extraídos en un formulario editable antes de confirmar', () => {
    const fixture = createFixture();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(fixture.componentInstance.form.value.material).toBe('sae_1010');
    expect(fixture.componentInstance.form.value.multiplicidad).toBe(2);
    expect(fixture.componentInstance.form.value.espesor).toBe(2.1);
    expect(fixture.componentInstance.form.value.largo).toBe(1000);
    expect(fixture.componentInstance.form.value.ancho).toBe(500);

    const materialInput = compiled.querySelector('#material') as HTMLInputElement;
    expect(materialInput).toBeTruthy();
    expect(materialInput.readOnly).toBe(false);
    expect(materialInput.disabled).toBe(false);
  });

  it('usa el valor editado en vez del extraído al confirmar', () => {
    const fixture = createFixture();
    ordenServiceSpy.confirmarOrden.mockReturnValue(of(respuestaExitosa));

    fixture.componentInstance.form.patchValue({ material: 'sae_1020', multiplicidad: 5 });
    fixture.componentInstance.onSubmit();

    expect(ordenServiceSpy.confirmarOrden).toHaveBeenCalledTimes(1);
    const payload = ordenServiceSpy.confirmarOrden.mock.calls[0][0] as OrdenConfirmarRequest;
    expect(payload.material).toBe('sae_1020');
    expect(payload.multiplicidad).toBe(5);
    expect(payload.crear_producto_automaticamente).toBe(false);
  });

  it('muestra el diálogo de advertencia ante 409 y reintenta con la bandera', () => {
    const errorBody = { material: 'sae_1010', espesor: 2.1, largo: 1000, ancho: 500 };
    const fixture = createFixture();
    ordenServiceSpy.confirmarOrden
      .mockReturnValueOnce(
        throwError(() => new HttpErrorResponse({ status: 409, error: errorBody })),
      )
      .mockReturnValueOnce(of(respuestaExitosa));

    fixture.componentInstance.onSubmit();
    fixture.detectChanges();

    expect(fixture.componentInstance.productoNoEncontrado()).toEqual(errorBody);
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('sae_1010');

    fixture.componentInstance.onCrearProductoYConfirmar();
    fixture.detectChanges();

    expect(ordenServiceSpy.confirmarOrden).toHaveBeenCalledTimes(2);
    const segundoPayload = ordenServiceSpy.confirmarOrden.mock.calls[1][0] as OrdenConfirmarRequest;
    expect(segundoPayload.crear_producto_automaticamente).toBe(true);
    expect(fixture.componentInstance.ordenConfirmada()).toEqual(respuestaExitosa);
  });

  it('muestra el indicador de alerta_stock_bajo cuando viene en true', () => {
    const respuestaConAlerta: OrdenResponse = { ...respuestaExitosa, alerta_stock_bajo: true };
    const fixture = createFixture();
    ordenServiceSpy.confirmarOrden.mockReturnValue(of(respuestaConAlerta));

    fixture.componentInstance.onSubmit();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('[data-testid="alerta-stock-bajo"]')).toBeTruthy();
  });

  it('no muestra el indicador de alerta_stock_bajo cuando viene en false', () => {
    const fixture = createFixture();
    ordenServiceSpy.confirmarOrden.mockReturnValue(of(respuestaExitosa));

    fixture.componentInstance.onSubmit();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('[data-testid="alerta-stock-bajo"]')).toBeFalsy();
  });

  it('muestra un placeholder cuando el borrador no trae indice_formato', () => {
    const fixture = createFixture();
    fixture.componentRef.setInput('borrador', { ...borrador, indice_formato: null });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('(sin índice)');
  });

  it('ante un 422 muestra un mensaje de datos inválidos y no marca la orden como confirmada', () => {
    const fixture = createFixture();
    ordenServiceSpy.confirmarOrden.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 422, error: { detail: 'espesor inválido' } })),
    );

    fixture.componentInstance.onSubmit();
    fixture.detectChanges();

    expect(fixture.componentInstance.errorMessage()).toBe(
      'Los datos de la orden no son válidos. Revisá los campos.',
    );
    expect(fixture.componentInstance.ordenConfirmada()).toBeNull();
    expect(fixture.componentInstance.productoNoEncontrado()).toBeNull();
  });

  it('ante un error no esperado (500) muestra un mensaje genérico de confirmación', () => {
    const fixture = createFixture();
    ordenServiceSpy.confirmarOrden.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 500, error: 'boom' })),
    );

    fixture.componentInstance.onSubmit();
    fixture.detectChanges();

    expect(fixture.componentInstance.errorMessage()).toBe(
      'No se pudo confirmar la orden. Intentá nuevamente.',
    );
    expect(fixture.componentInstance.ordenConfirmada()).toBeNull();
  });
});
