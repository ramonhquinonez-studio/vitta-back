# Implementation Plan: Session Photo on a Logged Workout Entry

**Feature Branch**: `062-back-workout-log-session-photo`

## Summary

Adds an optional photo to the per-exercise `workout_logs` document via a dedicated upload endpoint plus two new fields threaded through the existing upsert/read paths.

## Steps

1. **`app/schemas/workout_log.py`**: `WorkoutExerciseLogIn` gains `photo_url: Optional[str] = None`, `photo_content_type: Optional[str] = None`.
2. **`app/modules/me/presentation/router.py`**: new `POST /workout-logs/photo` — `file: UploadFile = File(...)`, `save_upload(file, subfolder=f"workout_logs/{_user_id(current)}")`, returns `{"photo_url", "content_type"}`. No repository write.
3. **`app/modules/me/application/me_service.py`** `upsert_workout_log`: passes `photo_url`/`photo_content_type` from the payload through to the repository.
4. **`app/modules/me/domain/repositories.py`** `MeRepository.upsert_workout_log`: signature gains the two optional params.
5. **`app/modules/me/infrastructure/mongo_me_repository.py`**: `upsert_workout_log`'s `$set` includes both fields (full-replace-on-every-write, same convention `sets`/`comment` already use); `_serialize_workout_log` returns both.
6. **`app/modules/patients/infrastructure/mongo_patients_repository.py`** `list_workout_logs` (coach read-side inline dict): adds both fields — read-only mirror, no write path.
7. **Tests**: `tests/test_me_service.py`'s `_FakeMeRepository.upsert_workout_log` accepts and returns the new fields; existing `test_upsert_workout_log_persists_a_sets_list` etc. unaffected since the fields default to `None`. `tests/test_patients_service.py` unaffected — its fake sits above the real serializer.
8. **Live verification**: round-trip against the running local server using the seeded demo accounts and a throwaway workout plan; clean up afterward (see spec's Validation section for the exact sequence and the unrelated role-mismatch aside found along the way).

## Constraints

- No content-type gate on the new upload endpoint (mirrors `POST /me/measurements`, not `POST /me/messages/attachment`).
- No document migration — missing fields read as `null`.
