import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { Login } from './login';
import { AuthService } from '../services/auth.service';

describe('Login', () => {
  let authServiceSpy: { login: ReturnType<typeof vi.fn> };
  let router: Router;

  beforeEach(async () => {
    authServiceSpy = { login: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [Login],
      providers: [provideRouter([]), { provide: AuthService, useValue: authServiceSpy }],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
  });

  it('renderiza el formulario con los campos email y password', () => {
    const fixture = TestBed.createComponent(Login);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('#email')).toBeTruthy();
    expect(compiled.querySelector('#password')).toBeTruthy();
  });

  it('el submit está deshabilitado con el form inválido', () => {
    const fixture = TestBed.createComponent(Login);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const button = compiled.querySelector('button[type="submit"]') as HTMLButtonElement;

    expect(button.disabled).toBe(true);
  });

  it('submit válido llama a AuthService.login y navega a / en éxito', () => {
    authServiceSpy.login.mockReturnValue(of({ access_token: 'token', token_type: 'bearer' }));

    const fixture = TestBed.createComponent(Login);
    const component = fixture.componentInstance;
    component.form.setValue({ email: 'user@dyp.com', password: 'secret123' });
    fixture.detectChanges();

    component.onSubmit();

    expect(authServiceSpy.login).toHaveBeenCalledWith('user@dyp.com', 'secret123');
    expect(router.navigate).toHaveBeenCalledWith(['/']);
  });

  it('muestra el mensaje de error en 401', () => {
    authServiceSpy.login.mockReturnValue(
      throwError(() => new HttpErrorResponse({ status: 401 })),
    );

    const fixture = TestBed.createComponent(Login);
    const component = fixture.componentInstance;
    component.form.setValue({ email: 'user@dyp.com', password: 'wrong' });
    fixture.detectChanges();

    component.onSubmit();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(component.errorMessage()).toBe('Email o contraseña incorrectos');
    expect(compiled.textContent).toContain('Email o contraseña incorrectos');
  });

  it('muestra un mensaje genérico ante un error no esperado (ej. red)', () => {
    authServiceSpy.login.mockReturnValue(throwError(() => new HttpErrorResponse({ status: 0 })));

    const fixture = TestBed.createComponent(Login);
    const component = fixture.componentInstance;
    component.form.setValue({ email: 'user@dyp.com', password: 'secret123' });
    fixture.detectChanges();

    component.onSubmit();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(component.errorMessage()).toBe('No se pudo conectar con el servidor');
    expect(compiled.textContent).toContain('No se pudo conectar con el servidor');
  });
});
