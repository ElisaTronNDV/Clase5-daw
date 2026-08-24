import { TestBed } from '@angular/core/testing';

import { Configuracion } from './configuracion';

describe('Configuracion', () => {
  it('renderiza el mensaje "módulo en construcción"', () => {
    TestBed.configureTestingModule({ imports: [Configuracion] });
    const fixture = TestBed.createComponent(Configuracion);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.textContent?.toLowerCase()).toContain('módulo en construcción');
  });
});
