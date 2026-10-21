import pytest


@pytest.mark.skip(reason="TODO")
def test_enough_staff_gives_full_coverage_without_violations() -> None:
    """TODO: 6 employees, demand 1: OPTIMAL, no shortfall, validate() empty."""


@pytest.mark.skip(reason="TODO")
def test_too_few_staff_stays_feasible_and_reports_shortfall() -> None:
    """TODO: 3 employees: shortfall > 0 and still no hard violation."""


@pytest.mark.skip(reason="TODO")
def test_same_seed_gives_same_objective() -> None:
    """TODO: num_workers = 1 and a fixed seed reproduce the objective."""


@pytest.mark.skip(reason="TODO")
def test_symmetry_breaking_keeps_objective() -> None:
    """TODO: objective equal with and without symmetry breaking."""
