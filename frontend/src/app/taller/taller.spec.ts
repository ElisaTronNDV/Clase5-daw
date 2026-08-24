import { TestBed } from '@angular/core/testing';

import { Taller } from './taller';

describe('Taller', () => {
  it('renderiza el mensaje "módulo en construcción"', () => {
    TestBed.configureTestingModule({ imports: [Taller] });
    const fixture = TestBed.createComponent(Taller);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.textContent?.toLowerCase()).toContain('módulo en construcción');
  });
});
