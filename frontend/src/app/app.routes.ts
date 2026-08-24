import { Routes } from '@angular/router';

import { authGuard } from './auth/guards/auth.guard';
import { Login } from './auth/login/login';
import { Register } from './auth/register/register';
import { Shell } from './shared/shell/shell';
import { Home } from './home/home';
import { Oficina } from './oficina/oficina';
import { Taller } from './taller/taller';
import { Inventario } from './inventario/inventario';
import { Configuracion } from './configuracion/configuracion';

export const routes: Routes = [
  { path: 'login', component: Login },
  { path: 'register', component: Register },
  {
    path: '',
    component: Shell,
    canActivate: [authGuard],
    children: [
      { path: '', component: Home },
      { path: 'oficina', component: Oficina },
      { path: 'taller', component: Taller },
      { path: 'inventario', component: Inventario },
      { path: 'configuracion', component: Configuracion },
    ],
  },
  { path: '**', redirectTo: '/' },
];
