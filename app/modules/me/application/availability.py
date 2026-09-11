"""Booking-slot generation for `GET /me/availability` (spec 086).

Nutritionist working hours are entered as local wall-clock time in a single
tenant timezone (`Settings.BOOKING_TIMEZONE`). Slots are generated in that zone,
then returned — and compared against stored appointments — as **naive UTC**,
which is how motor hands appointment datetimes back.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class AvailabilityConfig:
    weekdays: list[int]  # ISO 1..7
    window_start: str  # "HH:MM"
    window_end: str  # "HH:MM"
    slot_minutes: int
    modality: str

    @staticmethod
    def from_profile(profile: dict | None) -> "AvailabilityConfig":
        p = profile or {}
        return AvailabilityConfig(
            weekdays=[int(d) for d in (p.get("booking_weekdays") or [1, 2, 3, 4, 5])],
            window_start=p.get("booking_window_start") or "09:00",
            window_end=p.get("booking_window_end") or "18:00",
            slot_minutes=int(p.get("booking_slot_minutes") or 45),
            modality=p.get("booking_modality") or "both",
        )


def _parse_hhmm(value: str) -> time:
    hh, mm = value.split(":")
    return time(int(hh), int(mm))


def _to_naive_utc(dt: datetime | None) -> datetime | None:
    """A stored appointment datetime → naive UTC (motor returns naive-UTC; a
    tz-aware value gets converted)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def generate_days(
    config: AvailabilityConfig,
    *,
    from_date: date,
    day_count: int,
    busy: list[dict],
    now_utc: datetime,
    tz_name: str = "America/Mexico_City",
) -> list[dict]:
    """Open slots per configured weekday, `[{date, slots: [utc-iso, ...]}]`.

    `slots` are naive-UTC ISO strings (`...Z`-free, minute precision). A day
    with every slot taken still appears (`slots: []`).
    """
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")

    start_t = _parse_hhmm(config.window_start)
    end_t = _parse_hhmm(config.window_end)
    step = timedelta(minutes=config.slot_minutes)
    busy_ranges = [
        (_to_naive_utc(b["start"]), _to_naive_utc(b["end"]))
        for b in busy
        if b.get("start") is not None and b.get("end") is not None
    ]
    now_utc = _to_naive_utc(now_utc)

    out: list[dict] = []
    for offset in range(max(0, day_count)):
        day = from_date + timedelta(days=offset)
        if day.isoweekday() not in config.weekdays:
            continue
        slots: list[str] = []
        cursor_local = datetime.combine(day, start_t, tzinfo=tz)
        day_end_local = datetime.combine(day, end_t, tzinfo=tz)
        while cursor_local + step <= day_end_local:
            slot_start = cursor_local.astimezone(timezone.utc).replace(tzinfo=None)
            slot_end = slot_start + step
            cursor_local += step
            if slot_start <= now_utc:
                continue
            clash = any(
                s is not None and e is not None and s < slot_end and e > slot_start
                for s, e in busy_ranges
            )
            if not clash:
                slots.append(slot_start.isoformat(timespec="minutes"))
        out.append({"date": day.isoformat(), "slots": slots})
    return out
