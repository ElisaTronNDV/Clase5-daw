import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, ValidatorFn, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';

import { ProductService } from '../services/product.service';
import type { ProductCreate, ProductUpdate } from '../models/product.models';

function positiveNumber(): ValidatorFn {
  return (control) => {
    const value = control.value;
    if (value === null || value === undefined || value === '') {
      return null;
    }
    return Number(value) > 0 ? null : { positiveNumber: true };
  };
}

function positiveInteger(): ValidatorFn {
  return (control) => {
    const value = control.value;
    if (value === null || value === undefined || value === '') {
      return null;
    }
    const numericValue = Number(value);
    return Number.isInteger(numericValue) && numericValue > 0 ? null : { positiveInteger: true };
  };
}

@Component({
  selector: 'app-product-form',
  imports: [ReactiveFormsModule],
  templateUrl: './product-form.html',
  styleUrl: './product-form.scss',
})
export class ProductForm implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly productService = inject(ProductService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  private readonly productId = this.route.snapshot.paramMap.get('id');
  readonly isEditMode = this.productId !== null;

  readonly stockComprometido = signal<number | null>(null);
  readonly errorMessage = signal<string | null>(null);

  readonly form = this.fb.group({
    material: ['', [Validators.required]],
    espesor: [null as number | null, [Validators.required, positiveNumber()]],
    largo: [null as number | null, [Validators.required, positiveNumber()]],
    ancho: [null as number | null, [Validators.required, positiveNumber()]],
    stock: [null as number | null, [Validators.required, positiveInteger()]],
    punto_pedido: [null as number | null, [Validators.required, positiveInteger()]],
  });

  ngOnInit(): void {
    if (!this.isEditMode || this.productId === null) {
      return;
    }

    this.productService.getById(Number(this.productId)).subscribe({
      next: (product) => {
        this.form.patchValue({
          material: product.material,
          espesor: product.espesor,
          largo: product.largo,
          ancho: product.ancho,
          stock: product.stock,
          punto_pedido: product.punto_pedido,
        });
        this.stockComprometido.set(product.stock_comprometido);
      },
      error: (err: unknown) => {
        if (err instanceof HttpErrorResponse && err.status === 404) {
          this.errorMessage.set('El producto no existe');
          this.router.navigate(['/inventario']);
        } else {
          this.errorMessage.set('No se pudo cargar el producto');
        }
      },
    });
  }

  onSubmit(): void {
    if (this.form.invalid) {
      return;
    }

    this.errorMessage.set(null);
    const data = this.form.getRawValue() as ProductCreate | ProductUpdate;

    const request$ =
      this.isEditMode && this.productId !== null
        ? this.productService.update(Number(this.productId), data)
        : this.productService.create(data);

    request$.subscribe({
      next: () => this.router.navigate(['/inventario']),
      error: (err: unknown) => {
        if (err instanceof HttpErrorResponse && err.status === 400) {
          this.errorMessage.set('Ya existe un producto con ese material, espesor y dimensiones');
        } else if (err instanceof HttpErrorResponse && err.status === 404) {
          this.errorMessage.set('El producto ya no existe');
          this.router.navigate(['/inventario']);
        } else {
          this.errorMessage.set('No se pudo guardar el producto');
        }
      },
    });
  }
}
