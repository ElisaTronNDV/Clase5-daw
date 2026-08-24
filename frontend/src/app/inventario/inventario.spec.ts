import { TestBed } from '@angular/core/testing';

import { Inventario } from './inventario';

describe('Inventario', () => {
  it('renderiza el mensaje "módulo en construcción"', () => {
    TestBed.configureTestingModule({ imports: [Inventario] });
    const fixture = TestBed.createComponent(Inventario);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.textContent?.toLowerCase()).toContain('módulo en construcción');
  });
});
