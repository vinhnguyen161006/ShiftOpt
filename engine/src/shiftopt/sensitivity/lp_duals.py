from shiftopt.domain import Instance


def lp_relaxation_duals(instance: Instance, hourly_wage: int) -> tuple[float, ...]:
    """TODO: dual per hour of the week from the set covering LP relaxation, an approximation of
    the marginal cost of one more required person. Label it approximate in every output; the
    integrality gap can be large. A None dual from the solver interface becomes 0.0."""
    raise NotImplementedError
