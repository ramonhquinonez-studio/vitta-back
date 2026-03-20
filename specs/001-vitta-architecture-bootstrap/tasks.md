# Tasks: Vitta Back Architecture Bootstrap

## Phase 1: SDD Bootstrap

- [x] T001 Crear `docs/`, `docs/modules/`, `docs/architecture/`, `specs/`, `.specify/templates/`.
- [x] T002 Documentar política SDD del backend.
- [x] T003 Documentar guardrails y arquitectura objetivo.
- [x] T004 Crear spec inicial de bootstrap.

## Phase 2: Core and Security Backlog

- [ ] T005 Remover secretos hardcodeados de `app/core/config.py`.
- [ ] T006 Documentar variables de entorno obligatorias.
- [ ] T007 Definir estrategia de composición para módulos nuevos.

## Phase 3: Modular Migration Backlog

- [ ] T008 Crear módulo `auth` en `app/modules/`.
- [ ] T009 Crear módulo `appointments` en `app/modules/`.
- [ ] T010 Crear módulo `patients` en `app/modules/`.
- [ ] T011 Crear módulo `me` en `app/modules/`.
- [ ] T012 Crear módulo `plans` en `app/modules/`.

## Phase 4: Validation

- [ ] T013 Agregar suite de tests backend.
- [ ] T014 Definir evidencia mínima por refactor.
