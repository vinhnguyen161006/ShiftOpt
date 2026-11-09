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


def test_minimum_hours_is_optional() -> None:
    assert EmployeeCreate.model_validate(_payload()).min_weekly_hours is None


def test_minimum_hours_accepts_a_value_up_to_the_maximum() -> None:
    payload = _payload(min_weekly_hours=20, max_weekly_hours=30)

    assert EmployeeCreate.model_validate(payload).min_weekly_hours == 20


def test_minimum_above_maximum_is_rejected() -> None:
    with pytest.raises(ValidationError, match="must not exceed"):
        EmployeeCreate.model_validate(_payload(min_weekly_hours=31, max_weekly_hours=30))


@pytest.mark.parametrize("hours", [0, 49])
def test_minimum_hours_rejects_zero_and_above_law(hours: int) -> None:
    with pytest.raises(ValidationError):
        EmployeeCreate.model_validate(_payload(min_weekly_hours=hours))
