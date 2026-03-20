# Environments

## Objetivo

Definir la configuración mínima requerida para correr `nutri_back` sin depender de secretos embebidos en código.

## Fuente Canónica

- usa `.env.example` como punto de partida;
- copia a `.env` solo en tu entorno local;
- en staging/prod inyecta variables desde la plataforma, no desde archivos commiteados.

## Variables Requeridas

### Core

- `APP_ENV`
- `MONGO_URI`
- `MONGO_DB`
- `JWT_SECRET`
- `JWT_REFRESH_SECRET`

### Opcionales / Integraciones

- `CORS_ORIGINS`
- `FIREBASE_CREDENTIALS_PATH`
- `NOTIFY_BEFORE_MINUTES`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `GOOGLE_SCOPES`
- `APP_OAUTH_SUCCESS_REDIRECT`

## Reglas

- en `local`, los placeholders dev son aceptables para JWT mientras no se expongan fuera del equipo;
- en `staging/prod`, `JWT_SECRET` y `JWT_REFRESH_SECRET` no pueden usar placeholders;
- `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` deben definirse juntos o ambos vacíos;
- si `FIREBASE_CREDENTIALS_PATH` no existe localmente, Firebase admin queda deshabilitado en vez de exigir un archivo falso.
