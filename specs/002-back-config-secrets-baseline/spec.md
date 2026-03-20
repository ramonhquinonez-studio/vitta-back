# Refactor Specification: Back Config Secrets Baseline

**Feature Branch**: `002-back-config-secrets-baseline`
**Created**: 2026-03-20
**Status**: Draft
**Type**: Refactor

## Objective

Eliminar secretos reales hardcodeados del backend, documentar variables de entorno requeridas y agregar validaciones mínimas para evitar configuraciones inseguras o inconsistentes.

## In Scope

- `app/core/config.py`
- `app/core/notify.py`
- `docs/environments.md`
- `tests/test_config_guardrails.py`
- actualización del hub y tasks del bootstrap

## Out of Scope

- migración modular de `auth` o `appointments`;
- cambios de contrato API;
- integración completa de secrets manager.

## Baseline Behavior

- `config.py` contiene secretos/defaults sensibles en código;
- `main.py` intenta inicializar Firebase siempre;
- no hay tests de seguridad para configuración;
- `.env.example` existe, pero el código no está alineado completamente con ese baseline.

## Target Design

- sin secretos reales en código;
- defaults locales explícitos y seguros;
- validación de secretos placeholders en producción;
- validación de configuración parcial de Google OAuth;
- Firebase opcional en local si no hay archivo de credenciales;
- documentación operativa clara.

## Documentation Impact

- **Module docs to create/update**: `docs/modules/architecture.md`
- **Global docs to create/update**: `docs/README.md`, `docs/environments.md`, `specs/002-back-config-secrets-baseline/*`

## Parity Acceptance Criteria

1. Given local development without Firebase credentials, when the app boots, then config no longer depends on a real secret checked into code.
2. Given production-like config, when placeholders or partial OAuth config are used, then settings validation fails fast.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest tests.test_config_guardrails`
- `PYTHONPATH=. .venv/bin/python -m py_compile app/core/config.py app/core/notify.py`
