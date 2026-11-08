from dataclasses import dataclass, replace

from shiftopt.domain import Instance, ShiftType
from shiftopt.sensitivity.parametric import DEFAULT_MULTIPLIERS, scale_demand

SIX_START_HOURS = (0, 4, 8, 12, 16, 20)
SHIFT_LENGTH = 8


@dataclass(frozen=True)
class Scenario:
    name: str
    instance: Instance


def demand_scenarios(
    base: Instance, multipliers: tuple[float, ...] = DEFAULT_MULTIPLIERS
) -> list[Scenario]:
    """The base problem first, then the same problem with demand scaled by each multiplier."""
    scenarios = [Scenario("base", base)]
    scenarios.extend(
        Scenario(f"lambda={multiplier:.1f}", scale_demand(base, multiplier))
        for multiplier in multipliers
    )
    return scenarios


def staffing_scenarios(base: Instance, removals: tuple[int, ...] = (1, 2, 5)) -> list[Scenario]:
    """Drop the last employees by id, so the same reduction is reproducible."""
    ordered = sorted(base.employees, key=lambda employee: employee.id)
    scenarios = []
    for removed in removals:
        if removed >= len(ordered):
            raise ValueError(f"cannot remove {removed} of {len(ordered)} employees")
        kept = tuple(ordered[: len(ordered) - removed])
        scenarios.append(Scenario(f"minus-{removed}", replace(base, employees=kept)))
    return scenarios


def shift_pattern_scenarios(base: Instance) -> list[Scenario]:
    """Three fixed starts (the base shift types) against six starts every 4 hours."""
    six = tuple(ShiftType(f"s{start:02d}", start, SHIFT_LENGTH) for start in SIX_START_HOURS)
    return [
        Scenario("shifts-3", base),
        Scenario("shifts-6", replace(base, shift_types=six)),
    ]
