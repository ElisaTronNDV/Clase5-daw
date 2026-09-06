import { Component, EventEmitter, Output, effect, inject, input, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';

import { OrdenService } from '../services/orden.service';
import type {
  OrdenBorrador,
  OrdenConfirmarRequest,
  OrdenResponse,
  PiezaConfirmar,
  ProductoSinCoincidencia,
} from '../models/orden.models';

@Component({
  selector: 'app-revision-borrador',
  imports: [ReactiveFormsModule],
  templateUrl: './revision-borrador.html',
  styleUrl: './revision-borrador.scss',
})
export class RevisionBorrador {
  private readonly fb = inject(FormBuilder);
  private readonly ordenService = inject(OrdenService);

  readonly borrador = input.required<OrdenBorrador>();
  readonly indiceActual = input<number>(0);
  readonly totalPaginas = input<number>(1);

  /** Se emite cuando la orden de esta página quedó confirmada (201), para que el orquestador avance. */
  @Output() readonly confirmada = new EventEmitter<OrdenResponse>();

  readonly errorMessage = signal<string | null>(null);
  readonly productoNoEncontrado = signal<ProductoSinCoincidencia | null>(null);
  readonly ordenConfirmada = signal<OrdenResponse | null>(null);
  readonly enviando = signal(false);

  readonly form = this.fb.group({
    material: ['', [Validators.required]],
    multiplicidad: [1 as number | null, [Validators.required]],
    espesor: [null as number | null, [Validators.required]],
    largo: [null as number | null, [Validators.required]],
    ancho: [null as number | null, [Validators.required]],
    indice_formato: [null as string | null],
    tiempo_ejecucion_estimado: [null as string | null],
  });

  constructor() {
    // Precarga el formulario con los datos extraídos cada vez que cambia el borrador (nueva página).
    effect(() => {
      const b = this.borrador();
      this.form.reset({
        material: b.material,
        multiplicidad: b.multiplicidad,
        espesor: b.espesor,
        largo: b.largo,
        ancho: b.ancho,
        indice_formato: b.indice_formato,
        tiempo_ejecucion_estimado: b.tiempo_ejecucion_estimado,
      });
      this.errorMessage.set(null);
      this.productoNoEncontrado.set(null);
      this.ordenConfirmada.set(null);
    });
  }

  onSubmit(): void {
    this.enviar(false);
  }

  onCrearProductoYConfirmar(): void {
    this.enviar(true);
  }

  private enviar(crearProductoAutomaticamente: boolean): void {
    if (this.form.invalid) {
      return;
    }

    this.errorMessage.set(null);
    this.enviando.set(true);

    const v = this.form.getRawValue();
    const piezas: PiezaConfirmar[] = this.borrador().piezas.map((p) => ({
      ref: p.ref,
      cantidad: p.cantidad,
      pieza: p.pieza,
      descripcion: p.descripcion,
      es_recorte: p.es_recorte,
      largo_mm: p.largo_mm,
      ancho_mm: p.ancho_mm,
    }));

    const payload: OrdenConfirmarRequest = {
      indice_formato: v.indice_formato ?? null,
      multiplicidad: v.multiplicidad as number,
      material: v.material as string,
      espesor: v.espesor as number,
      largo: v.largo as number,
      ancho: v.ancho as number,
      tiempo_ejecucion_estimado: v.tiempo_ejecucion_estimado ?? null,
      piezas,
      crear_producto_automaticamente: crearProductoAutomaticamente,
    };

    this.ordenService.confirmarOrden(payload).subscribe({
      next: (res) => {
        this.enviando.set(false);
        this.productoNoEncontrado.set(null);
        this.ordenConfirmada.set(res);
        this.confirmada.emit(res);
      },
      error: (err: unknown) => {
        this.enviando.set(false);
        if (err instanceof HttpErrorResponse && err.status === 409) {
          this.productoNoEncontrado.set(err.error as ProductoSinCoincidencia);
        } else if (err instanceof HttpErrorResponse && err.status === 422) {
          this.errorMessage.set('Los datos de la orden no son válidos. Revisá los campos.');
        } else {
          this.errorMessage.set('No se pudo confirmar la orden. Intentá nuevamente.');
        }
      },
    });
  }
}
