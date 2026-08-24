import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { Home } from './home';

describe('Home', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Home],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('renderiza los links a los 4 módulos', () => {
    const fixture = TestBed.createComponent(Home);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const hrefs = Array.from(compiled.querySelectorAll('a[href]')).map((a) =>
      a.getAttribute('href'),
    );

    expect(hrefs).toContain('/oficina');
    expect(hrefs).toContain('/taller');
    expect(hrefs).toContain('/inventario');
    expect(hrefs).toContain('/configuracion');
  });
});
