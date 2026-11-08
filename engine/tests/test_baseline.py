from dataclasses import replace

from shiftopt import kpi
from shiftopt.baseline import greedy_resolver, greedy_roster
from shiftopt.domain import Employee, Instance, ShiftType
from shiftopt.models.roster_cpsat import solve_roster
from shiftopt.solvers.base import SolveParams, SolveStatus
from shiftopt.validation import validate

PARAMS = SolveParams(time_limit_seconds=60, num_workers=1, random_seed=0)
SHIFTS = (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))


def build(demand_at: dict[tuple[int, int], int], employees: tuple[Employee, ...]) -> Instance:
    demand = [0] * 168
    for (day, hour), value in demand_at.items():
        demand[day * 24 + hour] = value
    return Instance(tuple(demand), employees, SHIFTS)


def crew(count: int, wage: int = 100) -> tuple[Employee, ...]:
    return tuple(Employee(f"e{i}", wage) for i in range(count))


def flat(count: int, value: int = 1) -> dict[tuple[int, int], int]:
    return {(day, hour): value for day in range(7) for hour in range(8, 16)}


def test_flat_demand_has_no_hard_violations() -> None:
    instance = build(flat(1), crew(3))
    solution = greedy_roster(instance)
    assert validate(instance, solution) == []


def test_peaked_demand_has_no_hard_violations() -> None:
    demand = {(day, hour): 3 for day in range(5) for hour in range(8, 20)}
    demand.update({(5, hour): 2 for hour in range(0, 24)})
    instance = build(demand, crew(8))
    assert validate(instance, greedy_roster(instance)) == []


def test_unavailable_day_is_never_used() -> None:
    employees = (Employee("e0", 100, unavailable_days=frozenset({0, 1, 2})), Employee("e1", 100))
    instance = build(flat(1), employees)
    solution = greedy_roster(instance)
    assert validate(instance, solution) == []
    assert not any(a.employee_id == "e0" and a.day in {0, 1, 2} for a in solution.assignments)


def test_weekly_cap_is_respected() -> None:
    capped = Employee("e0", 100, max_weekly_hours=24)
    instance = build(flat(3), (capped, Employee("e1", 100)))
    solution = greedy_roster(instance)
    assert validate(instance, solution) == []
    hours = sum(
        instance.shift_by_name(a.shift_name).length
        for a in solution.assignments
        if a.employee_id == "e0"
    )
    assert hours <= 24


def test_one_day_shift_covers_a_single_person_demand() -> None:
    instance = build(flat(1), crew(2))
    solution = greedy_roster(instance)
    day_zero = [a for a in solution.assignments if a.day == 0]
    assert day_zero
    assert {a.shift_name for a in day_zero} == {"day"}


def test_is_deterministic() -> None:
    instance = build({(d, h): 2 for d in range(7) for h in range(6, 22)}, crew(6))
    assert greedy_roster(instance) == greedy_roster(instance)


def test_greedy_resolver_never_claims_optimal() -> None:
    instance = build(flat(1), crew(2))
    evaluation = greedy_resolver()(instance)
    assert evaluation.result.status is SolveStatus.FEASIBLE
    assert evaluation.result.bound is None
    assert not evaluation.proven


def test_greedy_is_no_better_than_cpsat_on_small_instance() -> None:
    demand = {(d, h): 2 for d in range(5) for h in range(8, 16)}
    instance = build(demand, crew(4))
    cpsat = solve_roster(instance, PARAMS)
    greedy = greedy_resolver()(instance)
    assert validate(instance, cpsat.solution) == []
    cpsat_short = cpsat.understaffed_hours
    assert cpsat_short is not None
    assert greedy.understaffed_hours is not None
    assert greedy.understaffed_hours >= cpsat_short
    if cpsat.result.status is SolveStatus.OPTIMAL and greedy.understaffed_hours == cpsat_short:
        assert greedy.labor_cost is not None
        assert greedy.labor_cost >= kpi.labor_cost(instance, cpsat.solution)


def test_zero_demand_yields_empty_roster() -> None:
    instance = replace(build({}, crew(3)))
    assert greedy_roster(instance).assignments == ()
