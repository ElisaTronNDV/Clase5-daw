import { Component, computed, signal } from '@angular/core';

import { SubirArchivo } from './subir-archivo/subir-archivo';
import { RevisionBorrador } from './revision-borrador/revision-borrador';
import { ListadoOrdenes } from './listado-ordenes/listado-ordenes';
import type { OrdenBorrador } from './models/orden.models';

type Vista = 'subir' | 'revision' | 'listado';

@Component({
  selector: 'app-oficina',
  imports: [SubirArchivo, RevisionBorrador, ListadoOrdenes],
  templateUrl: './oficina.html',
  styleUrl: './oficina.scss',
})
export class Oficina {
  readonly vista = signal<Vista>('subir');
  readonly borradores = signal<OrdenBorrador[]>([]);
  readonly indiceActual = signal(0);

  readonly borradorActual = computed(() => this.borradores()[this.indiceActual()]);

  onPaginasExtraidas(paginas: OrdenBorrador[]): void {
    if (paginas.length === 0) {
      return;
    }
    this.borradores.set(paginas);
    this.indiceActual.set(0);
    this.vista.set('revision');
  }

  onOrdenConfirmada(): void {
    const siguiente = this.indiceActual() + 1;
    if (siguiente < this.borradores().length) {
      this.indiceActual.set(siguiente);
    } else {
      this.vista.set('listado');
    }
  }

  irAListado(): void {
    this.vista.set('listado');
  }

  nuevaCarga(): void {
    this.borradores.set([]);
    this.indiceActual.set(0);
    this.vista.set('subir');
  }
}
