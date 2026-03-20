# Architecture Guardrails

## Purpose

Proteger la arquitectura objetivo del backend mientras se migra desde la estructura actual basada en `routers/`.

## Target Layers

- `app/modules/<feature>/presentation`: HTTP only
- `app/modules/<feature>/application`: use cases and orchestration
- `app/modules/<feature>/domain`: contracts, entities, invariants
- `app/modules/<feature>/infrastructure`: repositories, adapters, integrations
- `app/core/*`: cross-cutting concerns

## Dependency Rules

- presentation -> application
- application -> domain + infrastructure abstractions
- infrastructure -> domain
- domain -> no FastAPI/db/framework imports

## Mandatory Rules

- routers nuevos o refactorizados deben permanecer delgados;
- acceso directo a Mongo debe vivir fuera de `presentation`;
- serialización de respuestas debe estar tipada y no embebida como dicts anónimos en controladores HTTP cuando el módulo ya esté migrado;
- secretos y credenciales salen de código y se inyectan por entorno;
- cambios de arquitectura deben dejar docs y tests.

## Current Exceptions to Migrate

Estas excepciones existen hoy, pero no deben servir como precedente para nuevas implementaciones.
