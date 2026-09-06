import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { ListadoOrdenes } from './listado-ordenes';
import { OrdenService } from '../services/orden.service';
import type { OrdenListItem } from '../models/orden.models';

describe('ListadoOrdenes', () => {
  let ordenServiceSpy: {
    listarOrdenes: ReturnType<typeof vi.fn>;
    descargarDocumento: ReturnType<typeof vi.fn>;
  };

  const ordenes: OrdenListItem[] = [
    {
      id: 1,
      nest_code: 'NEST-000001',
      estado: 'vigente',
      material: 'sae_1010',
      espesor: 2.1,
      largo: 1000,
      ancho: 500,
      multiplicidad: 2,
      created_at: '2026-08-26T00:00:00Z',
    },
  ];

  function createFixture() {
    ordenServiceSpy = {
      listarOrdenes: vi.fn().mockReturnValue(of({ ordenes })),
      descargarDocumento: vi.fn().mockReturnValue(of(new Blob(['%PDF-1.4']))),
    };

    TestBed.configureTestingModule({
      imports: [ListadoOrdenes],
      providers: [{ provide: OrdenService, useValue: ordenServiceSpy }],
    });

    const fixture = TestBed.createComponent(ListadoOrdenes);
    fixture.detectChanges();
    return fixture;
  }

  it('carga las órdenes al inicializar y las renderiza', () => {
    const fixture = createFixture();

    expect(ordenServiceSpy.listarOrdenes).toHaveBeenCalledTimes(1);
    expect(fixture.nativeElement.textContent).toContain('NEST-000001');
  });

  it('aplica el filtro de estado', () => {
    vi.useFakeTimers();
    try {
      const fixture = createFixture();
      ordenServiceSpy.listarOrdenes.mockClear();

      fixture.componentInstance.filtros.patchValue({ estado: 'vigente' });
      vi.advanceTimersByTime(400);

      expect(ordenServiceSpy.listarOrdenes).toHaveBeenCalledTimes(1);
      expect(ordenServiceSpy.listarOrdenes).toHaveBeenLastCalledWith('vigente', undefined);
    } finally {
      vi.useRealTimers();
    }
  });

  it('combina filtro de estado con búsqueda por NEST', () => {
    vi.useFakeTimers();
    try {
      const fixture = createFixture();
      ordenServiceSpy.listarOrdenes.mockClear();

      fixture.componentInstance.filtros.patchValue({ estado: 'cerrada', nest: 'NEST-000001' });
      vi.advanceTimersByTime(400);

      expect(ordenServiceSpy.listarOrdenes).toHaveBeenLastCalledWith('cerrada', 'NEST-000001');
    } finally {
      vi.useRealTimers();
    }
  });

  it('dispara la descarga del blob con un enlace temporal', () => {
    const originalCreate = URL.createObjectURL;
    const originalRevoke = URL.revokeObjectURL;
    const createObjectURL = vi.fn().mockReturnValue('blob:fake');
    const revokeObjectURL = vi.fn();
    URL.createObjectURL = createObjectURL;
    URL.revokeObjectURL = revokeObjectURL;
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined);

    try {
      const fixture = createFixture();
      fixture.componentInstance.descargar(1);

      expect(ordenServiceSpy.descargarDocumento).toHaveBeenCalledWith(1);
      expect(createObjectURL).toHaveBeenCalled();
      expect(clickSpy).toHaveBeenCalled();
    } finally {
      clickSpy.mockRestore();
      URL.createObjectURL = originalCreate;
      URL.revokeObjectURL = originalRevoke;
    }
  });

  it('setea errorMessage cuando el servicio falla al recargar el listado', () => {
    vi.useFakeTimers();
    try {
      const fixture = createFixture();
      ordenServiceSpy.listarOrdenes.mockReturnValue(throwError(() => new Error('fail')));

      fixture.componentInstance.filtros.patchValue({ estado: 'vigente' });
      vi.advanceTimersByTime(400);

      expect(fixture.componentInstance.errorMessage()).toBeTruthy();
    } finally {
      vi.useRealTimers();
    }
  });

  it('setea errorMessage cuando falla la descarga del documento', () => {
    const fixture = createFixture();
    ordenServiceSpy.descargarDocumento.mockReturnValue(throwError(() => new Error('fail')));

    fixture.componentInstance.descargar(1);

    expect(fixture.componentInstance.errorMessage()).toBeTruthy();
  });
});
