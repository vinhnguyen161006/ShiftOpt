from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from shiftopt.domain import Instance
from shiftopt.sensitivity.parametric import Evaluation, Resolver
from shiftopt.staffing.linear import (
    DEFAULT_ALPHA,
    DEFAULT_MIN_STAFF,
    DEFAULT_NIGHT_MIN_STAFF,
    DEFAULT_PRODUCTIVITY,
    required_staff,
    tolerant_ceil,
)
from shiftopt.time_grid import HOURS_PER_DAY

PROMOTION_UPLIFT = 1.43
PROMOTION_SOURCE = (
    "median promotion uplift, FreshRetailNet paper arXiv:2505.16319 v5; "
    "suggested default only, not estimated for this team"
)


@dataclass(frozen=True)
class DemandScenario:
    """day_multipliers scales the demand of each weekday (0 = Monday). Days not listed keep
    their demand. source is shown on the UI next to every scenario result."""

    name: str
    day_multipliers: Mapping[int, float]
    source: str


def apply_demand_scenario(instance: Instance, scenario: DemandScenario) -> Instance:
    for day, multiplier in scenario.day_multipliers.items():
        if not 0 <= day < 7:
            raise ValueError(f"scenario {scenario.name}: day must be in [0, 7)")
        if multiplier <= 0:
            raise ValueError(f"scenario {scenario.name}: multiplier must be positive")
    demand = tuple(
        tolerant_ceil(scenario.day_multipliers.get(hour // HOURS_PER_DAY, 1.0) * value)
        for hour, value in enumerate(instance.demand)
    )
    return replace(instance, demand=demand)


def promotion_scenario(days: Sequence[int], uplift: float = PROMOTION_UPLIFT) -> DemandScenario:
    return DemandScenario(
        name="promotion",
        day_multipliers=dict.fromkeys(days, uplift),
        source=PROMOTION_SOURCE,
    )


def compare_scenarios(
    instance: Instance, scenarios: Sequence[DemandScenario], resolver: Resolver
) -> tuple[tuple[str, Evaluation], ...]:
    rows = [("baseline", resolver(instance))]
    rows.extend(
        (scenario.name, resolver(apply_demand_scenario(instance, scenario)))
        for scenario in scenarios
    )
    return tuple(rows)


@dataclass(frozen=True)
class StaffingAssumption:
    alpha: float = DEFAULT_ALPHA
    productivity: float = DEFAULT_PRODUCTIVITY
    min_staff: float = DEFAULT_MIN_STAFF
    night_min_staff: float = DEFAULT_NIGHT_MIN_STAFF


STAFFING_FIELDS = ("alpha", "productivity", "min_staff", "night_min_staff")


def sweep_staffing_assumption(
    template: Instance,
    load: Sequence[float],
    base: StaffingAssumption,
    field: str,
    values: Sequence[float],
    resolver: Resolver,
) -> list[tuple[float, Evaluation]]:
    """Re-derive demand from the load index for each value of one conversion assumption, then
    re-solve. Makes the effect of alpha, productivity or the staff floors visible instead of
    hiding it."""
    if field not in STAFFING_FIELDS:
        raise ValueError(f"field must be one of {STAFFING_FIELDS}")
    points: list[tuple[float, Evaluation]] = []
    for value in values:
        assumption = replace(base, **{field: value})
        demand = required_staff(
            load,
            alpha=assumption.alpha,
            productivity=assumption.productivity,
            min_staff=_as_count(assumption.min_staff),
            night_min_staff=_as_count(assumption.night_min_staff),
            rules=template.rules,
        )
        points.append((value, resolver(replace(template, demand=demand))))
    return points


def _as_count(value: float) -> int:
    if not float(value).is_integer():
        raise ValueError("staff floors must be whole numbers")
    return int(value)
