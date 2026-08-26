import { TestBed } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { Configuracion } from './configuracion';
import { ConfiguracionService } from './services/configuracion.service';
import type { ConfiguracionOut } from './models/configuracion.models';

describe('Configuracion', () => {
  let configuracionServiceSpy: {
    get: ReturnType<typeof vi.fn>;
    update: ReturnType<typeof vi.fn>;
  };

  const configuracion: ConfiguracionOut = { margen_tolerancia_dimensional: 1.0 };

  function configureTestBed(): void {
    configuracionServiceSpy = {
      get: vi.fn().mockReturnValue(of(configuracion)),
      update: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [Configuracion],
      providers: [{ provide: ConfiguracionService, useValue: configuracionServiceSpy }],
    });
  }

  beforeEach(() => {
    configureTestBed();
  });

  it('precarga el valor obtenido del servicio al iniciar', () => {
    configuracionServiceSpy.get.mockReturnValue(of({ margen_tolerancia_dimensional: 2.5 }));

    const fixture = TestBed.createComponent(Configuracion);
    fixture.detectChanges();

    expect(configuracionServiceSpy.get).toHaveBeenCalled();
    expect(fixture.componentInstance.form.value.margen_tolerancia_dimensional).toBe(2.5);
  });

  it('el submit está deshabilitado con el campo vacío', () => {
    const fixture = TestBed.createComponent(Configuracion);
    fixture.detectChanges();
    fixture.componentInstance.form.setValue({ margen_tolerancia_dimensional: null });
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const button = compiled.querySelector('button[type="submit"]') as HTMLButtonElement;

    expect(fixture.componentInstance.form.invalid).toBe(true);
    expect(button.disabled).toBe(true);
  });

  it('el submit está deshabilitado si el valor es ≤ 0', () => {
    const fixture = TestBed.createComponent(Configuracion);
    fixture.detectChanges();
    fixture.componentInstance.form.setValue({ margen_tolerancia_dimensional: 0 });
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const button = compiled.querySelector('button[type="submit"]') as HTMLButtonElement;

    expect(fixture.componentInstance.form.invalid).toBe(true);
    expect(button.disabled).toBe(true);
  });

  it('submit válido llama a ConfiguracionService.update y muestra confirmación', () => {
    configuracionServiceSpy.update.mockReturnValue(of({ margen_tolerancia_dimensional: 3.0 }));

    const fixture = TestBed.createComponent(Configuracion);
    fixture.detectChanges();
    fixture.componentInstance.form.setValue({ margen_tolerancia_dimensional: 3.0 });
    fixture.detectChanges();

    fixture.componentInstance.onSubmit();
    fixture.detectChanges();

    expect(configuracionServiceSpy.update).toHaveBeenCalledWith({
      margen_tolerancia_dimensional: 3.0,
    });
    expect(fixture.componentInstance.successMessage()).toBeTruthy();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain(fixture.componentInstance.successMessage());
  });

  it('muestra un mensaje de error ante un 422 del servidor', () => {
    configuracionServiceSpy.update.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 422 })),
    );

    const fixture = TestBed.createComponent(Configuracion);
    fixture.detectChanges();
    fixture.componentInstance.form.setValue({ margen_tolerancia_dimensional: -1 });
    fixture.componentInstance.form.setValue({ margen_tolerancia_dimensional: 3.0 });
    fixture.detectChanges();

    fixture.componentInstance.onSubmit();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(fixture.componentInstance.errorMessage()).toBe(
      'El valor ingresado no es válido, debe ser un número mayor a 0',
    );
    expect(compiled.textContent).toContain(
      'El valor ingresado no es válido, debe ser un número mayor a 0',
    );
    expect(fixture.componentInstance.form.value.margen_tolerancia_dimensional).toBe(3.0);
  });

  it('muestra un mensaje genérico ante un error no esperado (ej. red)', () => {
    configuracionServiceSpy.update.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 0 })),
    );

    const fixture = TestBed.createComponent(Configuracion);
    fixture.detectChanges();
    fixture.componentInstance.form.setValue({ margen_tolerancia_dimensional: 3.0 });
    fixture.detectChanges();

    fixture.componentInstance.onSubmit();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(fixture.componentInstance.errorMessage()).toBeTruthy();
    expect(fixture.componentInstance.errorMessage()).not.toBe(
      'El valor ingresado no es válido, debe ser un número mayor a 0',
    );
    expect(compiled.textContent).toContain(fixture.componentInstance.errorMessage());
    expect(fixture.componentInstance.form.value.margen_tolerancia_dimensional).toBe(3.0);
  });
});
