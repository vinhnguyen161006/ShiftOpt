import pytest
from pydantic import ValidationError

from src.analysis.schemas import FairnessSweepRequest
from src.schedules.schemas import SolveRequest


def _request(tolerances: list[float]) -> dict[str, object]:
    solve = SolveRequest(demand_profile_id=1, shift_template_ids=[1])
    return {"solve": solve.model_dump(), "tolerances": tolerances}


def test_default_tolerances_include_zero_as_baseline() -> None:
    request = FairnessSweepRequest.model_validate({"solve": _request([])["solve"]})

    assert request.tolerances[0] == 0.0
    assert request.tolerances == [0.0, 1.0, 2.0, 5.0, 10.0]


def test_tolerances_accept_fractions_within_range() -> None:
    assert FairnessSweepRequest.model_validate(_request([0.5, 10.0])).tolerances == [0.5, 10.0]


@pytest.mark.parametrize("tolerances", [[-0.1], [10.5], []])
def test_tolerances_outside_range_are_rejected(tolerances: list[float]) -> None:
    with pytest.raises(ValidationError):
        FairnessSweepRequest.model_validate(_request(tolerances))


def test_solve_settings_reject_tolerance_above_ten() -> None:
    with pytest.raises(ValidationError):
        SolveRequest(demand_profile_id=1, shift_template_ids=[1], cost_tolerance_percent=11.0)
