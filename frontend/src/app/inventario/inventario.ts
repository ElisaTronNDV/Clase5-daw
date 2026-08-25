import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ProductService } from './services/product.service';
import type { ProductOut } from './models/product.models';

@Component({
  selector: 'app-inventario',
  imports: [RouterLink],
  templateUrl: './inventario.html',
  styleUrl: './inventario.scss',
})
export class Inventario implements OnInit {
  private readonly productService = inject(ProductService);

  readonly products = signal<ProductOut[]>([]);

  ngOnInit(): void {
    this.productService.list().subscribe((products) => this.products.set(products));
  }
}
