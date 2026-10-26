import pytest
from pydantic import ValidationError
from shiftopt.time_grid import HOURS_PER_WEEK

from src.demand.schemas import MAX_HOURLY_DEMAND, DemandProfileCreate


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": "week", "required_staff": [1] * HOURS_PER_WEEK}
    payload.update(overrides)
    return payload


def test_accepts_full_grid() -> None:
    profile = DemandProfileCreate.model_validate(_payload())
    assert len(profile.required_staff) == HOURS_PER_WEEK


@pytest.mark.parametrize("length", [167, 169])
def test_rejects_wrong_cell_count(length: int) -> None:
    with pytest.raises(ValidationError, match="demand grid must have 168 cells"):
        DemandProfileCreate.model_validate(_payload(required_staff=[1] * length))


def test_rejects_negative_demand() -> None:
    grid = [1] * HOURS_PER_WEEK
    grid[5] = -1
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        DemandProfileCreate.model_validate(_payload(required_staff=grid))


def test_rejects_fractional_demand() -> None:
    grid: list[object] = [1] * HOURS_PER_WEEK
    grid[5] = 1.5
    with pytest.raises(ValidationError):
        DemandProfileCreate.model_validate(_payload(required_staff=grid))


def test_rejects_demand_above_limit() -> None:
    grid = [1] * HOURS_PER_WEEK
    grid[5] = MAX_HOURLY_DEMAND + 1
    with pytest.raises(ValidationError, match="less than or equal to 1000"):
        DemandProfileCreate.model_validate(_payload(required_staff=grid))
