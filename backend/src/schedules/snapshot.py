from collections.abc import Mapping, Sequence
from dataclasses import asdict
from typing import Any

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Assignment, Employee, Instance, ShiftType, Solution

from src.employees.models import EmployeeRecord
from src.shifts.models import ShiftTemplate

Snapshot = dict[str, Any]


def build_snapshot(
    required_staff: Sequence[int],
    templates: Sequence[ShiftTemplate],
    employees: Sequence[EmployeeRecord],
    rules: LaborRules,
) -> Snapshot:
    """Plain JSON copy of one scheduling problem. Employees are ordered by code and shifts by
    start hour and name, so the same data always yields the same instance."""
    return {
        "demand": list(required_staff),
        "shift_types": [
            {
                "name": template.name,
                "start_hour": template.start_hour,
                "length": template.length_hours,
            }
            for template in sorted(templates, key=lambda t: (t.start_hour, t.name))
        ],
        "employees": [
            {
                "id": employee.code,
                "hourly_wage": employee.hourly_wage,
                "unavailable_days": sorted(employee.unavailable_days),
                "preferred_days_off": sorted(employee.preferred_days_off),
            }
            for employee in sorted(employees, key=lambda e: e.code)
        ],
        "rules": asdict(rules),
    }


def instance_from_snapshot(snapshot: Snapshot) -> Instance:
    return Instance(
        demand=tuple(snapshot["demand"]),
        employees=tuple(
            Employee(
                id=row["id"],
                hourly_wage=row["hourly_wage"],
                unavailable_days=frozenset(row["unavailable_days"]),
                preferred_days_off=frozenset(row["preferred_days_off"]),
            )
            for row in snapshot["employees"]
        ),
        shift_types=tuple(
            ShiftType(name=row["name"], start_hour=row["start_hour"], length=row["length"])
            for row in snapshot["shift_types"]
        ),
        rules=LaborRules(**snapshot["rules"]),
    )


def solution_from_rows(rows: Sequence[Mapping[str, Any]]) -> Solution:
    return Solution(
        tuple(
            Assignment(
                employee_id=row["employee_code"],
                day=row["day"],
                shift_name=row["shift_name"],
                break_offset=row.get("break_offset"),
            )
            for row in rows
        )
    )
