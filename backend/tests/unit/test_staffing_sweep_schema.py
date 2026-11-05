import pytest
from pydantic import ValidationError

from src.analysis.schemas import StaffingSweepRequest
from src.schedules.schemas import SolveRequest


def _request(assumption: str, values: list[float]) -> dict[str, object]:
    solve = SolveRequest(demand_profile_id=1, shift_template_ids=[1])
    return {"solve": solve.model_dump(), "assumption": assumption, "values": values}


def test_alpha_accepts_fractional_values() -> None:
    assert StaffingSweepRequest.model_validate(_request("alpha", [0.5, 1.5])).values == [0.5, 1.5]


@pytest.mark.parametrize("assumption", ["min_staff", "night_min_staff"])
def test_staff_floors_reject_fractional_values(assumption: str) -> None:
    with pytest.raises(ValidationError, match="whole numbers"):
        StaffingSweepRequest.model_validate(_request(assumption, [1.5]))


@pytest.mark.parametrize("values", [[0.0], [-1.0], [1001.0], []])
def test_values_must_be_positive_and_bounded(values: list[float]) -> None:
    with pytest.raises(ValidationError):
        StaffingSweepRequest.model_validate(_request("productivity", values))


def test_unknown_assumption_is_rejected() -> None:
    with pytest.raises(ValidationError):
        StaffingSweepRequest.model_validate(_request("wage", [1.0]))
