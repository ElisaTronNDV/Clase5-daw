import { Component, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { debounceTime } from 'rxjs';

import { OrdenService } from '../services/orden.service';
import type { OrdenListItem } from '../models/orden.models';

const DEBOUNCE_MS = 300;

@Component({
  selector: 'app-listado-ordenes',
  imports: [ReactiveFormsModule, DatePipe],
  templateUrl: './listado-ordenes.html',
  styleUrl: './listado-ordenes.scss',
})
export class ListadoOrdenes implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly ordenService = inject(OrdenService);

  readonly ordenes = signal<OrdenListItem[]>([]);
  readonly errorMessage = signal<string | null>(null);

  readonly filtros = this.fb.group({
    estado: [''],
    nest: [''],
  });

  constructor() {
    this.filtros.valueChanges
      .pipe(debounceTime(DEBOUNCE_MS), takeUntilDestroyed())
      .subscribe(() => this.cargar());
  }

  ngOnInit(): void {
    this.cargar();
  }

  descargar(id: number): void {
    this.ordenService.descargarDocumento(id).subscribe({
      next: (blob) => this.dispararDescarga(blob, id),
      error: () => this.errorMessage.set('No se pudo descargar el documento de la orden.'),
    });
  }

  private cargar(): void {
    const { estado, nest } = this.filtros.getRawValue();
    this.ordenService.listarOrdenes(estado || undefined, nest || undefined).subscribe({
      next: (res) => {
        this.errorMessage.set(null);
        this.ordenes.set(res.ordenes);
      },
      error: () => this.errorMessage.set('No se pudieron cargar las órdenes.'),
    });
  }

  private dispararDescarga(blob: Blob, id: number): void {
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = `orden-${id}.pdf`;
    document.body.appendChild(enlace);
    enlace.click();
    document.body.removeChild(enlace);
    URL.revokeObjectURL(url);
  }
}
