import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { Register } from './register';
import { AuthService } from '../services/auth.service';

describe('Register', () => {
  let authServiceSpy: { register: ReturnType<typeof vi.fn> };
  let router: Router;

  beforeEach(async () => {
    authServiceSpy = { register: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [Register],
      providers: [provideRouter([]), { provide: AuthService, useValue: authServiceSpy }],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
  });

  it('el submit está deshabilitado con el form inválido', () => {
    const fixture = TestBed.createComponent(Register);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const button = compiled.querySelector('button[type="submit"]') as HTMLButtonElement;

    expect(button.disabled).toBe(true);
  });

  it('submit válido llama a AuthService.register y navega a /login en éxito', () => {
    authServiceSpy.register.mockReturnValue(of({ id: 1, email: 'user@dyp.com' }));

    const fixture = TestBed.createComponent(Register);
    const component = fixture.componentInstance;
    component.form.setValue({ email: 'user@dyp.com', password: 'secret123' });
    fixture.detectChanges();

    component.onSubmit();

    expect(authServiceSpy.register).toHaveBeenCalledWith('user@dyp.com', 'secret123');
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('muestra el mensaje de error en email duplicado (400)', () => {
    authServiceSpy.register.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 400 })),
    );

    const fixture = TestBed.createComponent(Register);
    const component = fixture.componentInstance;
    component.form.setValue({ email: 'user@dyp.com', password: 'secret123' });
    fixture.detectChanges();

    component.onSubmit();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(component.errorMessage()).toBe('Ese email ya está registrado');
    expect(compiled.textContent).toContain('Ese email ya está registrado');
  });

  it('muestra el mensaje de error si la contraseña es muy corta (422)', () => {
    authServiceSpy.register.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 422 })),
    );

    const fixture = TestBed.createComponent(Register);
    const component = fixture.componentInstance;
    // Passes client-side minLength(8) so the submit reaches AuthService.register;
    // the 422 mocked here represents the backend's own password policy check.
    component.form.setValue({ email: 'user@dyp.com', password: 'secret12' });
    fixture.detectChanges();

    component.onSubmit();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(component.errorMessage()).toBe('La contraseña debe tener al menos 8 caracteres');
    expect(compiled.textContent).toContain('La contraseña debe tener al menos 8 caracteres');
  });
});
