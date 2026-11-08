import pytest

from shiftopt.domain import Assignment, Employee, Instance, ShiftType, Solution
from shiftopt.replacement import suggest_replacements
from shiftopt.time_grid import HOURS_PER_WEEK

EARLY = ShiftType("early", 6)
LATE = ShiftType("late", 14)


def instance_of(*employees: Employee) -> Instance:
    return Instance(
        demand=(0,) * HOURS_PER_WEEK,
        employees=employees,
        shift_types=(EARLY, LATE),
    )


def test_rest_violating_candidate_is_excluded() -> None:
    instance = instance_of(
        Employee("absent", 100),
        Employee("late_yesterday", 100),
        Employee("free", 100),
    )
    roster = Solution(
        (
            Assignment("absent", 1, "early", 3),
            Assignment("late_yesterday", 0, "late", 3),
        )
    )

    ids = [item.employee_id for item in suggest_replacements(instance, roster, "absent", 1, 5)]

    assert ids == ["free"]


def test_absent_and_busy_employees_are_excluded() -> None:
    instance = instance_of(Employee("absent", 100), Employee("busy", 100), Employee("free", 100))
    roster = Solution(
        (
            Assignment("absent", 1, "early", 3),
            Assignment("busy", 1, "late", 3),
        )
    )

    ids = [item.employee_id for item in suggest_replacements(instance, roster, "absent", 1, 5)]

    assert ids == ["free"]


def test_unavailable_employee_is_excluded() -> None:
    instance = instance_of(
        Employee("absent", 100),
        Employee("blocked", 100, unavailable_days=frozenset({1})),
        Employee("free", 100),
    )
    roster = Solution((Assignment("absent", 1, "early", 3),))

    ids = [item.employee_id for item in suggest_replacements(instance, roster, "absent", 1, 5)]

    assert ids == ["free"]


def test_ranking_prefers_day_off_then_cost_and_limit_applies() -> None:
    instance = instance_of(
        Employee("absent", 100),
        Employee("expensive", 200),
        Employee("cheap", 100),
        Employee("wants_off", 50, preferred_days_off=frozenset({1})),
    )
    roster = Solution((Assignment("absent", 1, "early", 3),))

    ranked = suggest_replacements(instance, roster, "absent", 1, 5)
    first_only = suggest_replacements(instance, roster, "absent", 1, 1)

    assert [item.employee_id for item in ranked] == ["cheap", "expensive", "wants_off"]
    assert [item.employee_id for item in first_only] == ["cheap"]
    assert ranked[0].extra_cost == 100 * EARLY.cost_per_wage_unit(instance.rules)


def test_employee_without_shift_on_day_is_rejected() -> None:
    instance = instance_of(Employee("absent", 100), Employee("free", 100))
    roster = Solution((Assignment("absent", 1, "early", 3),))
    with pytest.raises(ValueError, match="no shift on day 2"):
        suggest_replacements(instance, roster, "absent", 2, 5)
