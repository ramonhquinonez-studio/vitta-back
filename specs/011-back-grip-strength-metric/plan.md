# Implementation Plan: Back Grip Strength Metric

**Branch**: `011-back-grip-strength-metric` | **Date**: 2026-08-12 | **Spec**: `specs/011-back-grip-strength-metric/spec.md`

## Summary

Agregar dos campos opcionales más al mismo `metrics` dict que ya usa InBody, sin tocar arquitectura ni endpoints nuevos.

## Steps

1. `app/schemas/body_composition.py`: `grip_strength_left_kg`/`grip_strength_right_kg`.
2. `app/modules/patients/presentation/router.py`: dos `Form(None)` más en `add_patient_body_composition`, incluidos en el dict de `metrics`.
3. `seed_dev.py`: valores demo crecientes en los 4 escaneos ya sembrados.

## Constraints

- Sin nueva colección, sin nuevo endpoint, sin nuevo adjunto: reutiliza exactamente la infraestructura de InBody.
