from dataclasses import dataclass, field

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.time_grid import (
    DAYS_PER_WEEK,
    HOURS_PER_DAY,
    HOURS_PER_WEEK,
    night_hours_in_shift,
)

PERCENT_BASE = 100


@dataclass(frozen=True)
class ShiftType:
    name: str
    start_hour: int
    length: int = 8

    def __post_init__(self) -> None:
        if not 0 <= self.start_hour < HOURS_PER_DAY:
            raise ValueError(f"shift {self.name}: start_hour must be in [0, 24)")
        if not 0 < self.length <= HOURS_PER_DAY:
            raise ValueError(f"shift {self.name}: length must be in (0, 24]")

    def night_hours(self, rules: LaborRules) -> int:
        """Hours of this shift inside the night window (Article 106)."""
        return night_hours_in_shift(
            self.start_hour, self.length, rules.night_start, rules.night_end
        )

    def cost_per_wage_unit(self, rules: LaborRules) -> int:
        """Shift cost in hundredths of the hourly wage: 100 * length plus
        night_premium_percent * night_hours (Article 98 clause 2)."""
        return PERCENT_BASE * self.length + rules.night_premium_percent * self.night_hours(rules)

    def is_night_shift(self, rules: LaborRules) -> bool:
        """True when more than half of the shift lies in the night window. Used for the
        fairness measure, so an evening shift that only touches midnight is not a night shift."""
        return 2 * self.night_hours(rules) > self.length


@dataclass(frozen=True)
class Employee:
    id: str
    hourly_wage: int

    def __post_init__(self) -> None:
        if self.hourly_wage <= 0:
            raise ValueError(f"employee {self.id}: hourly_wage must be positive")


@dataclass(frozen=True)
class Instance:
    """One weekly scheduling problem. The roster repeats every week (cyclic horizon).

    demand holds the required head count for each of the 168 hours of the week, Monday 00:00 first.
    """

    demand: tuple[int, ...]
    employees: tuple[Employee, ...]
    shift_types: tuple[ShiftType, ...]
    rules: LaborRules = field(default_factory=LaborRules)

    def __post_init__(self) -> None:
        if len(self.demand) != HOURS_PER_WEEK:
            raise ValueError(f"demand must have {HOURS_PER_WEEK} entries")
        if any(value < 0 for value in self.demand):
            raise ValueError("demand must be non-negative")
        if len({shift.name for shift in self.shift_types}) != len(self.shift_types):
            raise ValueError("shift type names must be unique")
        if len({employee.id for employee in self.employees}) != len(self.employees):
            raise ValueError("employee ids must be unique")

    def shift_by_name(self, name: str) -> ShiftType:
        """Look up a shift type; raise KeyError when the name is unknown."""
        for shift in self.shift_types:
            if shift.name == name:
                return shift
        raise KeyError(name)


@dataclass(frozen=True)
class Assignment:
    employee_id: str
    day: int
    shift_name: str

    def __post_init__(self) -> None:
        if not 0 <= self.day < DAYS_PER_WEEK:
            raise ValueError("day must be in [0, 7)")


@dataclass(frozen=True)
class Solution:
    assignments: tuple[Assignment, ...]
