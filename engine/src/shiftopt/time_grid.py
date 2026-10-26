HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
HOURS_PER_WEEK = HOURS_PER_DAY * DAYS_PER_WEEK


def hour_of_week(day: int, hour: int) -> int:
    """Cyclic hour-of-week index; day 0 is Monday and hour may exceed 23."""
    return (day * HOURS_PER_DAY + hour) % HOURS_PER_WEEK


def shift_hours(day: int, start_hour: int, length: int) -> tuple[int, ...]:
    """Hour-of-week indexes a shift occupies. Overnight shifts spill into the next day and
    the last day of the week wraps to hour 0 because the roster repeats weekly."""
    return tuple(hour_of_week(day, start_hour + offset) for offset in range(length))


def covers_hour(hour: int, start_hour: int, length: int, period: int) -> bool:
    """Coverage coefficient a_tj of the cyclic set covering model: True when a shift starting at
    start_hour with the given length works at hour, on a horizon of period hours (24 or 168)."""
    return (hour - start_hour) % period < length


def is_night_hour(hour: int, night_start: int, night_end: int) -> bool:
    """True when an hour lies in the night window, which may wrap past midnight
    (Article 106: 22:00 to 06:00). Accepts hour of day or hour of week."""
    hour_of_day = hour % HOURS_PER_DAY
    if night_start > night_end:
        return hour_of_day >= night_start or hour_of_day < night_end
    return night_start <= hour_of_day < night_end


def night_hours_in_shift(start_hour: int, length: int, night_start: int, night_end: int) -> int:
    """Count the hours of a shift that fall inside the night window."""
    return sum(
        is_night_hour(start_hour + offset, night_start, night_end) for offset in range(length)
    )
