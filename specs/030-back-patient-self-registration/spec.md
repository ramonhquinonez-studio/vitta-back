# Feature Specification: Patient Self-Registration + Nutritionist Claim by Connection Code

**Feature Branch**: `030-back-patient-self-registration`
**Created**: 2026-08-19
**Status**: Draft
**Type**: Feature

## Objective

Every path to a patient account existed only through a nutritionist first: either the nutritionist created the chart directly (`028-patients-direct-create` in `nutri_pro`), or generated an invite code (scoped or unscoped) for the patient to redeem. A patient who wants to try the app before picking a nutritionist — or whose nutritionist isn't using Vitta yet — had no way to create an account at all, since `POST /auth/register` required `invite_code`.

Let a patient register with no invite code. They get their own chart (`owner_id: null`) plus a short connection code, the mirror image of an invite code: instead of the nutritionist generating a code for the patient, the patient now holds a code they can hand to a nutritionist, who redeems it to add that patient to their roster.

## In Scope

- `Patient.owner_id` becomes nullable. `None` means self-registered, no nutritionist yet — this is a genuinely new state; previously every patient document always had an owner.
- `POST /auth/register`: `invite_code` becomes optional. When omitted/blank, a new user + an ownerless patient chart are created; the chart gets a random 8-character `connection_code` (same alphabet/generator pattern as invite codes).
- `GET /me/profile`: the nested `patient` object gains `connection_code` (null once claimed, or if the account was never self-registered).
- `POST /patients/claim` (nutritionist-authenticated): body `{code}`. Finds the unclaimed patient by connection code, sets `owner_id` to the caller, clears `connection_code`. 404 if the code is unknown or already claimed.

## Out of Scope

- Any UI/consent step on the patient's side for the claim — the connection code itself, shared out-of-band by the patient, is the consent mechanism (same trust model as invite codes, just reversed).
- Un-claiming, or a patient having more than one nutritionist at a time.
- Any change to the existing invite-code flow (`028`/`029`) — both directions coexist independently.

## Baseline Behavior

- `RegisterIn.invite_code` was `Field(..., min_length=4, max_length=40)` — registration was impossible without one.
- `Patient.owner_id: str` was a required dataclass field with no default — every patient document was assumed to have exactly one owner, enforced by every repository method being `*_for_owner`.

## Documentation Impact

- **Global docs to create/update**: `specs/SPEC_ROADMAP.md`
- **Cross-repo impact**: `nutri_app` gains the self-registration form + connection-code display (`035-front-patient-self-registration`), `nutri_pro` gains the claim-by-code UI (`030-patient-self-registration-claim`).

## Acceptance Criteria

1. Given a patient registers with no `invite_code`, when the account is created, then a `patients` document exists with `owner_id: null`, `user_id` set to the new account, and a unique `connection_code`.
2. Given that account's `GET /me/profile`, when read, then `patient.connection_code` is present and `patient.owner_id` is `null`.
3. Given a nutritionist calls `POST /patients/claim` with that code, when it succeeds, then the same patient document now has `owner_id` set to the calling nutritionist, `connection_code` is cleared, and the patient appears in `GET /patients` for that nutritionist — with no duplicate record created.
4. Given the same code is submitted again (by any nutritionist), when claimed, then it's rejected with 404 — a connection code is single-use.
5. Given an invite-code registration (with a code), when it completes, then behavior is byte-for-byte unchanged from before this slice.
6. Given a patient with `owner_id: null` uses the rest of the API (recipe collections, education videos, recommendations, nutritionist profile), when called, then each returns an empty/null result rather than erroring — all of these already null-guarded on `owner_id` before this slice; verified still true.

## Validation

- `PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "test_*.py"` → 100/100 green (5 new tests across `test_auth_service.py` and `test_patients_service.py`).
- Manual: `curl` end-to-end against the live local backend — registered a patient with no invite code, confirmed `owner_id: null` + a real `connection_code` on `/me/profile`; registered a nutritionist, confirmed empty roster; claimed by code (lowercase, confirming case-insensitivity), confirmed same patient id now owned with roster total=1; confirmed the patient's own `/me/profile` now shows `connection_code: null`; confirmed re-claiming the same code and claiming an unknown code both 404.
