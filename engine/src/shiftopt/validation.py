from dataclasses import dataclass
from enum import StrEnum

from shiftopt.domain import Instance, Solution


class ViolationKind(StrEnum):
    UNKNOWN_EMPLOYEE = "unknown_employee"
    UNKNOWN_SHIFT = "unknown_shift"
    MULTIPLE_SHIFTS_PER_DAY = "multiple_shifts_per_day"
    WEEKLY_HOURS = "weekly_hours"
    REST_BETWEEN_SHIFTS = "rest_between_shifts"
    CONSECUTIVE_DAYS = "consecutive_days"
    WEEKLY_REST = "weekly_rest"


@dataclass(frozen=True)
class Violation:
    kind: ViolationKind
    employee_id: str
    detail: str


def validate(instance: Instance, solution: Solution) -> list[Violation]:
    """TODO: re-check every hard constraint from first principles on the absolute hour axis.

    Must not import models or solvers. The week is cyclic, so rest gaps and day runs wrap from
    Sunday to Monday. Checks: one shift per day, weekly hours (Article 105), rest of at least
    12 hours between consecutive shifts (Article 110), maximum consecutive working days, and a
    longest rest gap of at least 24 hours (Article 111), which a calendar day off alone does
    not guarantee for overnight shifts.
    """
    raise NotImplementedError
