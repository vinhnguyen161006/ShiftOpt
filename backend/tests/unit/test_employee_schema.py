import pytest
from pydantic import ValidationError

from src.employees.schemas import EmployeeCreate


def _payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {"code": "E1", "name": "Ann", "hourly_wage": 100}
    base.update(overrides)
    return base


def test_weekly_hours_is_optional() -> None:
    assert EmployeeCreate.model_validate(_payload()).max_weekly_hours is None


@pytest.mark.parametrize("hours", [24, 40, 48])
def test_weekly_hours_accepts_values_up_to_the_law_limit(hours: int) -> None:
    assert EmployeeCreate.model_validate(_payload(max_weekly_hours=hours)).max_weekly_hours == hours


@pytest.mark.parametrize("hours", [0, -1, 49])
def test_weekly_hours_rejects_zero_negative_and_above_law(hours: int) -> None:
    with pytest.raises(ValidationError):
        EmployeeCreate.model_validate(_payload(max_weekly_hours=hours))
