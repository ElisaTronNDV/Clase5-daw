import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { Inventario } from './inventario';
import { ProductService } from './services/product.service';
import type { ProductOut } from './models/product.models';

describe('Inventario', () => {
  let productServiceSpy: { list: ReturnType<typeof vi.fn> };

  const products: ProductOut[] = [
    {
      id: 1,
      material: 'sae_1010',
      espesor: 2.1,
      largo: 3000,
      ancho: 1500,
      stock: 10,
      stock_comprometido: 2,
      punto_pedido: 5,
    },
    {
      id: 2,
      material: 'sae_1020',
      espesor: 3,
      largo: 2000,
      ancho: 1000,
      stock: 4,
      stock_comprometido: 0,
      punto_pedido: 2,
    },
  ];

  beforeEach(async () => {
    productServiceSpy = { list: vi.fn().mockReturnValue(of(products)) };

    await TestBed.configureTestingModule({
      imports: [Inventario],
      providers: [provideRouter([]), { provide: ProductService, useValue: productServiceSpy }],
    }).compileComponents();
  });

  it('renderiza el listado de productos obtenido del servicio', () => {
    const fixture = TestBed.createComponent(Inventario);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(productServiceSpy.list).toHaveBeenCalled();
    expect(compiled.textContent).toContain('sae_1010');
    expect(compiled.textContent).toContain('sae_1020');
  });

  it('renderiza las 7 columnas requeridas para cada producto (AC-08)', () => {
    const fixture = TestBed.createComponent(Inventario);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const rows = compiled.querySelectorAll('tbody tr');

    expect(rows.length).toBe(2);
    const firstRowCells = Array.from(rows[0].querySelectorAll('td')).map(
      (cell) => cell.textContent?.trim(),
    );

    expect(firstRowCells).toEqual(
      expect.arrayContaining([
        'sae_1010', // material
        '2.1', // espesor
        '3000', // largo
        '1500', // ancho
        '10', // stock
        '2', // stock_comprometido
        '5', // punto_pedido
      ]),
    );
  });

  it('muestra un botón para crear un nuevo producto', () => {
    const fixture = TestBed.createComponent(Inventario);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const link = compiled.querySelector('a[href="/inventario/nuevo"]');

    expect(link).toBeTruthy();
  });

  it('cada producto del listado tiene un botón de edición', () => {
    const fixture = TestBed.createComponent(Inventario);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('a[href="/inventario/1/editar"]')).toBeTruthy();
    expect(compiled.querySelector('a[href="/inventario/2/editar"]')).toBeTruthy();
  });
});
