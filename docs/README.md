# Vitta Nutri Back Documentation Hub

Esta carpeta centraliza la documentación funcional, arquitectónica y operativa del backend `nutri_back`.

## Objetivo

Llevar `nutri_back` a una base modular similar a `fidelity_back`:

- módulos por feature;
- capas `application/domain/infrastructure/presentation`;
- routers delgados;
- reglas de negocio en services/use cases;
- repositorios/adapters en infraestructura;
- SDD y documentación obligatoria.

## Estado Actual

El backend hoy tiene una base funcional, pero todavía opera principalmente con:

- `routers/` que concentran HTTP + reglas + acceso a DB + serialización;
- ausencia de estructura modular por feature;
- ausencia de docs de arquitectura y specs;
- ausencia de tests visibles en repo;
- secretos configurados en código.

## Test Foundation

La base actual de tests se ejecuta con:

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`

La suite cubre:

- unit tests de servicios modulares;
- guardrails para wrappers legacy de `app/routers/`;
- smoke tests de routers modulares.

## Jerarquía Canónica

1. `docs/modules/*.md`
2. `docs/architecture/ARCHITECTURE_GUARDRAILS.md`
3. `docs/SDD_DOCUMENTATION_POLICY.md`
4. `specs/<id>/spec.md`, `plan.md`, `tasks.md`
5. `README.md`

## Mapa Inicial

- [architecture](modules/architecture.md)
- [guardrails](architecture/ARCHITECTURE_GUARDRAILS.md)
- [environments](environments.md)

## Spec Activo Inicial

- `specs/001-vitta-architecture-bootstrap/`
