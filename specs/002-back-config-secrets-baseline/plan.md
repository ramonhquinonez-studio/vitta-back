# Implementation Plan: Back Config Secrets Baseline

**Branch**: `002-back-config-secrets-baseline` | **Date**: 2026-03-20 | **Spec**: `specs/002-back-config-secrets-baseline/spec.md`

## Summary

Cerrar la deuda más sensible del backend antes de refactors por módulos: secretos reales en código y validación débil de entorno.

## Steps

1. Reemplazar defaults sensibles por placeholders seguros.
2. Validar producción vs local en `Settings`.
3. Validar configuración consistente de Google OAuth.
4. Hacer Firebase opcional cuando faltan credenciales locales.
5. Documentar variables de entorno.
6. Agregar tests de configuración.
