import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { AuthService } from './auth.service';
import { environment } from '../../../environments/environment';
import type { TokenResponse, UserOut } from '../models/auth.models';

const TOKEN_KEY = 'dyp_lasercore_token';

function base64UrlEncode(obj: unknown): string {
  const json = JSON.stringify(obj);
  return btoa(json).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function buildJwt(expSecondsFromNow: number): string {
  const header = base64UrlEncode({ alg: 'HS256', typ: 'JWT' });
  const payload = base64UrlEncode({
    sub: '1',
    exp: Math.floor(Date.now() / 1000) + expSecondsFromNow,
  });
  return `${header}.${payload}.signature`;
}

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [AuthService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  describe('login', () => {
    it('éxito guarda el token y emite TokenResponse', () => {
      const response: TokenResponse = { access_token: buildJwt(3600), token_type: 'bearer' };
      let emitted: TokenResponse | undefined;

      service.login('user@dyp.com', 'secret123').subscribe((res: TokenResponse) => {
        emitted = res;
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ email: 'user@dyp.com', password: 'secret123' });
      req.flush(response);

      expect(emitted).toEqual(response);
      expect(localStorage.getItem(TOKEN_KEY)).toBe(response.access_token);
    });

    it('con 401 no guarda token y propaga el error', () => {
      let errorReceived: unknown;

      service.login('user@dyp.com', 'wrong').subscribe({
        next: () => {
          throw new Error('should not emit a value');
        },
        error: (err: unknown) => {
          errorReceived = err;
        },
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login`);
      req.flush({ detail: 'invalid credentials' }, { status: 401, statusText: 'Unauthorized' });

      expect(errorReceived).toBeTruthy();
      expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
    });
  });

  describe('register', () => {
    it('éxito emite UserOut sin tocar localStorage', () => {
      const response: UserOut = { id: 1, email: 'user@dyp.com' };
      let emitted: UserOut | undefined;

      service.register('user@dyp.com', 'secret123').subscribe((res: UserOut) => {
        emitted = res;
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/register`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ email: 'user@dyp.com', password: 'secret123' });
      req.flush(response);

      expect(emitted).toEqual(response);
      expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
    });

    it('con 400 propaga el error', () => {
      let errorReceived: unknown;

      service.register('user@dyp.com', 'secret123').subscribe({
        next: () => {
          throw new Error('should not emit a value');
        },
        error: (err: unknown) => {
          errorReceived = err;
        },
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/register`);
      req.flush({ detail: 'email already registered' }, { status: 400, statusText: 'Bad Request' });

      expect(errorReceived).toBeTruthy();
      expect(localStorage.getItem(TOKEN_KEY)).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('true con token válido no expirado', () => {
      localStorage.setItem(TOKEN_KEY, buildJwt(3600));
      expect(service.isAuthenticated()).toBe(true);
    });

    it('false sin token', () => {
      expect(service.isAuthenticated()).toBe(false);
    });

    it('false con token expirado', () => {
      localStorage.setItem(TOKEN_KEY, buildJwt(-3600));
      expect(service.isAuthenticated()).toBe(false);
    });

    it('false con token malformado', () => {
      localStorage.setItem(TOKEN_KEY, 'not-a-valid-jwt');
      expect(service.isAuthenticated()).toBe(false);
    });
  });

  describe('logout', () => {
    it('limpia localStorage', () => {
      localStorage.setItem(TOKEN_KEY, buildJwt(3600));
      service.logout();
      expect(service.getToken()).toBeNull();
    });
  });

  describe('getToken', () => {
    it('devuelve el token almacenado', () => {
      localStorage.setItem(TOKEN_KEY, 'abc.def.ghi');
      expect(service.getToken()).toBe('abc.def.ghi');
    });
  });
});
