import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { Shell } from './shell';
import { AuthService } from '../../auth/services/auth.service';

describe('Shell', () => {
  let authServiceSpy: { logout: ReturnType<typeof vi.fn> };
  let router: Router;

  beforeEach(async () => {
    authServiceSpy = { logout: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [Shell],
      providers: [provideRouter([]), { provide: AuthService, useValue: authServiceSpy }],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
  });

  it('muestra los 4 links de módulo', () => {
    const fixture = TestBed.createComponent(Shell);
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

  it('el botón de logout llama a AuthService.logout y navega a /login', () => {
    const fixture = TestBed.createComponent(Shell);
    const component = fixture.componentInstance;
    fixture.detectChanges();

    component.logout();

    expect(authServiceSpy.logout).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });
});
