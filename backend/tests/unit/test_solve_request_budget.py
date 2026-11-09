import pytest
from pydantic import ValidationError

from src.schedules.schemas import SolveRequest


def test_budget_is_optional() -> None:
    request = SolveRequest(demand_profile_id=1, shift_template_ids=[1])

    assert request.weekly_budget is None


@pytest.mark.parametrize("budget", [0, -5])
def test_budget_must_be_positive(budget: int) -> None:
    with pytest.raises(ValidationError):
        SolveRequest(demand_profile_id=1, shift_template_ids=[1], weekly_budget=budget)
