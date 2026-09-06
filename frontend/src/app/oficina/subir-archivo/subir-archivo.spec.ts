import { TestBed } from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { Subject, of, throwError } from 'rxjs';

import { SubirArchivo } from './subir-archivo';
import { OrdenService } from '../services/orden.service';
import type { OrdenBorrador } from '../models/orden.models';

describe('SubirArchivo', () => {
  let ordenServiceSpy: { subirArchivo: ReturnType<typeof vi.fn> };

  function createFixture() {
    ordenServiceSpy = { subirArchivo: vi.fn() };

    TestBed.configureTestingModule({
      imports: [SubirArchivo],
      providers: [{ provide: OrdenService, useValue: ordenServiceSpy }],
    });

    const fixture = TestBed.createComponent(SubirArchivo);
    fixture.detectChanges();
    return fixture;
  }

  function fileInputEvent(file: File | null): Event {
    const input = document.createElement('input');
    input.type = 'file';
    // jsdom no implementa DataTransfer; se define `files` directamente como un FileList-like.
    Object.defineProperty(input, 'files', {
      value: file ? [file] : [],
      configurable: true,
    });
    return { target: input } as unknown as Event;
  }

  it('rechaza en cliente un archivo no-PDF', () => {
    const fixture = createFixture();
    const file = new File(['contenido'], 'ejemplo.txt', { type: 'text/plain' });

    fixture.componentInstance.onFileSelected(fileInputEvent(file));
    fixture.detectChanges();

    expect(ordenServiceSpy.subirArchivo).not.toHaveBeenCalled();
    expect(fixture.componentInstance.errorMessage()).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('PDF');
  });

  it('acepta un PDF y llama a OrdenService.subirArchivo', () => {
    const paginas: OrdenBorrador[] = [];
    ordenServiceSpy.subirArchivo = vi.fn();
    const fixture = createFixture();
    ordenServiceSpy.subirArchivo.mockReturnValue(of({ paginas }));
    const file = new File(['contenido'], 'ejemplo.pdf', { type: 'application/pdf' });
    let emitted: OrdenBorrador[] | undefined;
    fixture.componentInstance.paginasExtraidas.subscribe((p: OrdenBorrador[]) => (emitted = p));

    fixture.componentInstance.onFileSelected(fileInputEvent(file));
    fixture.detectChanges();

    expect(ordenServiceSpy.subirArchivo).toHaveBeenCalledWith(file);
    expect(emitted).toBe(paginas);
    expect(fixture.componentInstance.errorMessage()).toBeNull();
  });

  it('muestra un mensaje de error si la subida falla', () => {
    const fixture = createFixture();
    ordenServiceSpy.subirArchivo.mockReturnValue(throwError(() => new Error('fail')));
    const file = new File(['contenido'], 'ejemplo.pdf', { type: 'application/pdf' });

    fixture.componentInstance.onFileSelected(fileInputEvent(file));
    fixture.detectChanges();

    expect(fixture.componentInstance.errorMessage()).toBeTruthy();
  });

  function subirConError(status: number, error: unknown): { errorMessage: string | null } {
    const fixture = createFixture();
    ordenServiceSpy.subirArchivo.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status, error })),
    );
    const file = new File(['contenido'], 'ejemplo.pdf', { type: 'application/pdf' });

    fixture.componentInstance.onFileSelected(fileInputEvent(file));
    fixture.detectChanges();

    return { errorMessage: fixture.componentInstance.errorMessage() };
  }

  it('muestra el indicador de carga mientras la subida está en curso', () => {
    const fixture = createFixture();
    const pendiente = new Subject<{ paginas: OrdenBorrador[] }>();
    ordenServiceSpy.subirArchivo.mockReturnValue(pendiente.asObservable());
    const file = new File(['contenido'], 'ejemplo.pdf', { type: 'application/pdf' });

    fixture.componentInstance.onFileSelected(fileInputEvent(file));
    fixture.detectChanges();

    expect(fixture.componentInstance.cargando()).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Procesando');

    pendiente.next({ paginas: [] });
    pendiente.complete();
    fixture.detectChanges();

    expect(fixture.componentInstance.cargando()).toBe(false);
  });

  it('mapea el 413 a un mensaje de tamaño máximo en español', () => {
    const { errorMessage } = subirConError(413, { detail: 'too large' });

    expect(errorMessage).toBe('El archivo supera el tamaño máximo permitido (10 MB).');
  });

  it('mapea el 422 usando el detail del backend cuando es un string', () => {
    const { errorMessage } = subirConError(422, {
      detail: 'No se encontraron las tablas esperadas del archivo de corte',
    });

    expect(errorMessage).toBe('No se encontraron las tablas esperadas del archivo de corte');
  });

  it('mapea el 422 sin detail legible a un mensaje genérico de procesamiento', () => {
    const { errorMessage } = subirConError(422, {});

    expect(errorMessage).toBe(
      'El archivo de corte no pudo procesarse. Revisá que sea un PDF válido de Salvagnini.',
    );
  });

  it('mapea el 400 (PDF inválido) a un mensaje distinto del de 413/422', () => {
    const { errorMessage: msg400 } = subirConError(400, { detail: 'el archivo no es un PDF válido' });

    expect(msg400).toBe('el archivo no es un PDF válido');
    expect(msg400).not.toBe('El archivo supera el tamaño máximo permitido (10 MB).');
    expect(msg400).not.toBe(
      'El archivo de corte no pudo procesarse. Revisá que sea un PDF válido de Salvagnini.',
    );
  });
});
