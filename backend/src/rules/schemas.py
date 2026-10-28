from pydantic import BaseModel


class LaborRulesRead(BaseModel):
    """Default labor rules of the engine (Labor Code 45/2019/QH14), so the UI can warn before
    the backend rejects an input."""

    max_daily_hours: int
    max_weekly_hours: int
    night_start: int
    night_end: int
    night_premium_percent: int
    min_rest_between_shifts: int
    weekly_rest_hours: int
    max_consecutive_days: int
    min_break_minutes: int
    min_night_break_minutes: int
    break_required_from_hours: int
