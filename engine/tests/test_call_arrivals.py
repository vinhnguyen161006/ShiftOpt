import pytest

from shiftopt.staffing.call_arrivals import simulate_arrival_rates
from shiftopt.staffing.erlang import required_staff_erlang_a
from shiftopt.time_grid import HOURS_PER_WEEK


def test_same_seed_gives_same_week() -> None:
    assert simulate_arrival_rates(100.0, noise=0.2, seed=7) == simulate_arrival_rates(
        100.0, noise=0.2, seed=7
    )


def test_different_seed_changes_noisy_week() -> None:
    assert simulate_arrival_rates(100.0, noise=0.2, seed=7) != simulate_arrival_rates(
        100.0, noise=0.2, seed=8
    )


def test_week_has_168_non_negative_rates() -> None:
    rates = simulate_arrival_rates(100.0, noise=0.5, seed=1)
    assert len(rates) == HOURS_PER_WEEK
    assert all(rate >= 0 for rate in rates)


def test_peak_hour_is_busier_than_night_without_noise() -> None:
    rates = simulate_arrival_rates(100.0)
    assert rates[11] > rates[3]
    assert rates[19] > rates[3]


def test_peak_near_midnight_spills_into_early_hours() -> None:
    rates = simulate_arrival_rates(100.0, peak_hours=(23.0,))
    assert rates[22] == pytest.approx(rates[0])
    assert rates[0] > rates[12]


def test_saturday_factor_scales_the_whole_day() -> None:
    rates = simulate_arrival_rates(100.0, weekday_factors=(1.0,) * 5 + (2.0, 1.0))
    assert rates[5 * 24 + 11] == pytest.approx(2 * rates[11])


def test_generated_week_feeds_erlang_a() -> None:
    rates = simulate_arrival_rates(60.0, noise=0.1, seed=3)
    staff = required_staff_erlang_a(rates, 180.0, 60.0, 0.8, 20.0, 1)
    assert len(staff) == HOURS_PER_WEEK
    assert all(agents >= 1 for agents in staff)


def test_rejects_negative_base_rate() -> None:
    with pytest.raises(ValueError, match="base_rate"):
        simulate_arrival_rates(-1.0)


def test_rejects_wrong_weekday_count() -> None:
    with pytest.raises(ValueError, match="weekday_factors"):
        simulate_arrival_rates(10.0, weekday_factors=(1.0,) * 6)


def test_rejects_zero_weekday_factor() -> None:
    with pytest.raises(ValueError, match="weekday_factors"):
        simulate_arrival_rates(10.0, weekday_factors=(1.0,) * 6 + (0.0,))


def test_rejects_peak_hour_outside_day() -> None:
    with pytest.raises(ValueError, match="peak_hours"):
        simulate_arrival_rates(10.0, peak_hours=(24.0,))


def test_rejects_non_positive_peak_width() -> None:
    with pytest.raises(ValueError, match="peak_width"):
        simulate_arrival_rates(10.0, peak_width=0.0)


def test_rejects_negative_noise() -> None:
    with pytest.raises(ValueError, match="noise"):
        simulate_arrival_rates(10.0, noise=-0.1)
