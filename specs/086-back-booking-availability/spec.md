# Feature Specification: Nutritionist booking availability

**Feature Branch**: `feat/booking-availability`
**Created**: 2026-09-10
**Status**: Done — 324 unittests green
**Type**: Feature (small)

## Objective

Replace the patient booking sheet's **fabricated static slot grid** (`nutri_app`
`booking_sheet.dart`'s `_slotsByPeriod`) with the nutritionist's *real* open
times: their configured working window, minus the slots already taken by live
appointments. Consumed by `nutri_app` `075`.

## Data — `NutritionistProfile`

New fields (all with sensible defaults, no migration):

| field | default | meaning |
|---|---|---|
| `booking_modality` | `"both"` | `online` \| `onsite` \| `both` — which the patient may pick |
| `booking_weekdays` | `[1,2,3,4,5]` | ISO weekdays the nutritionist takes appointments |
| `booking_window_start` | `"09:00"` | daily start (local `HH:MM`) |
| `booking_window_end` | `"18:00"` | daily end |
| `booking_slot_minutes` | `45` | slot length (matches the appointment default) |

`NutritionistProfileUpdate` validates: weekdays ∈ 1..7 & non-empty, `HH:MM`
24h format, end > start, `15 ≤ slot_minutes ≤ 180`. All exposed on
`GET /nutritionist_profile/me` and `GET /me/nutritionist_profile`.

## API — `GET /me/availability`

Patient-scoped. Query: `from` (date, default today), `days` (1..60, default 21).

```json
{
  "slot_minutes": 45,
  "modality": "both",
  "days": [
    { "date": "2026-09-15", "slots": ["2026-09-15T15:00", "2026-09-15T15:45"] }
  ]
}
```

- Only configured weekdays appear; a fully-booked day still appears with
  `slots: []`.
- Slots are **naive-UTC** ISO strings (minute precision). Working hours are
  interpreted in `Settings.BOOKING_TIMEZONE` (`America/Mexico_City`, single
  tenant tz for now — a per-nutritionist tz is a later refinement), converted to
  UTC for the response and for overlap comparison against stored appointments.
- A slot is dropped when it overlaps any `pending`/`confirmed` appointment of the
  nutritionist (`list_owner_appointments_between`), or is in the past.
- 404 when the patient has no linked account; 400 with no assigned nutritionist.

## Out of scope

- Per-nutritionist timezone. Recurring exceptions / holidays / one-off blocks.
- Enforcing availability at `POST /me/appointments` (still overlap-only) — the
  sheet just won't *offer* a bad slot.
- A nutritionist-facing availability config UI (`nutri_pro`) — a follow-up;
  defaults apply until then.

## Acceptance criteria

1. `GET /me/availability` returns slots generated from the window, in UTC.
2. A slot overlapping a live appointment is absent.
3. Non-configured weekdays are absent; past slots are absent.
4. `PATCH /nutritionist_profile/me` persists the 5 fields with validation.
5. Full unittest suite green.

## Docs

`specs/SPEC_ROADMAP.md` here; `.env.example` (`BOOKING_TIMEZONE`). Cross-repo:
`nutri_app` `075`. `nutri_pro` config UI: deferred follow-up.
