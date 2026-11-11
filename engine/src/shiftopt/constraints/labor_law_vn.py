from dataclasses import dataclass


@dataclass(frozen=True)
class LaborRules:
    """Vietnamese Labor Code 45/2019/QH14 rules used as hard constraints.

    max_daily_hours: Article 105, normal working time per day.
    max_weekly_hours: Article 105, normal working time per week.
    night_start, night_end: Article 106, night work runs from 22:00 to 06:00.
    night_premium_percent: Article 98 clause 2, at least 30 percent extra pay at night.
    min_rest_between_shifts: Article 110, at least 12 hours before switching shifts.
    weekly_rest_hours: Article 111, at least 24 consecutive hours of rest each week.
    max_consecutive_days: working days in a row; 6 guarantees a day off in every 7-day window.
    """

    max_daily_hours: int = 8
    max_weekly_hours: int = 48
    night_start: int = 22
    night_end: int = 6
    night_premium_percent: int = 30
    min_rest_between_shifts: int = 12
    weekly_rest_hours: int = 24
    max_consecutive_days: int = 6
