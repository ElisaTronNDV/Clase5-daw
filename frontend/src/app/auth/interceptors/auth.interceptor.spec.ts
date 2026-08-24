import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';

import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let authServiceSpy: { getToken: ReturnType<typeof vi.fn>; logout: ReturnType<typeof vi.fn> };
  let routerSpy: { navigate: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    authServiceSpy = { getToken: vi.fn(), logout: vi.fn() };
    routerSpy = { navigate: vi.fn() };

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });

    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('agrega el header Authorization cuando hay token', () => {
    authServiceSpy.getToken.mockReturnValue('my-token');

    http.get('/api/test').subscribe();

    const req = httpMock.expectOne('/api/test');
    expect(req.request.headers.get('Authorization')).toBe('Bearer my-token');
    req.flush({});
  });

  it('no agrega el header cuando no hay token', () => {
    authServiceSpy.getToken.mockReturnValue(null);

    http.get('/api/test').subscribe();

    const req = httpMock.expectOne('/api/test');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({});
  });

  it('en 401 llama logout y navega a /login', () => {
    authServiceSpy.getToken.mockReturnValue('my-token');
    let errorReceived: unknown;

    http.get('/api/test').subscribe({
      next: () => {
        throw new Error('should not emit a value');
      },
      error: (err: unknown) => {
        errorReceived = err;
      },
    });

    const req = httpMock.expectOne('/api/test');
    req.flush({ detail: 'invalid or expired token' }, { status: 401, statusText: 'Unauthorized' });

    expect(authServiceSpy.logout).toHaveBeenCalled();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
    expect(errorReceived).toBeTruthy();
  });

  it('en un error distinto de 401 no llama logout ni navega, pero relanza el error', () => {
    authServiceSpy.getToken.mockReturnValue('my-token');
    let errorReceived: unknown;

    http.get('/api/test').subscribe({
      next: () => {
        throw new Error('should not emit a value');
      },
      error: (err: unknown) => {
        errorReceived = err;
      },
    });

    const req = httpMock.expectOne('/api/test');
    req.flush({ detail: 'server error' }, { status: 500, statusText: 'Internal Server Error' });

    expect(authServiceSpy.logout).not.toHaveBeenCalled();
    expect(routerSpy.navigate).not.toHaveBeenCalled();
    expect(errorReceived).toBeTruthy();
  });
});
