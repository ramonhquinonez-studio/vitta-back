# Implementation Plan: Back Test Foundation

**Branch**: `008-back-test-foundation` | **Date**: 2026-03-20 | **Spec**: `specs/008-back-test-foundation/spec.md`

## Summary

Convertir la colección actual de tests en una base explícita y reusable, con guardrails sobre wrappers legacy y smoke tests de routers modulares.

## Steps

1. Agregar tests de guardrail para wrappers de `app/routers/`.
2. Agregar smoke tests para routers modulares principales.
3. Documentar comando de ejecución y estado de la base.
4. Validar con `unittest discover`.

## Constraints

- no cambiar el runtime de tests;
- mantener la suite ligera y local, sin levantar servicios externos.
