import { Component, EventEmitter, Output, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

import { OrdenService } from '../services/orden.service';
import type { OrdenBorrador } from '../models/orden.models';

@Component({
  selector: 'app-subir-archivo',
  templateUrl: './subir-archivo.html',
  styleUrl: './subir-archivo.scss',
})
export class SubirArchivo {
  private readonly ordenService = inject(OrdenService);

  readonly errorMessage = signal<string | null>(null);
  readonly cargando = signal(false);

  @Output() readonly paginasExtraidas = new EventEmitter<OrdenBorrador[]>();

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    if (!file) {
      return;
    }

    // Validación de extensión en cliente: es solo UX; el servidor revalida extensión,
    // magic bytes y tamaño.
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      this.errorMessage.set('El archivo debe ser un PDF (.pdf).');
      return;
    }

    this.errorMessage.set(null);
    this.cargando.set(true);

    this.ordenService.subirArchivo(file).subscribe({
      next: (res) => {
        this.cargando.set(false);
        this.paginasExtraidas.emit(res.paginas);
      },
      error: (err: unknown) => {
        this.cargando.set(false);
        if (err instanceof HttpErrorResponse && err.status === 422) {
          const detail = err.error?.detail;
          this.errorMessage.set(
            typeof detail === 'string'
              ? detail
              : 'El archivo de corte no pudo procesarse. Revisá que sea un PDF válido de Salvagnini.',
          );
        } else if (err instanceof HttpErrorResponse && err.status === 413) {
          this.errorMessage.set('El archivo supera el tamaño máximo permitido (10 MB).');
        } else if (err instanceof HttpErrorResponse && err.status === 400) {
          const detail = err.error?.detail;
          this.errorMessage.set(
            typeof detail === 'string' ? detail : 'El archivo no es un PDF válido.',
          );
        } else {
          this.errorMessage.set('No se pudo subir el archivo. Intentá nuevamente.');
        }
      },
    });
  }
}
