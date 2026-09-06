import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { of } from 'rxjs';

import { Oficina } from './oficina';
import { SubirArchivo } from './subir-archivo/subir-archivo';
import { RevisionBorrador } from './revision-borrador/revision-borrador';
import { ListadoOrdenes } from './listado-ordenes/listado-ordenes';
import { OrdenService } from './services/orden.service';
import type { OrdenBorrador, OrdenResponse } from './models/orden.models';

describe('Oficina', () => {
  const borradores: OrdenBorrador[] = [
    {
      indice_formato: '1/2',
      multiplicidad: 1,
      material: 'sae_1010',
      espesor: 2.1,
      largo: 1000,
      ancho: 500,
      tiempo_ejecucion_estimado: null,
      piezas: [],
    },
    {
      indice_formato: '2/2',
      multiplicidad: 1,
      material: 'sae_1010',
      espesor: 2.1,
      largo: 1000,
      ancho: 500,
      tiempo_ejecucion_estimado: null,
      piezas: [],
    },
  ];

  function createFixture() {
    const ordenServiceSpy = {
      subirArchivo: vi.fn(),
      confirmarOrden: vi.fn(),
      listarOrdenes: vi.fn().mockReturnValue(of({ ordenes: [] })),
      descargarDocumento: vi.fn(),
    };

    TestBed.configureTestingModule({
      imports: [Oficina],
      providers: [{ provide: OrdenService, useValue: ordenServiceSpy }],
    });

    const fixture = TestBed.createComponent(Oficina);
    fixture.detectChanges();
    return fixture;
  }

  it('renderiza SubirArchivo al inicio', () => {
    const fixture = createFixture();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('app-subir-archivo')).toBeTruthy();
    expect(compiled.querySelector('app-revision-borrador')).toBeFalsy();
  });

  it('al recibir paginasExtraidas muestra RevisionBorrador para la primera página', () => {
    const fixture = createFixture();

    const subir = fixture.debugElement.query(By.directive(SubirArchivo))
      .componentInstance as SubirArchivo;
    subir.paginasExtraidas.emit(borradores);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('app-revision-borrador')).toBeTruthy();
    expect(compiled.querySelector('app-subir-archivo')).toBeFalsy();
    expect(compiled.textContent).toContain('1/2');
  });

  it('avanza página por página al confirmar y pasa al listado tras la última', () => {
    const respuesta = { id: 1, nest_code: 'NEST-000001' } as OrdenResponse;
    const fixture = createFixture();

    const subir = fixture.debugElement.query(By.directive(SubirArchivo))
      .componentInstance as SubirArchivo;
    subir.paginasExtraidas.emit(borradores);
    fixture.detectChanges();

    expect(fixture.componentInstance.indiceActual()).toBe(0);

    let revision = fixture.debugElement.query(By.directive(RevisionBorrador))
      .componentInstance as RevisionBorrador;
    revision.confirmada.emit(respuesta);
    fixture.detectChanges();

    expect(fixture.componentInstance.indiceActual()).toBe(1);
    expect(fixture.nativeElement.querySelector('app-revision-borrador')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('app-listado-ordenes')).toBeFalsy();

    revision = fixture.debugElement.query(By.directive(RevisionBorrador))
      .componentInstance as RevisionBorrador;
    revision.confirmada.emit(respuesta);
    fixture.detectChanges();

    expect(fixture.debugElement.query(By.directive(ListadoOrdenes))).toBeTruthy();
    expect(fixture.nativeElement.querySelector('app-revision-borrador')).toBeFalsy();
  });
});
