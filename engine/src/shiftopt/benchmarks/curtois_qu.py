from dataclasses import dataclass
from typing import Any

from ortools.sat.python import cp_model

from shiftopt.solvers.base import SolveParams, SolveResult
from shiftopt.solvers.cpsat import run_cp_model
from shiftopt.time_grid import DAYS_PER_WEEK

SATURDAY = 5
SUNDAY = 6


@dataclass(frozen=True)
class BenchmarkShift:
    """A shift type. forbidden_next lists the shift ids that may not start on the next day."""

    id: str
    minutes: int
    forbidden_next: frozenset[str]


@dataclass(frozen=True)
class BenchmarkStaff:
    """Per-employee limits. max_shifts must give a cap for every shift id."""

    id: str
    max_shifts: dict[str, int]
    max_total_minutes: int
    min_total_minutes: int
    max_consecutive_shifts: int
    min_consecutive_shifts: int
    min_consecutive_days_off: int
    max_weekends: int


@dataclass(frozen=True)
class ShiftRequest:
    staff: str
    day: int
    shift: str
    weight: int


@dataclass(frozen=True)
class CoverRequirement:
    day: int
    shift: str
    requirement: int
    under_weight: int
    over_weight: int


@dataclass(frozen=True)
class BenchmarkInstance:
    """Curtois and Qu (2014) nurse rostering instance, https://www.schedulingbenchmarks.org/nrp/.

    Day 0 is a Monday. Weekend day k is a Saturday or Sunday of the horizon. Staff with no
    entry in days_off have no forced days off. Cover is per day and shift, not per hour.
    """

    horizon_days: int
    shifts: tuple[BenchmarkShift, ...]
    staff: tuple[BenchmarkStaff, ...]
    days_off: dict[str, frozenset[int]]
    on_requests: tuple[ShiftRequest, ...]
    off_requests: tuple[ShiftRequest, ...]
    cover: tuple[CoverRequirement, ...]


def parse_instance(text: str) -> BenchmarkInstance:
    """Parse the published text format. Lines starting with # are comments; each SECTION_ header
    is followed by rows in the column order given by that section header comment."""
    sections = _read_sections(text)
    return BenchmarkInstance(
        horizon_days=int(sections["SECTION_HORIZON"][0][0]),
        shifts=tuple(_shift(row) for row in sections.get("SECTION_SHIFTS", [])),
        staff=tuple(_staff(row) for row in sections.get("SECTION_STAFF", [])),
        days_off=_days_off(sections.get("SECTION_DAYS_OFF", [])),
        on_requests=tuple(_request(row) for row in sections.get("SECTION_SHIFT_ON_REQUESTS", [])),
        off_requests=tuple(_request(row) for row in sections.get("SECTION_SHIFT_OFF_REQUESTS", [])),
        cover=tuple(_cover(row) for row in sections.get("SECTION_COVER", [])),
    )


def solve_benchmark(instance: BenchmarkInstance, params: SolveParams) -> SolveResult:
    """Exact CP-SAT model of the published objective: unmet on-requests, violated off-requests,
    and under and over cover weighted per day and shift. Hard rules follow the benchmark format
    page. Status is returned as is; OPTIMAL means proven."""
    model = cp_model.CpModel()
    work = _work_variables(model, instance)
    on = _day_flags(model, instance, work)
    _add_one_shift_per_day(model, instance, work)
    _add_days_off(model, instance, work)
    _add_forbidden_next(model, instance, work)
    _add_workload(model, instance, work)
    _add_consecutive_shifts(model, instance, on)
    _add_min_consecutive_shifts(model, instance, on)
    _add_min_consecutive_days_off(model, instance, on)
    _add_weekends(model, instance, on)
    terms = _request_terms(instance, work) + _cover_terms(model, instance, work)
    model.minimize(sum(terms, 0))
    _, result = run_cp_model(model, params)
    return result


def _read_sections(text: str) -> dict[str, list[list[str]]]:
    sections: dict[str, list[list[str]]] = {}
    current: list[list[str]] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("SECTION_"):
            current = sections.setdefault(line, [])
        elif current is None:
            raise ValueError(f"data before the first SECTION_ header: {line}")
        else:
            current.append([field.strip() for field in line.split(",")])
    return sections


def _shift(row: list[str]) -> BenchmarkShift:
    forbidden = row[2] if len(row) > 2 else ""
    return BenchmarkShift(
        id=row[0],
        minutes=int(row[1]),
        forbidden_next=frozenset(name for name in forbidden.split("|") if name),
    )


def _caps(text: str) -> dict[str, int]:
    caps: dict[str, int] = {}
    for item in text.split("|"):
        name, cap = item.split("=")
        caps[name] = int(cap)
    return caps


def _staff(row: list[str]) -> BenchmarkStaff:
    return BenchmarkStaff(
        id=row[0],
        max_shifts=_caps(row[1]),
        max_total_minutes=int(row[2]),
        min_total_minutes=int(row[3]),
        max_consecutive_shifts=int(row[4]),
        min_consecutive_shifts=int(row[5]),
        min_consecutive_days_off=int(row[6]),
        max_weekends=int(row[7]),
    )


def _days_off(rows: list[list[str]]) -> dict[str, frozenset[int]]:
    result: dict[str, frozenset[int]] = {}
    for row in rows:
        days = frozenset(int(day) for day in row[1:])
        result[row[0]] = result.get(row[0], frozenset()) | days
    return result


def _request(row: list[str]) -> ShiftRequest:
    return ShiftRequest(staff=row[0], day=int(row[1]), shift=row[2], weight=int(row[3]))


def _cover(row: list[str]) -> CoverRequirement:
    return CoverRequirement(
        day=int(row[0]),
        shift=row[1],
        requirement=int(row[2]),
        under_weight=int(row[3]),
        over_weight=int(row[4]),
    )


def _work_variables(
    model: cp_model.CpModel, instance: BenchmarkInstance
) -> dict[tuple[str, int, str], Any]:
    return {
        (member.id, day, shift.id): model.new_bool_var(f"work_{member.id}_{day}_{shift.id}")
        for member in instance.staff
        for day in range(instance.horizon_days)
        for shift in instance.shifts
    }


def _day_flags(
    model: cp_model.CpModel,
    instance: BenchmarkInstance,
    work: dict[tuple[str, int, str], Any],
) -> dict[tuple[str, int], Any]:
    flags: dict[tuple[str, int], Any] = {}
    for member in instance.staff:
        for day in range(instance.horizon_days):
            flag = model.new_bool_var(f"on_{member.id}_{day}")
            model.add(flag == sum(work[(member.id, day, shift.id)] for shift in instance.shifts))
            flags[(member.id, day)] = flag
    return flags


def _add_one_shift_per_day(
    model: cp_model.CpModel,
    instance: BenchmarkInstance,
    work: dict[tuple[str, int, str], Any],
) -> None:
    for member in instance.staff:
        for day in range(instance.horizon_days):
            model.add_at_most_one(work[(member.id, day, shift.id)] for shift in instance.shifts)


def _add_days_off(
    model: cp_model.CpModel,
    instance: BenchmarkInstance,
    work: dict[tuple[str, int, str], Any],
) -> None:
    for staff_id, days in instance.days_off.items():
        for day in days:
            for shift in instance.shifts:
                model.add(work[(staff_id, day, shift.id)] == 0)


def _add_forbidden_next(
    model: cp_model.CpModel,
    instance: BenchmarkInstance,
    work: dict[tuple[str, int, str], Any],
) -> None:
    for member in instance.staff:
        for day in range(instance.horizon_days - 1):
            for shift in instance.shifts:
                for following in shift.forbidden_next:
                    model.add(
                        work[(member.id, day, shift.id)] + work[(member.id, day + 1, following)]
                        <= 1
                    )


def _add_workload(
    model: cp_model.CpModel,
    instance: BenchmarkInstance,
    work: dict[tuple[str, int, str], Any],
) -> None:
    for member in instance.staff:
        minutes = sum(
            shift.minutes * work[(member.id, day, shift.id)]
            for day in range(instance.horizon_days)
            for shift in instance.shifts
        )
        model.add(minutes <= member.max_total_minutes)
        model.add(minutes >= member.min_total_minutes)
        for shift in instance.shifts:
            count = sum(work[(member.id, day, shift.id)] for day in range(instance.horizon_days))
            model.add(count <= member.max_shifts[shift.id])


def _add_consecutive_shifts(
    model: cp_model.CpModel,
    instance: BenchmarkInstance,
    on: dict[tuple[str, int], Any],
) -> None:
    for member in instance.staff:
        limit = member.max_consecutive_shifts
        for start in range(instance.horizon_days - limit):
            window = range(start, start + limit + 1)
            model.add(sum(on[(member.id, day)] for day in window) <= limit)


def _add_min_consecutive_shifts(
    model: cp_model.CpModel,
    instance: BenchmarkInstance,
    on: dict[tuple[str, int], Any],
) -> None:
    horizon = instance.horizon_days
    for member in instance.staff:
        for length in range(1, member.min_consecutive_shifts):
            for start in range(1, horizon - length):
                block = range(start, start + length)
                model.add_bool_or(
                    [on[(member.id, start - 1)], on[(member.id, start + length)]]
                    + [on[(member.id, day)].Not() for day in block]
                )


def _add_min_consecutive_days_off(
    model: cp_model.CpModel,
    instance: BenchmarkInstance,
    on: dict[tuple[str, int], Any],
) -> None:
    horizon = instance.horizon_days
    for member in instance.staff:
        for length in range(1, member.min_consecutive_days_off):
            for start in range(1, horizon - length):
                block = range(start, start + length)
                model.add_bool_or(
                    [on[(member.id, start - 1)].Not(), on[(member.id, start + length)].Not()]
                    + [on[(member.id, day)] for day in block]
                )


def _add_weekends(
    model: cp_model.CpModel,
    instance: BenchmarkInstance,
    on: dict[tuple[str, int], Any],
) -> None:
    for member in instance.staff:
        worked: list[Any] = []
        for week_start in range(0, instance.horizon_days, DAYS_PER_WEEK):
            days = [
                week_start + offset
                for offset in (SATURDAY, SUNDAY)
                if week_start + offset < instance.horizon_days
            ]
            if not days:
                continue
            flag = model.new_bool_var(f"weekend_{member.id}_{week_start}")
            for day in days:
                model.add(on[(member.id, day)] <= flag)
            worked.append(flag)
        if worked:
            model.add(sum(worked) <= member.max_weekends)


def _request_terms(
    instance: BenchmarkInstance,
    work: dict[tuple[str, int, str], Any],
) -> list[Any]:
    on_terms = [
        request.weight * (1 - work[(request.staff, request.day, request.shift)])
        for request in instance.on_requests
    ]
    off_terms = [
        request.weight * work[(request.staff, request.day, request.shift)]
        for request in instance.off_requests
    ]
    return on_terms + off_terms


def _cover_terms(
    model: cp_model.CpModel,
    instance: BenchmarkInstance,
    work: dict[tuple[str, int, str], Any],
) -> list[Any]:
    terms: list[Any] = []
    for cover in instance.cover:
        count = sum(work[(member.id, cover.day, cover.shift)] for member in instance.staff)
        label = f"{cover.day}_{cover.shift}"
        under = model.new_int_var(0, cover.requirement, f"under_{label}")
        over = model.new_int_var(0, len(instance.staff), f"over_{label}")
        model.add(under >= cover.requirement - count)
        model.add(over >= count - cover.requirement)
        terms.append(cover.under_weight * under + cover.over_weight * over)
    return terms
