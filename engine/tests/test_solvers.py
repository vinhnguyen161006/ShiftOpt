import pulp
import pytest
from ortools.sat.python import cp_model

from shiftopt.solvers.base import ModelInvalidError, SolveParams, SolveStatus, relative_gap
from shiftopt.solvers.cpsat import run_cp_model
from shiftopt.solvers.pulp_backend import run_problem


def cp_cover_model(lower: int) -> tuple[cp_model.CpModel, cp_model.IntVar, cp_model.IntVar]:
    model = cp_model.CpModel()
    x = model.new_int_var(0, 10, "x")
    y = model.new_int_var(0, 10, "y")
    model.add(x + y >= lower)
    model.minimize(x + 2 * y)
    return model, x, y


def pulp_cover_problem(lower: int) -> pulp.LpProblem:
    problem = pulp.LpProblem("cover", pulp.LpMinimize)
    x = problem.add_variable("x", lowBound=0, upBound=10, cat=pulp.LpInteger)
    y = problem.add_variable("y", lowBound=0, upBound=10, cat=pulp.LpInteger)
    problem += x + 2 * y
    problem += x + y >= lower, "cover"
    return problem


def test_relative_gap_uses_floor_of_one_in_denominator() -> None:
    assert relative_gap(10.0, 9.0) == pytest.approx(0.1)
    assert relative_gap(0.0, 0.5) == pytest.approx(0.5)


def test_cpsat_finds_known_optimum() -> None:
    model, x, y = cp_cover_model(lower=3)
    solver, result = run_cp_model(model, SolveParams(num_workers=1))
    assert result.status is SolveStatus.OPTIMAL
    assert result.objective == 3
    assert result.bound == 3
    assert result.gap == 0
    assert result.solver == "ortools-cp-sat"
    assert solver.value(x) + solver.value(y) >= 3


def test_cpsat_reports_infeasible() -> None:
    model = cp_model.CpModel()
    x = model.new_int_var(0, 1, "x")
    model.add(x >= 2)
    _, result = run_cp_model(model, SolveParams(num_workers=1))
    assert result.status is SolveStatus.INFEASIBLE
    assert result.objective is None
    assert result.bound is None


def test_cpsat_rejects_invalid_model_as_programming_error() -> None:
    model = cp_model.CpModel()
    model.new_int_var(5, 1, "broken")
    with pytest.raises(ModelInvalidError):
        run_cp_model(model, SolveParams(num_workers=1))


def test_highs_lp_matches_cpsat_on_same_toy_model() -> None:
    problem = pulp_cover_problem(lower=3)
    result = run_problem(problem, SolveParams(num_workers=1), mip=False)
    assert result.status is SolveStatus.OPTIMAL
    assert result.objective == pytest.approx(3)
    assert result.solver == "pulp-highs"


def test_highs_mip_reports_optimal_with_bound() -> None:
    problem = pulp_cover_problem(lower=3)
    result = run_problem(problem, SolveParams(num_workers=1), mip=True)
    assert result.status is SolveStatus.OPTIMAL
    assert result.objective == pytest.approx(3)
    assert result.bound == pytest.approx(3)


def test_highs_reports_infeasible() -> None:
    problem = pulp.LpProblem("bad", pulp.LpMinimize)
    x = problem.add_variable("x", lowBound=0, upBound=1, cat=pulp.LpInteger)
    problem += x
    problem += x >= 2, "impossible"
    result = run_problem(problem, SolveParams(num_workers=1), mip=True)
    assert result.status is SolveStatus.INFEASIBLE
    assert result.objective is None


def test_tiny_time_limit_never_claims_optimal_without_proof() -> None:
    model = cp_model.CpModel()
    variables = [model.new_int_var(0, 50, f"v{i}") for i in range(40)]
    model.add(sum(variables) >= 437)
    model.add_all_different(variables)
    model.minimize(sum((index + 1) * var for index, var in enumerate(variables)))
    _, result = run_cp_model(model, SolveParams(time_limit_seconds=0.001, num_workers=1))
    assert result.status is not SolveStatus.INFEASIBLE
    if result.status is SolveStatus.FEASIBLE:
        assert result.bound is not None
        assert result.gap is not None
