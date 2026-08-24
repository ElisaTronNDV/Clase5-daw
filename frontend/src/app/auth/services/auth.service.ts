import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import type { LoginRequest, RegisterRequest, TokenResponse, UserOut } from '../models/auth.models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly TOKEN_KEY = 'dyp_lasercore_token';

  login(email: string, password: string): Observable<TokenResponse> {
    const body: LoginRequest = { email, password };
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/login`, body)
      .pipe(tap((response) => localStorage.setItem(this.TOKEN_KEY, response.access_token)));
  }

  register(email: string, password: string): Observable<UserOut> {
    const body: RegisterRequest = { email, password };
    return this.http.post<UserOut>(`${environment.apiUrl}/auth/register`, body);
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) {
      return false;
    }

    try {
      const payloadSegment = token.split('.')[1];
      const normalized = payloadSegment.replace(/-/g, '+').replace(/_/g, '/');
      const payload = JSON.parse(atob(normalized));
      const exp = payload?.exp;
      if (typeof exp !== 'number') {
        return false;
      }
      return exp > Date.now() / 1000;
    } catch {
      return false;
    }
  }
}
