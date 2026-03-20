# Refactor Specification: Back Test Foundation

**Feature Branch**: `008-back-test-foundation`
**Created**: 2026-03-20
**Status**: Draft
**Type**: Refactor

## Objective

Dejar una base mínima de tests y guardrails para `nutri_back` que proteja la modularización ya aplicada y facilite nuevos slices sin regresiones estructurales.

## In Scope

- formalizar una suite discoverable de `unittest`;
- agregar guardrail para routers legacy wrapper;
- agregar smoke tests para routers modulares principales;
- documentar cómo correr la suite;
- actualizar roadmap y docs.

## Out of Scope

- migrar toda la suite a `pytest`;
- crear integración HTTP end-to-end;
- cubrir exhaustivamente todos los repositorios con tests nuevos.

## Baseline Behavior

- ya existen tests unitarios por servicio, pero no hay smoke/guardrails del backend modular;
- no hay guía explícita de ejecución de suite en docs;
- los wrappers de `app/routers/*.py` no están protegidos por tests.

## Target Design

- `unittest discover` debe ser el comando base reproducible;
- la suite debe fallar si un router legacy vuelve a crecer con lógica propia;
- la suite debe validar que los routers modulares críticos se pueden importar y exponen rutas;
- la documentación debe reflejar la base de testing actual.

## Documentation Impact

- **Module docs to create/update**: `docs/modules/architecture.md`
- **Global docs to create/update**: `docs/README.md`, `specs/008-back-test-foundation/*`

## Parity Acceptance Criteria

1. Given the current backend, when `unittest discover` runs, then the suite passes.
2. Given a future regression where a legacy router wrapper gains logic again, when guardrails run, then the suite fails.
3. Given the modular routers, when smoke tests run, then the suite confirms they are importable and expose routes.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`
