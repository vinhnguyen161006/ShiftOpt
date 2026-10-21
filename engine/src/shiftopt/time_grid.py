HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
HOURS_PER_WEEK = HOURS_PER_DAY * DAYS_PER_WEEK


def hour_of_week(day: int, hour: int) -> int:
    """TODO: cyclic hour-of-week index; day 0 is Monday and hour may exceed 23."""
    raise NotImplementedError


def shift_hours(day: int, start_hour: int, length: int) -> tuple[int, ...]:
    """TODO: hour-of-week indexes a shift occupies. Overnight shifts spill into the next day and
    the last day of the week wraps to hour 0 because the roster repeats weekly."""
    raise NotImplementedError


def is_night_hour(hour: int, night_start: int, night_end: int) -> bool:
    """TODO: True when an hour of day lies in the night window, which wraps past midnight
    (Article 106: 22:00 to 06:00)."""
    raise NotImplementedError


def night_hours_in_shift(start_hour: int, length: int, night_start: int, night_end: int) -> int:
    """TODO: count the hours of a shift that fall inside the night window."""
    raise NotImplementedError
