import { TestBed } from '@angular/core/testing';

import { Oficina } from './oficina';

describe('Oficina', () => {
  it('renderiza el mensaje "módulo en construcción"', () => {
    TestBed.configureTestingModule({ imports: [Oficina] });
    const fixture = TestBed.createComponent(Oficina);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.textContent?.toLowerCase()).toContain('módulo en construcción');
  });
});
