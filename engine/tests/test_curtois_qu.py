from pathlib import Path

import pytest

from shiftopt.benchmarks.curtois_qu import (
    BenchmarkInstance,
    BenchmarkShift,
    BenchmarkStaff,
    CoverRequirement,
    ShiftRequest,
    parse_instance,
    solve_benchmark,
)
from shiftopt.solvers.base import SolveParams, SolveStatus

TINY_TEXT = """# comment line
SECTION_HORIZON
# Monday start
2

SECTION_SHIFTS
D,480,
N,600,D

SECTION_STAFF
A,D=2|N=1,960,480,4,1,1,1

SECTION_DAYS_OFF
A,1

SECTION_SHIFT_ON_REQUESTS
A,0,D,3

SECTION_SHIFT_OFF_REQUESTS
A,1,N,2

SECTION_COVER
0,D,1,100,1
1,N,0,100,1
"""

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "benchmarks" / "curtois_qu"
PARAMS = SolveParams(time_limit_seconds=60.0, relative_gap_limit=0.0, num_workers=1, random_seed=0)
DAY = BenchmarkShift("D", 480, frozenset())


def _one_staff(
    horizon: int,
    *,
    shifts: tuple[BenchmarkShift, ...] = (DAY,),
    max_consecutive: int = 7,
    min_consecutive: int = 1,
    min_off: int = 1,
    max_weekends: int = 99,
    cover: tuple[CoverRequirement, ...] = (),
    on: tuple[ShiftRequest, ...] = (),
) -> BenchmarkInstance:
    member = BenchmarkStaff(
        id="A",
        max_shifts={shift.id: horizon for shift in shifts},
        max_total_minutes=10_000,
        min_total_minutes=0,
        max_consecutive_shifts=max_consecutive,
        min_consecutive_shifts=min_consecutive,
        min_consecutive_days_off=min_off,
        max_weekends=max_weekends,
    )
    return BenchmarkInstance(
        horizon_days=horizon,
        shifts=shifts,
        staff=(member,),
        days_off={},
        on_requests=on,
        off_requests=(),
        cover=cover,
    )


def test_parse_tiny_instance() -> None:
    instance = parse_instance(TINY_TEXT)

    assert instance.horizon_days == 2
    assert instance.shifts == (
        BenchmarkShift("D", 480, frozenset()),
        BenchmarkShift("N", 600, frozenset({"D"})),
    )
    assert instance.staff == (BenchmarkStaff("A", {"D": 2, "N": 1}, 960, 480, 4, 1, 1, 1),)
    assert instance.days_off == {"A": frozenset({1})}
    assert instance.on_requests == (ShiftRequest("A", 0, "D", 3),)
    assert instance.off_requests == (ShiftRequest("A", 1, "N", 2),)
    assert instance.cover == (
        CoverRequirement(0, "D", 1, 100, 1),
        CoverRequirement(1, "N", 0, 100, 1),
    )


def test_solve_tiny_known_optimum() -> None:
    """Two days, one employee, at most one day of work in a row. Working day 1 leaves day 0
    uncovered (100) and meets the on-request (0). Working day 0 leaves day 1 uncovered (100) and
    misses the request (3), so 103. Optimum 100."""
    instance = _one_staff(
        2,
        max_consecutive=1,
        cover=(CoverRequirement(0, "D", 1, 100, 1), CoverRequirement(1, "D", 1, 100, 1)),
        on=(ShiftRequest("A", 1, "D", 3),),
    )

    result = solve_benchmark(instance, PARAMS)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective == 100


def test_min_consecutive_shifts_exempt_at_horizon_start() -> None:
    """Day 0 alone is a block of one shift touching the horizon start, so it is exempt from the
    minimum of two. Working day 0 costs nothing. Without the exemption the block would have to
    grow to day 1, which costs 50 on over-cover."""
    instance = _one_staff(
        3,
        max_consecutive=3,
        min_consecutive=2,
        cover=(
            CoverRequirement(0, "D", 1, 100, 1),
            CoverRequirement(1, "D", 0, 100, 50),
            CoverRequirement(2, "D", 0, 100, 50),
        ),
    )

    result = solve_benchmark(instance, PARAMS)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective == 0


def test_forbidden_next_shift_blocks_consecutive_days() -> None:
    """D may not follow D. Covering both days needs two shifts in a row, so one day stays
    uncovered (100). Without the forbidden pair the cost would be 0."""
    forbidden_pair = BenchmarkShift("D", 480, frozenset({"D"}))
    instance = _one_staff(
        2,
        shifts=(forbidden_pair,),
        max_consecutive=2,
        cover=(CoverRequirement(0, "D", 1, 100, 1), CoverRequirement(1, "D", 1, 100, 1)),
    )

    result = solve_benchmark(instance, PARAMS)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective == 100


def test_max_weekends_blocks_weekend_cover() -> None:
    """Horizon of one week with zero weekends allowed: the Saturday and Sunday requirements
    cannot be met, so each costs 100."""
    instance = _one_staff(
        7,
        max_weekends=0,
        cover=(CoverRequirement(5, "D", 1, 100, 1), CoverRequirement(6, "D", 1, 100, 1)),
    )

    result = solve_benchmark(instance, PARAMS)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective == 200


def test_min_consecutive_days_off_blocks_single_gap() -> None:
    """A one-day off block between two shifts breaks the minimum of two days off. Only one of
    day 0 and day 2 can be covered, so the other costs 100. Without the minimum the employee
    could work both and the cost would be 0."""
    instance = _one_staff(
        4,
        max_consecutive=1,
        min_off=2,
        cover=(CoverRequirement(0, "D", 1, 100, 1), CoverRequirement(2, "D", 1, 100, 1)),
    )

    result = solve_benchmark(instance, PARAMS)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective == 100


@pytest.mark.skipif(
    not (DATA_FILE / "Instance1.txt").exists(),
    reason="run engine/benchmarks/download_curtois_qu.py first",
)
def test_instance1_reaches_published_optimum() -> None:
    instance = parse_instance((DATA_FILE / "Instance1.txt").read_text(encoding="ascii"))

    result = solve_benchmark(instance, PARAMS)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective == 607
