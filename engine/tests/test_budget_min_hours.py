import pytest

from shiftopt.baseline import greedy_roster
from shiftopt.constraints.fairness import min_hours_shortfall
from shiftopt.diagnostics import WarningKind, diagnose
from shiftopt.domain import Assignment, Employee, Instance, ShiftType, Solution
from shiftopt.kpi import compute_kpi, labor_cost
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.models.roster_mip import solve_roster_mip
from shiftopt.solvers.base import SolveParams, SolveStatus
from shiftopt.time_grid import HOURS_PER_WEEK, hour_of_week
from shiftopt.validation import ViolationKind, validate

DAY = ShiftType("day", 8)
SHIFT_COST = 100 * 8 * 100
PARAMS = SolveParams(time_limit_seconds=60, num_workers=1, random_seed=0)
UNCOVERED_WITH_TWO_SHIFTS = 3 * 8 - 2 * 8


def day_demand(days: int) -> tuple[int, ...]:
    demand = [0] * HOURS_PER_WEEK
    for day in range(days):
        for hour in range(8, 16):
            demand[hour_of_week(day, hour)] = 1
    return tuple(demand)


def plain_crew(count: int) -> tuple[Employee, ...]:
    return tuple(Employee(f"e{index}", 100) for index in range(count))


def instance_of(
    employees: tuple[Employee, ...], demand: tuple[int, ...], budget: int | None = None
) -> Instance:
    return Instance(demand=demand, employees=employees, shift_types=(DAY,), weekly_budget=budget)


def test_validator_flags_a_roster_over_budget() -> None:
    instance = instance_of(plain_crew(1), day_demand(1), budget=SHIFT_COST - 1)
    roster = Solution((Assignment("e0", 0, "day"),))

    violations = validate(instance, roster)

    assert [item.kind for item in violations] == [ViolationKind.OVER_BUDGET]
    assert violations[0].employee_id is None


def test_validator_accepts_a_roster_exactly_at_budget() -> None:
    instance = instance_of(plain_crew(1), day_demand(1), budget=SHIFT_COST)
    roster = Solution((Assignment("e0", 0, "day"),))

    assert validate(instance, roster) == []


def test_binding_budget_adds_shortfall_and_stays_feasible() -> None:
    instance = instance_of(plain_crew(3), day_demand(3), budget=2 * SHIFT_COST)

    outcome = solve_roster(instance, PARAMS)

    assert outcome.result.status is SolveStatus.OPTIMAL
    assert outcome.understaffed_hours == UNCOVERED_WITH_TWO_SHIFTS
    assert labor_cost(instance, outcome.solution) <= 2 * SHIFT_COST
    assert validate(instance, outcome.solution) == []


def test_loose_budget_changes_nothing() -> None:
    free = instance_of(plain_crew(3), day_demand(3))
    capped = instance_of(plain_crew(3), day_demand(3), budget=10 * SHIFT_COST)

    free_outcome = solve_roster(free, PARAMS)
    capped_outcome = solve_roster(capped, PARAMS)

    assert free_outcome.understaffed_hours == capped_outcome.understaffed_hours == 0
    assert labor_cost(free, free_outcome.solution) == labor_cost(capped, capped_outcome.solution)
    assert len(free_outcome.phases) == len(capped_outcome.phases) == 3


def test_minimum_hours_pull_an_idle_employee_onto_the_roster() -> None:
    crew = (Employee("e0", 100, min_weekly_hours=16), Employee("e1", 100))
    instance = instance_of(crew, day_demand(1))

    outcome = solve_roster(instance, PARAMS)

    assert outcome.min_hours_shortfall == 0
    assert min_hours_shortfall(instance, outcome.solution) == 0
    worked = sum(8 for item in outcome.solution.assignments if item.employee_id == "e0")
    assert worked >= 16
    assert len(outcome.phases) == 4
    assert validate(instance, outcome.solution) == []


def test_unreachable_minimum_is_reported_not_infeasible() -> None:
    blocked = Employee("e0", 100, unavailable_days=frozenset(range(6)), min_weekly_hours=16)
    instance = instance_of((blocked, Employee("e1", 100)), day_demand(1))

    outcome = solve_roster(instance, PARAMS)

    assert outcome.result.status is not SolveStatus.INFEASIBLE
    assert outcome.min_hours_shortfall == 8
    assert compute_kpi(instance, outcome.solution).min_hours_shortfall == 8


def test_mip_and_cpsat_agree_on_the_minimum_hours_tier() -> None:
    crew = (Employee("e0", 100, min_weekly_hours=16), Employee("e1", 100))
    instance = instance_of(crew, day_demand(1))

    cpsat = solve_roster(instance, PARAMS)
    mip = solve_roster_mip(instance, PARAMS)

    assert mip.min_hours_shortfall == cpsat.min_hours_shortfall == 0
    assert mip.phases[1].objective == cpsat.phases[1].objective
    assert validate(instance, mip.solution) == []


def test_mip_respects_the_budget() -> None:
    instance = instance_of(plain_crew(3), day_demand(3), budget=2 * SHIFT_COST)

    outcome = solve_roster_mip(instance, PARAMS)

    assert outcome.understaffed_hours == UNCOVERED_WITH_TWO_SHIFTS
    assert labor_cost(instance, outcome.solution) <= 2 * SHIFT_COST


def test_greedy_never_exceeds_the_budget() -> None:
    instance = instance_of(plain_crew(3), day_demand(3), budget=2 * SHIFT_COST)

    roster = greedy_roster(instance)

    assert labor_cost(instance, roster) <= 2 * SHIFT_COST
    assert validate(instance, roster) == []


def test_instance_rejects_a_minimum_above_the_weekly_cap() -> None:
    with pytest.raises(ValueError, match="min_weekly_hours"):
        instance_of((Employee("e0", 100, max_weekly_hours=20, min_weekly_hours=24),), day_demand(1))


def test_employee_rejects_a_non_positive_minimum() -> None:
    with pytest.raises(ValueError, match="min_weekly_hours"):
        Employee("e0", 100, min_weekly_hours=0)


def test_diagnostics_flag_a_minimum_the_employee_cannot_reach() -> None:
    blocked = Employee("e0", 100, unavailable_days=frozenset(range(6)), min_weekly_hours=16)
    instance = instance_of((blocked,), day_demand(1))

    kinds = [item.kind for item in diagnose(instance)]

    assert WarningKind.MIN_HOURS_UNREACHABLE in kinds


def test_diagnostics_flag_a_budget_below_the_cheapest_coverage() -> None:
    instance = instance_of(plain_crew(2), day_demand(1), budget=SHIFT_COST - 1)

    assert WarningKind.BUDGET_BELOW_DEMAND in [item.kind for item in diagnose(instance)]
    enough = instance_of(plain_crew(2), day_demand(1), budget=SHIFT_COST)
    assert WarningKind.BUDGET_BELOW_DEMAND not in [item.kind for item in diagnose(enough)]
