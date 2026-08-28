# Tasks: Fix Push Notification SDK Call

## Phase 1: SDD

- [x] T001 Crear spec, plan y tasks del slice.

## Phase 2: Implementation

- [x] T002 `app/core/notify.py`: `send_multicast` → `send_each_for_multicast`.
- [x] T003 `tests/test_notify.py` nuevo (3 tests).

## Phase 3: Validation

- [x] T004 `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 230/230 verde.
- [x] T005 Verificación en vivo: `POST /devices/test` con un token de prueba real registrado → `200 {"ok":true,"sent_to":1}` (antes: `500`). Registro de dispositivo de prueba eliminado tras la verificación.

## Evidence

- Suite completa: 230/230 verde (227 previos + 3 nuevos).
- En vivo, contra el servidor local (con `firebase-service-account.json` real configurado): `POST /devices/register` → `{"ok":true}`; `POST /devices/test` → `{"ok":true,"sent_to":1}`. Dispositivo de prueba eliminado.
