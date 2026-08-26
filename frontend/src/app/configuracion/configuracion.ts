import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, ValidatorFn, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';

import { ConfiguracionService } from './services/configuracion.service';
import type { ConfiguracionUpdate } from './models/configuracion.models';

const DEFAULT_MARGEN_TOLERANCIA = 1.0;

function positiveNumber(): ValidatorFn {
  return (control) => {
    const value = control.value;
    if (value === null || value === undefined || value === '') {
      return null;
    }
    return Number(value) > 0 ? null : { positiveNumber: true };
  };
}

@Component({
  selector: 'app-configuracion',
  imports: [ReactiveFormsModule],
  templateUrl: './configuracion.html',
})
export class Configuracion implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly configuracionService = inject(ConfiguracionService);

  readonly errorMessage = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly form = this.fb.group({
    margen_tolerancia_dimensional: [
      DEFAULT_MARGEN_TOLERANCIA as number | null,
      [Validators.required, positiveNumber()],
    ],
  });

  ngOnInit(): void {
    this.configuracionService.get().subscribe({
      next: (config) => {
        this.form.patchValue({
          margen_tolerancia_dimensional: config.margen_tolerancia_dimensional,
        });
      },
      error: () => {
        // El backend siempre responde 200 con al menos el default (RF-02); si igual falla
        // (ej. red), se mantiene el default visual ya precargado en el form.
      },
    });
  }

  onSubmit(): void {
    if (this.form.invalid) {
      return;
    }

    this.errorMessage.set(null);
    this.successMessage.set(null);
    const data = this.form.getRawValue() as ConfiguracionUpdate;

    this.configuracionService.update(data).subscribe({
      next: () => {
        this.successMessage.set('Configuración guardada correctamente');
      },
      error: (err: unknown) => {
        if (err instanceof HttpErrorResponse && err.status === 422) {
          this.errorMessage.set('El valor ingresado no es válido, debe ser un número mayor a 0');
        } else {
          this.errorMessage.set('No se pudo guardar la configuración');
        }
      },
    });
  }
}
