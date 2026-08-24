import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-register',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrl: './register.scss',
})
export class Register {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  readonly errorMessage = signal<string | null>(null);

  onSubmit(): void {
    if (this.form.invalid) {
      return;
    }

    this.errorMessage.set(null);
    const { email, password } = this.form.getRawValue();

    this.authService.register(email, password).subscribe({
      next: () => this.router.navigate(['/login']),
      error: (err: unknown) => {
        if (err instanceof HttpErrorResponse && err.status === 400) {
          this.errorMessage.set('Ese email ya está registrado');
        } else if (err instanceof HttpErrorResponse && err.status === 422) {
          this.errorMessage.set('La contraseña debe tener al menos 8 caracteres');
        } else {
          this.errorMessage.set('No se pudo completar el registro');
        }
      },
    });
  }
}
