import copy
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from typing import Any

from shiftopt.constraints.labor_law_vn import LaborRules
from shiftopt.domain import Assignment, Employee, Instance, RepairSpec, ShiftType, Solution

from src.employees.models import EmployeeRecord
from src.shifts.models import ShiftTemplate

Snapshot = dict[str, Any]
REPAIR_KEY = "repair"


def build_snapshot(
    required_staff: Sequence[int],
    templates: Sequence[ShiftTemplate],
    employees: Sequence[EmployeeRecord],
    rules: LaborRules,
    weekly_budget: int | None = None,
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
                "max_weekly_hours": employee.max_weekly_hours,
                "min_weekly_hours": employee.min_weekly_hours,
                "unavailable_days": sorted(employee.unavailable_days),
                "preferred_days_off": sorted(employee.preferred_days_off),
            }
            for employee in sorted(employees, key=lambda e: e.code)
        ],
        "rules": asdict(rules),
        "weekly_budget": weekly_budget,
    }


def instance_from_snapshot(snapshot: Snapshot) -> Instance:
    return Instance(
        demand=tuple(snapshot["demand"]),
        employees=tuple(
            Employee(
                id=row["id"],
                hourly_wage=row["hourly_wage"],
                max_weekly_hours=row.get("max_weekly_hours"),
                min_weekly_hours=row.get("min_weekly_hours"),
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
        weekly_budget=snapshot.get("weekly_budget"),
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


def repair_snapshot(
    base: Snapshot,
    *,
    from_day: int,
    baseline_rows: Sequence[Mapping[str, Any]],
    pinned_rows: Sequence[Mapping[str, Any]],
    absences: Mapping[str, Sequence[int]],
    demand: Sequence[int] | None,
) -> Snapshot:
    """Copy of the base problem with absences added to unavailable_days, an optional new demand
    profile, and the baseline roster and pinned shifts stored under the repair key."""
    snapshot = copy.deepcopy(base)
    if demand is not None:
        snapshot["demand"] = list(demand)
    for row in snapshot["employees"]:
        row["unavailable_days"] = sorted(
            set(row["unavailable_days"]) | set(absences.get(row["id"], ()))
        )
    snapshot[REPAIR_KEY] = {
        "from_day": from_day,
        "baseline": [dict(row) for row in baseline_rows],
        "pinned": [dict(row) for row in pinned_rows],
    }
    return snapshot


def repair_from_snapshot(snapshot: Snapshot) -> RepairSpec | None:
    repair = snapshot.get(REPAIR_KEY)
    if repair is None:
        return None
    return RepairSpec(
        baseline=solution_from_rows(repair["baseline"]),
        from_day=int(repair["from_day"]),
        pinned=solution_from_rows(repair["pinned"]).assignments,
    )


def assignment_changes(
    baseline_rows: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]]
) -> int:
    """Shifts added or removed relative to the baseline, counted per (employee, day, shift). Moving
    a break inside the same shift does not count."""
    before = {(row["employee_code"], row["day"], row["shift_name"]) for row in baseline_rows}
    after = {(row["employee_code"], row["day"], row["shift_name"]) for row in rows}
    return len(before ^ after)
