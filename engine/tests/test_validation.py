import ast
from pathlib import Path

from shiftopt import validation
from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Assignment, Employee, Instance, ShiftType, Solution
from shiftopt.time_grid import HOURS_PER_WEEK
from shiftopt.validation import Violation, ViolationKind, validate

DAY = ShiftType("day", 8)
MORNING = ShiftType("morning", 6)
AFTERNOON = ShiftType("afternoon", 14)
NIGHT = ShiftType("night", 22)
SEVEN_HOURS = ShiftType("seven", 8, length=7)
TEN_HOURS = ShiftType("ten", 8, length=10)
START_SHIFTS = tuple(ShiftType(f"s{start}", start) for start in (0, 4, 8, 12, 16, 20, 22))
ALL_SHIFTS = (DAY, MORNING, AFTERNOON, NIGHT, SEVEN_HOURS, TEN_HOURS, *START_SHIFTS)


def work(day: int, shift: ShiftType, employee: str = "e1") -> Assignment:
    return Assignment(employee, day, shift.name)


def violations_for(*assignments: Assignment, rules: LaborRules | None = None) -> list[Violation]:
    instance = Instance(
        demand=(0,) * HOURS_PER_WEEK,
        employees=(Employee("e1", 100), Employee("e2", 100)),
        shift_types=ALL_SHIFTS,
        rules=rules or LaborRules(),
    )
    return validate(instance, Solution(assignments))


def kinds_for(*assignments: Assignment, rules: LaborRules | None = None) -> list[ViolationKind]:
    return [violation.kind for violation in violations_for(*assignments, rules=rules)]


def imported_modules(module_file: str) -> set[str]:
    tree = ast.parse(Path(module_file).read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    return modules


def test_clean_roster_has_no_violations() -> None:
    assert violations_for(*(work(day, DAY) for day in range(5))) == []


def test_afternoon_then_morning_breaks_rest_rule() -> None:
    violations = violations_for(work(0, AFTERNOON), work(1, MORNING))
    assert [violation.kind for violation in violations] == [ViolationKind.REST_BETWEEN_SHIFTS]
    assert "8 hours" in violations[0].detail


def test_rest_rule_wraps_from_sunday_to_monday() -> None:
    assert kinds_for(work(6, NIGHT), work(0, MORNING)) == [ViolationKind.REST_BETWEEN_SHIFTS]


def test_seven_working_days_breaks_consecutive_days() -> None:
    kinds = kinds_for(*(work(day, DAY) for day in range(7)))
    assert ViolationKind.CONSECUTIVE_DAYS in kinds


def test_consecutive_run_wraps_over_week_boundary() -> None:
    rules = LaborRules(max_consecutive_days=3)
    across = kinds_for(work(5, DAY), work(6, DAY), work(0, DAY), work(1, DAY), rules=rules)
    assert ViolationKind.CONSECUTIVE_DAYS in across
    within = kinds_for(work(6, DAY), work(0, DAY), work(1, DAY), rules=rules)
    assert ViolationKind.CONSECUTIVE_DAYS not in within


def test_six_working_days_in_a_row_are_allowed() -> None:
    assert kinds_for(*(work(day, DAY) for day in range(6))) == []


def test_forty_nine_hours_breaks_weekly_hours() -> None:
    kinds = kinds_for(*(work(day, SEVEN_HOURS) for day in range(7)))
    assert ViolationKind.WEEKLY_HOURS in kinds


def test_weekly_hours_limit_follows_rules() -> None:
    six_shifts = [work(day, DAY) for day in range(6)]
    assert kinds_for(*six_shifts) == []
    assert ViolationKind.WEEKLY_HOURS in kinds_for(
        *six_shifts, rules=LaborRules(max_weekly_hours=40)
    )


def test_shift_longer_than_daily_limit_is_reported_with_day() -> None:
    violations = violations_for(work(3, TEN_HOURS))
    assert [violation.kind for violation in violations] == [ViolationKind.DAILY_HOURS]
    assert violations[0].day == 3


def test_staircase_roster_never_rests_24_hours() -> None:
    roster = [work(day, START_SHIFTS[index]) for index, day in enumerate(range(6))]
    assert kinds_for(*roster) == [ViolationKind.WEEKLY_REST]


def test_trap_rest_day_with_overnight_shift_is_reported() -> None:
    roster = [work(0, START_SHIFTS[6])] + [
        work(day, START_SHIFTS[index]) for index, day in enumerate((2, 3, 4, 5, 6), start=0)
    ]
    assert kinds_for(*roster) == [ViolationKind.WEEKLY_REST]


def test_overnight_shift_then_full_24_hour_rest_is_allowed() -> None:
    assert kinds_for(work(0, NIGHT), work(2, MORNING)) == []


def test_two_shifts_on_one_day_are_reported() -> None:
    assert ViolationKind.MULTIPLE_SHIFTS_PER_DAY in kinds_for(work(0, DAY), work(0, MORNING))


def test_unknown_employee_and_shift_are_reported() -> None:
    kinds = kinds_for(Assignment("ghost", 0, "day"), Assignment("e1", 0, "missing"))
    assert kinds == [ViolationKind.UNKNOWN_EMPLOYEE, ViolationKind.UNKNOWN_SHIFT]


def test_employees_are_checked_independently() -> None:
    violations = violations_for(
        work(0, AFTERNOON, "e1"), work(1, MORNING, "e1"), work(1, DAY, "e2")
    )
    assert {violation.employee_id for violation in violations} == {"e1"}


def test_validation_does_not_import_models_or_solvers() -> None:
    assert validation.__file__ is not None
    modules = imported_modules(validation.__file__)
    assert not any(module.startswith(("shiftopt.models", "shiftopt.solvers")) for module in modules)
