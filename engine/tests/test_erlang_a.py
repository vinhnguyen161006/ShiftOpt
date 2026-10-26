import time

import pytest

from shiftopt.staffing.erlang import (
    erlang_a_queue_probabilities,
    erlang_a_service_level,
    erlang_c_service_level,
    required_staff_erlang_a,
    required_staff_erlang_c,
)
from shiftopt.time_grid import HOURS_PER_WEEK

HANDLE_SECONDS = 180.0
ANSWER_SECONDS = 20.0
HUGE_PATIENCE = 1e12


def flat_rates(value: float) -> list[float]:
    return [value] * HOURS_PER_WEEK


def test_queue_probabilities_sum_to_one() -> None:
    probabilities = erlang_a_queue_probabilities(12, 10.0, HANDLE_SECONDS, 60.0)
    assert sum(probabilities) == pytest.approx(1.0, abs=1e-12)
    assert all(probability >= 0 for probability in probabilities)


def test_patience_to_infinity_matches_erlang_c() -> None:
    for agents, load in [(12, 10.0), (20, 15.0)]:
        erlang_a = erlang_a_service_level(
            agents, load, HANDLE_SECONDS, HUGE_PATIENCE, ANSWER_SECONDS
        )
        erlang_c = erlang_c_service_level(agents, load, HANDLE_SECONDS, ANSWER_SECONDS)
        assert erlang_a == pytest.approx(erlang_c, abs=1e-6)


def test_zero_answer_time_counts_only_idle_agents() -> None:
    probabilities = erlang_a_queue_probabilities(12, 10.0, HANDLE_SECONDS, 60.0)
    assert erlang_a_service_level(12, 10.0, HANDLE_SECONDS, 60.0, 0.0) == pytest.approx(
        sum(probabilities[:12]), abs=1e-12
    )


def test_service_level_is_monotone_in_answer_time() -> None:
    levels = [
        erlang_a_service_level(10, 9.0, HANDLE_SECONDS, 60.0, answer)
        for answer in (0.0, 10.0, 20.0, 60.0, 600.0)
    ]
    assert levels == sorted(levels)
    assert all(0.0 <= level <= 1.0 for level in levels)


def test_erlang_a_never_needs_more_agents_than_erlang_c() -> None:
    rates = [float(rate) for rate in range(10, 10 + HOURS_PER_WEEK)]
    erlang_a = required_staff_erlang_a(rates, HANDLE_SECONDS, 60.0, 0.8, ANSWER_SECONDS, 1)
    erlang_c = required_staff_erlang_c(rates, HANDLE_SECONDS, 0.8, ANSWER_SECONDS, 1)
    assert all(a <= c for a, c in zip(erlang_a, erlang_c, strict=True))


def test_required_staff_erlang_a_is_minimal() -> None:
    staff = required_staff_erlang_a(flat_rates(200.0), HANDLE_SECONDS, 60.0, 0.8, ANSWER_SECONDS, 1)
    agents = staff[0]
    assert erlang_a_service_level(agents, 10.0, HANDLE_SECONDS, 60.0, ANSWER_SECONDS) >= 0.8
    assert (
        agents == 1
        or erlang_a_service_level(agents - 1, 10.0, HANDLE_SECONDS, 60.0, ANSWER_SECONDS) < 0.8
    )


def test_required_staff_erlang_a_uses_minimum_for_idle_hours() -> None:
    staff = required_staff_erlang_a(flat_rates(0.0), HANDLE_SECONDS, 60.0, 0.8, ANSWER_SECONDS, 2)
    assert staff == (2,) * HOURS_PER_WEEK


@pytest.mark.parametrize(
    ("patience", "target", "answer", "min_staff", "message"),
    [
        (0.0, 0.8, ANSWER_SECONDS, 1, "patience_seconds"),
        (60.0, 1.0, ANSWER_SECONDS, 1, "target_service_level"),
        (60.0, 0.8, -1.0, 1, "answer_seconds"),
        (60.0, 0.8, ANSWER_SECONDS, -1, "min_staff"),
    ],
)
def test_required_staff_erlang_a_rejects_bad_input(
    patience: float, target: float, answer: float, min_staff: int, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        required_staff_erlang_a(
            flat_rates(10.0), HANDLE_SECONDS, patience, target, answer, min_staff
        )


def test_queue_functions_reject_bad_input() -> None:
    with pytest.raises(ValueError, match="agents"):
        erlang_a_queue_probabilities(0, 1.0, HANDLE_SECONDS, 60.0)
    with pytest.raises(ValueError, match="offered_load"):
        erlang_a_queue_probabilities(2, 0.0, HANDLE_SECONDS, 60.0)
    with pytest.raises(ValueError, match="patience"):
        erlang_a_queue_probabilities(2, 1.0, HANDLE_SECONDS, 0.0)


def test_huge_answer_time_terminates_quickly() -> None:
    started = time.perf_counter()
    level = erlang_a_service_level(200, 190.0, HANDLE_SECONDS, 600.0, 1e4)
    assert 0.0 <= level <= 1.0
    assert time.perf_counter() - started < 10.0


def test_patience_above_cap_is_rejected() -> None:
    with pytest.raises(ValueError, match="patience_seconds"):
        required_staff_erlang_a(flat_rates(10.0), HANDLE_SECONDS, 3601.0, 0.8, ANSWER_SECONDS, 1)


def test_staffing_search_over_a_day_stays_fast() -> None:
    started = time.perf_counter()
    staff = required_staff_erlang_a(
        flat_rates(60.0), HANDLE_SECONDS, 3600.0, 0.8, ANSWER_SECONDS, 1
    )
    assert len(staff) == HOURS_PER_WEEK
    assert time.perf_counter() - started < 10.0
