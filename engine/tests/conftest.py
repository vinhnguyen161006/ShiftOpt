from collections.abc import Callable

import pytest

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Employee, Instance, ShiftType
from shiftopt.time_grid import HOURS_PER_WEEK

InstanceFactory = Callable[..., Instance]


@pytest.fixture
def three_shifts() -> tuple[ShiftType, ...]:
    return (ShiftType("night", 0), ShiftType("day", 8), ShiftType("evening", 16))


@pytest.fixture
def build_instance(three_shifts: tuple[ShiftType, ...]) -> InstanceFactory:
    def build(
        demand_per_hour: int = 1,
        employee_count: int = 6,
        wage: int = 100,
        shifts: tuple[ShiftType, ...] | None = None,
        rules: LaborRules | None = None,
    ) -> Instance:
        return Instance(
            demand=(demand_per_hour,) * HOURS_PER_WEEK,
            employees=tuple(Employee(f"e{i}", wage) for i in range(employee_count)),
            shift_types=shifts if shifts is not None else three_shifts,
            rules=rules if rules is not None else LaborRules(),
        )

    return build
