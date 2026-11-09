import pytest
from pydantic import ValidationError

from src.schedules.schemas import PreviewWarningsRead


def test_warning_kind_must_be_known() -> None:
    with pytest.raises(ValidationError):
        PreviewWarningsRead.model_validate(
            {"warnings": [{"kind": "unknown", "detail": "x", "employee_id": None}]}
        )


def test_warning_round_trips_with_employee_id() -> None:
    payload = PreviewWarningsRead.model_validate(
        {
            "warnings": [
                {
                    "kind": "no_available_days",
                    "detail": "employee E1 has no available day",
                    "employee_id": "E1",
                }
            ]
        }
    )

    assert payload.warnings[0].employee_id == "E1"
