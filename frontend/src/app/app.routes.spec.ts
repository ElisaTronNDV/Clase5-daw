import { routes } from './app.routes';
import { authGuard } from './auth/guards/auth.guard';

describe('routes', () => {
  it('define /login y /register como públicas, sin authGuard', () => {
    const loginRoute = routes.find((r) => r.path === 'login');
    const registerRoute = routes.find((r) => r.path === 'register');

    expect(loginRoute).toBeTruthy();
    expect(registerRoute).toBeTruthy();
    expect(loginRoute?.canActivate ?? []).not.toContain(authGuard);
    expect(registerRoute?.canActivate ?? []).not.toContain(authGuard);
  });

  it('la ruta raíz "" está protegida por authGuard', () => {
    const rootRoute = routes.find((r) => r.path === '');

    expect(rootRoute).toBeTruthy();
    expect(rootRoute?.canActivate).toContain(authGuard);
  });

  it('oficina/taller/inventario/configuracion son hijas de la ruta protegida, sin restricción adicional', () => {
    const rootRoute = routes.find((r) => r.path === '');
    const children = rootRoute?.children ?? [];
    const childPaths = children.map((c) => c.path);

    expect(childPaths).toEqual(
      expect.arrayContaining(['oficina', 'taller', 'inventario', 'configuracion']),
    );

    for (const modulePath of ['oficina', 'taller', 'inventario', 'configuracion']) {
      const child = children.find((c) => c.path === modulePath);
      expect(child?.canActivate ?? []).toHaveLength(0);
    }
  });

  it('inventario/nuevo e inventario/:id/editar están definidas como hijas de la ruta protegida, sin canActivate propio', () => {
    const rootRoute = routes.find((r) => r.path === '');
    const children = rootRoute?.children ?? [];

    const nuevoRoute = children.find((c) => c.path === 'inventario/nuevo');
    const editarRoute = children.find((c) => c.path === 'inventario/:id/editar');

    expect(nuevoRoute).toBeTruthy();
    expect(editarRoute).toBeTruthy();
    expect(nuevoRoute?.canActivate ?? []).toHaveLength(0);
    expect(editarRoute?.canActivate ?? []).toHaveLength(0);
  });

  it('la ruta comodín "**" redirige a la raíz', () => {
    const wildcard = routes.find((r) => r.path === '**');

    expect(wildcard?.redirectTo).toBe('/');
  });
});
