from collections.abc import Sequence

from shiftopt.domain import Instance


def apply_demand_scenario(instance: Instance, load: Sequence[float], uplift: float) -> Instance:
    """TODO: build a scenario instance from holiday, promotion or rain covariates of the dataset;
    observed sales under-state real demand in those scenarios."""
    raise NotImplementedError
