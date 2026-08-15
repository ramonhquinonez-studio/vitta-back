# Feature Specification: Back Grip Strength Metric

**Feature Branch**: `011-back-grip-strength-metric`
**Created**: 2026-08-12
**Status**: Draft
**Type**: Feature

## Objective

El nutriólogo mide la fuerza de agarre (izquierda/derecha, en kg) con un dinamómetro en cada cita, inmediatamente después del escaneo InBody. Se agrega como dos campos más de `body_compositions.metrics`, en vez de crear una entidad nueva, porque siempre se captura en la misma visita que el InBody y no genera un documento propio que adjuntar.

## In Scope

- `BodyCompositionMetrics.grip_strength_left_kg` / `grip_strength_right_kg`.
- Los mismos dos campos como `Form(None)` en `POST /patients/{id}/body_compositions`.
- Datos demo en `seed_dev.py` (progresión creciente a lo largo de los 4 escaneos ya sembrados).

## Out of Scope

- Una colección/entidad separada para fuerza (decidido explícitamente en contra: siempre se mide junto al InBody).
- Adjuntar un documento propio del dinamómetro (el instrumento solo da números, sin reporte imprimible).

## Baseline Behavior

- `body_compositions.metrics` no tenía ningún campo de fuerza; no había manera de registrar esta medición en absoluto.

## Target Design

- Mismo patrón que el resto de `metrics`: opcional, `float | None`, pasa por el filtro `if value is not None` antes de guardarse.

## Documentation Impact

- **Global docs to create/update**: `specs/011-back-grip-strength-metric/*`, `specs/SPEC_ROADMAP.md`.

## Parity Acceptance Criteria

1. Given un pro sube un escaneo con `grip_strength_left_kg`/`grip_strength_right_kg`, when se guarda, then ambos valores quedan en `metrics` del `body_compositions` creado.
2. Given un escaneo sin esos campos, when se guarda, then no aparecen en `metrics` (comportamiento ya existente para campos opcionales no enviados).

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"`
