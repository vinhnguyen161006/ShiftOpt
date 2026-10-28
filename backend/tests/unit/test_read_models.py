from dataclasses import asdict
from datetime import datetime

from httpx import AsyncClient
from shiftopt.constraints.labor_law_vn import LaborRules

from src.schedules.models import RunStatus, SolveRun
from src.schedules.schemas import SolveRunRead
from src.shifts.models import ShiftTemplate
from src.shifts.schemas import ShiftTemplateRead

CREATED = datetime(2026, 10, 28)


async def test_labor_rules_endpoint_returns_engine_defaults(client: AsyncClient) -> None:
    response = await client.get("/api/labor-rules")

    assert response.status_code == 200
    assert response.json() == asdict(LaborRules())


def test_shift_template_read_carries_night_hours_from_the_engine() -> None:
    night = ShiftTemplate(id=1, name="night", start_hour=22, length_hours=8, created_at=CREATED)
    late = ShiftTemplate(id=2, name="late", start_hour=14, length_hours=8, created_at=CREATED)
    short = ShiftTemplate(id=3, name="short", start_hour=8, length_hours=4, created_at=CREATED)

    assert ShiftTemplateRead.model_validate(night).night_hours == 8
    assert ShiftTemplateRead.model_validate(late).night_hours == 0
    assert ShiftTemplateRead.model_validate(night).break_required is True
    assert ShiftTemplateRead.model_validate(short).break_required is False


def test_solve_run_read_lists_snapshot_employees_and_shifts() -> None:
    run = SolveRun(
        id=5,
        status=RunStatus.SUCCEEDED,
        solver="ortools-cp-sat",
        params={"random_seed": 0},
        instance_snapshot={
            "demand": [0] * 168,
            "employees": [{"id": "E1"}, {"id": "E2"}],
            "shift_types": [{"name": "day", "start_hour": 8, "length": 8}],
            "rules": asdict(LaborRules()),
        },
        assignments=None,
        created_at=CREATED,
    )

    read = SolveRunRead.model_validate(run)

    assert read.employee_codes == ["E1", "E2"]
    assert read.shift_types[0].start_hour == 8
