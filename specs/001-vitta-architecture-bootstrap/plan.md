# Implementation Plan: Vitta Back Architecture Bootstrap

**Branch**: `001-vitta-architecture-bootstrap` | **Date**: 2026-03-20 | **Spec**: `specs/001-vitta-architecture-bootstrap/spec.md`

## Summary

Crear la base documental y arquitectónica mínima del backend antes de empezar a mover routers y lógica a módulos por feature.

## Technical Context

- **Language**: Python / FastAPI
- **Persistence**: MongoDB via Motor
- **Current Shape**: `routers + schemas + services + core + db`
- **Target Shape**: `modules/<feature>/application/domain/infrastructure/presentation`

## Phases

### Phase 1: SDD Bootstrap

- hub docs;
- policy;
- guardrails;
- spec inicial.

### Phase 2: Security and Core Baseline

- sacar secretos de código;
- documentar variables de entorno requeridas;
- revisar ownership de auth/config.

### Phase 3: Modular Migration

- `auth`
- `appointments`
- `patients`
- `me`
- `plans`

### Phase 4: Tests and Enforcement

- tests de servicios;
- tests de routers;
- guardrails de arquitectura si se automatizan.

## Validation Minimum

- estructura SDD visible en repo;
- guardrails documentados;
- backlog inicial priorizado;
- cero cambio funcional.
