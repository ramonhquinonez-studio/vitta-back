# Feature Specification: Delete a measurement entry (undo-last-save)

**Feature Branch**: `feat/delete-measurement-entry`
**Created**: 2026-09-14
**Status**: Done — 349 unittests green
**Type**: Feature (small — undo action)

## Objective

Direct user request while reviewing the body-figure feature: "what else do
you recommend to improve this feature?" → agreed follow-up "no way to fix a
bad entry — every save just appends, there's no edit/delete." Rather than a
full history-editing UI, this ships the minimal high-value slice: undo the
entry you *just* saved, via a "Deshacer" action on the save confirmation
snackbar in both clients. Consumed by `nutri_app` and `nutri_pro`'s
body-figure entry-UX work (specs 072/113 follow-ups).

## Endpoints

- `DELETE /me/measurements/{entry_id}` (patient-scoped) — 204 on success,
  404 if the entry doesn't exist or doesn't belong to the calling patient.
  Deletes from the shared `measurements` collection (same one `POST
  /me/measurements` and `POST /me/body-measurements` write to — weight/photo
  entries and circumference-only entries are the same document shape), so
  this works for either kind.
- `DELETE /patients/{patient_id}/measurements/{entry_id}` (nutritionist-
  scoped) — 204 on success; 404 if the patient isn't owned by the caller, or
  if the entry doesn't belong to that patient.

Both filter the delete by the owning patient's id (not just the entry's own
`_id`), so a client can never delete another patient's entry even by
guessing a valid ObjectId.

## Data

No schema change — deletes an existing `measurements` document by `_id`.

## Acceptance criteria

1. `DELETE /me/measurements/{id}` removes the entry and is idempotent-safe
   (a second call 404s rather than erroring).
2. `DELETE /patients/{id}/measurements/{entry_id}` requires the calling
   nutritionist to own the patient; rejects otherwise.
3. Full unittest suite green.

## Docs

`specs/SPEC_ROADMAP.md` here. Cross-repo: `nutri_app`'s
`072-front-body-figure-measurements` "Fix — ... a real multi-step sheet /
what else can we improve" addenda, `nutri_pro`'s
`113-front-body-figure-measurements` equivalent.
