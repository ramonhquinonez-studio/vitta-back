# SDD Documentation Policy

## Objetivo

Hacer obligatoria la documentación arquitectónica y operativa del backend en el mismo cambio donde se modifica código.

## Regla Base

Todo cambio debe responder:

1. `¿Qué cambió en contrato, comportamiento o arquitectura?`
2. `¿Dónde quedó documentado?`

## Cambios que Obligan Documentación

- feature nuevo;
- bugfix;
- refactor;
- cambio de contrato API;
- cambio de seguridad, auth o sesión;
- cambio de integración externa;
- cambio de arquitectura por módulos;
- cambio operativo o de despliegue.

## Entregables Mínimos

- `specs/<id>/spec.md`
- `plan.md`
- `tasks.md`
- actualización de `docs/modules/` o `docs/architecture/`

## Reglas Arquitectónicas Vigentes

- `presentation`: HTTP only, request parsing, auth, response mapping;
- `application`: business logic and orchestration;
- `domain`: contracts and core entities/rules;
- `infrastructure`: persistence and external integrations;
- no acceso directo a DB desde routers nuevos o refactorizados;
- no secretos en código.
