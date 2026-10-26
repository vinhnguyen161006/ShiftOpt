from dataclasses import dataclass, replace
from typing import Any

from ortools.sat.python import cp_model

from shiftopt.constraints.sequences import consecutive_day_windows, forbidden_shift_pairs
from shiftopt.domain import Assignment, Employee, Instance, Solution
from shiftopt.models.implicit_breaks import solve_with_implicit_breaks
from shiftopt.solvers.base import SolveParams, SolveResult, SolveStatus
from shiftopt.solvers.cpsat import SOLVER_NAME, run_cp_model, with_time_share
from shiftopt.staffing.linear import tolerant_ceil
from shiftopt.time_grid import DAYS_PER_WEEK, HOURS_PER_WEEK, hour_of_week, shift_hours


@dataclass(frozen=True)
class RosterOutcome:
    solution: Solution
    result: SolveResult
    phases: tuple[SolveResult, ...]
    understaffed_hours: int | None
    night_spread: int | None
    preference_misses: int | None
    approximate: bool = False


def solve_roster(
    instance: Instance,
    params: SolveParams,
    *,
    symmetry_breaking: bool = False,
    decompose: bool = False,
) -> RosterOutcome:
    """Per-employee roster with Boolean work[e, d, s] solved by CP-SAT on a cyclic week.

    Hard: at most one shift per day, weekly hours (Article 105), rest between shifts from the
    general formula (Article 110), maximum consecutive days, at least 24 consecutive hours without
    work (Article 111), one rest break per shift that needs one (Article 109), and no shift on an
    unavailable day. Soft: coverage through shortfall variables, so the model is always feasible.
    Objective: lexicographic, one CP-SAT solve per tier: shortfall, labour cost with the night
    premium (Article 98), night-shift spread, then preference misses. Each tier is capped at the
    optimum of the tier before. Status is OPTIMAL only when every tier proves optimality.

    symmetry_breaking orders employees that are identical in wage and carry no requests by their
    shift count; this keeps the optimum and only removes permutations of the same roster.
    decompose first solves the aggregate model with implicit breaks, then caps the number of starts
    per day and shift type to that head count. The result is then an approximation and is never
    reported as OPTIMAL.
    """
    if not decompose:
        model = _RosterModel(instance)
        if symmetry_breaking:
            model.add_symmetry_breaking()
        return model.solve(params)
    half = replace(params, time_limit_seconds=params.time_limit_seconds / 2)
    model = _RosterModel(instance)
    if symmetry_breaking:
        model.add_symmetry_breaking()
    model.add_start_caps(_aggregate_starts(instance, half))
    outcome = model.solve(half)
    return replace(outcome, approximate=True, result=_downgrade(outcome.result))


def symmetry_pairs(employees: tuple[Employee, ...]) -> list[tuple[int, int]]:
    """Consecutive index pairs of employees with equal wage and no requests. Only these are
    interchangeable: swapping two employees with different contracts or requests can change the
    optimum."""
    groups: dict[int, list[int]] = {}
    for index, employee in enumerate(employees):
        if not employee.has_requests:
            groups.setdefault(employee.hourly_wage, []).append(index)
    return [
        (members[position], members[position + 1])
        for members in groups.values()
        for position in range(len(members) - 1)
    ]


def _aggregate_starts(instance: Instance, params: SolveParams) -> dict[tuple[int, str], int]:
    wages = sorted(employee.hourly_wage for employee in instance.employees)
    if not wages:
        return {}
    median_wage = wages[len(wages) // 2]
    counts = solve_with_implicit_breaks(instance, median_wage, params).counts
    return {key: tolerant_ceil(value) for key, value in counts.items()}


def _downgrade(result: SolveResult) -> SolveResult:
    if result.status is not SolveStatus.OPTIMAL:
        return result
    return replace(result, status=SolveStatus.FEASIBLE)


class _RosterModel:
    def __init__(self, instance: Instance) -> None:
        self.instance = instance
        self.rules = instance.rules
        self.employees = instance.employees
        self.shifts = tuple(
            shift for shift in instance.shift_types if shift.length <= self.rules.max_daily_hours
        )
        self.shift_index = {shift.name: index for index, shift in enumerate(self.shifts)}
        self.model = cp_model.CpModel()
        self.zero = self.model.new_constant(0)
        self.all_vars: list[Any] = []
        self.work: dict[tuple[int, int, int], Any] = {}
        self.breaks: dict[tuple[int, int, int, int], Any] = {}
        self.break_at: list[list[Any]] = [[] for _ in range(HOURS_PER_WEEK)]
        self.hour_work: list[list[list[Any]]] = [
            [[] for _ in range(HOURS_PER_WEEK)] for _ in self.employees
        ]
        self.shortfall: list[Any] = []
        self.night_counts: list[Any] = []
        self.night_max: Any = None
        self.night_min: Any = None
        self._build()

    def _bool(self, name: str) -> Any:
        variable = self.model.new_bool_var(name)
        self.all_vars.append(variable)
        return variable

    def _sum(self, terms: Any) -> Any:
        return sum(terms, self.zero)

    def _build(self) -> None:
        self._create_shift_variables()
        self._add_one_shift_per_day()
        self._add_weekly_hours()
        self._add_rest_between_shifts()
        self._add_consecutive_days()
        self._add_weekly_rest()
        self._add_breaks_and_coverage()
        self._add_night_spread()

    def _create_shift_variables(self) -> None:
        for e_index, employee in enumerate(self.employees):
            for day in range(DAYS_PER_WEEK):
                if day in employee.unavailable_days:
                    continue
                for s_index, shift in enumerate(self.shifts):
                    work = self._bool(f"work_{e_index}_{day}_{s_index}")
                    self.work[(e_index, day, s_index)] = work
                    for hour in shift_hours(day, shift.start_hour, shift.length):
                        self.hour_work[e_index][hour].append(work)
                    for offset in shift.break_window(self.rules):
                        broken = self._bool(f"break_{e_index}_{day}_{s_index}_{offset}")
                        self.breaks[(e_index, day, s_index, offset)] = broken
                        self.break_at[hour_of_week(day, shift.start_hour + offset)].append(broken)

    def _add_one_shift_per_day(self) -> None:
        for e_index in range(len(self.employees)):
            for day in range(DAYS_PER_WEEK):
                day_shifts = [
                    self.work[(e_index, day, s_index)]
                    for s_index in range(len(self.shifts))
                    if (e_index, day, s_index) in self.work
                ]
                if len(day_shifts) > 1:
                    self.model.add_at_most_one(day_shifts)

    def _add_weekly_hours(self) -> None:
        for e_index in range(len(self.employees)):
            terms = [
                self.shifts[s_index].length * work
                for (e, _, s_index), work in self.work.items()
                if e == e_index
            ]
            self.model.add(self._sum(terms) <= self.rules.max_weekly_hours)

    def _add_rest_between_shifts(self) -> None:
        pairs_by_offset: dict[int, list[tuple[int, int]]] = {}
        for prev_name, next_name, offset in forbidden_shift_pairs(self.shifts, self.rules):
            pairs_by_offset.setdefault(offset, []).append(
                (self.shift_index[prev_name], self.shift_index[next_name])
            )
        for e_index in range(len(self.employees)):
            for day in range(DAYS_PER_WEEK):
                for offset, pairs in pairs_by_offset.items():
                    next_day = (day + offset) % DAYS_PER_WEEK
                    for prev_s, next_s in pairs:
                        prev = self.work.get((e_index, day, prev_s))
                        nxt = self.work.get((e_index, next_day, next_s))
                        if prev is not None and nxt is not None:
                            self.model.add(prev + nxt <= 1)

    def _add_consecutive_days(self) -> None:
        for e_index in range(len(self.employees)):
            for window in consecutive_day_windows(self.rules):
                terms = [
                    self.work[(e_index, day, s_index)]
                    for day in window
                    for s_index in range(len(self.shifts))
                    if (e_index, day, s_index) in self.work
                ]
                if terms:
                    self.model.add(self._sum(terms) <= self.rules.max_consecutive_days)

    def _add_weekly_rest(self) -> None:
        for e_index in range(len(self.employees)):
            rest_starts = []
            for start in range(HOURS_PER_WEEK):
                rest_start = self._bool(f"rest_{e_index}_{start}")
                rest_starts.append(rest_start)
                window_work = [
                    work
                    for offset in range(self.rules.weekly_rest_hours)
                    for work in self.hour_work[e_index][(start + offset) % HOURS_PER_WEEK]
                ]
                if window_work:
                    self.model.add(self._sum(window_work) == 0).only_enforce_if(rest_start)
            self.model.add_bool_or(rest_starts)

    def _add_breaks_and_coverage(self) -> None:
        for (e_index, day, s_index), work in self.work.items():
            window = self.shifts[s_index].break_window(self.rules)
            breaks = [self.breaks[(e_index, day, s_index, offset)] for offset in window]
            self.model.add(self._sum(breaks) == work)
        for hour in range(HOURS_PER_WEEK):
            present = self._sum(
                work for employee_hours in self.hour_work for work in employee_hours[hour]
            )
            shortfall = self.model.new_int_var(0, self.instance.demand[hour], f"short_{hour}")
            self.shortfall.append(shortfall)
            self.model.add(
                present - self._sum(self.break_at[hour]) + shortfall >= self.instance.demand[hour]
            )

    def _add_night_spread(self) -> None:
        if len(self.employees) < 2:
            return
        for e_index in range(len(self.employees)):
            nights = [
                work
                for (e, _, s_index), work in self.work.items()
                if e == e_index and self.shifts[s_index].is_night_shift(self.rules)
            ]
            count = self.model.new_int_var(0, len(self.work) + 1, f"night_{e_index}")
            self.model.add(count == self._sum(nights))
            self.night_counts.append(count)
        self.night_max = self.model.new_int_var(0, len(self.work) + 1, "night_max")
        self.night_min = self.model.new_int_var(0, len(self.work) + 1, "night_min")
        self.model.add_max_equality(self.night_max, self.night_counts)
        self.model.add_min_equality(self.night_min, self.night_counts)

    def _employee_shifts(self, e_index: int) -> Any:
        return self._sum(work for (e, _, _), work in self.work.items() if e == e_index)

    def add_symmetry_breaking(self) -> None:
        for earlier, later in symmetry_pairs(self.employees):
            self.model.add(self._employee_shifts(earlier) >= self._employee_shifts(later))

    def add_start_caps(self, caps: dict[tuple[int, str], int]) -> None:
        for (day, name), cap in caps.items():
            if name not in self.shift_index:
                continue
            s_index = self.shift_index[name]
            starts = [
                self.work[(e_index, day, s_index)]
                for e_index in range(len(self.employees))
                if (e_index, day, s_index) in self.work
            ]
            if starts:
                self.model.add(self._sum(starts) <= cap)

    def _cost(self) -> Any:
        return self._sum(
            self.employees[e].hourly_wage
            * self.shifts[s_index].cost_per_wage_unit(self.rules)
            * work
            for (e, _, s_index), work in self.work.items()
        )

    def _preference_misses(self) -> Any:
        return self._sum(
            work
            for (e, day, _), work in self.work.items()
            if day in self.employees[e].preferred_days_off
        )

    def _stages(self) -> list[tuple[str, Any]]:
        stages: list[tuple[str, Any]] = [
            ("shortfall", self._sum(self.shortfall)),
            ("cost", self._cost()),
        ]
        if self.night_max is not None:
            stages.append(("night_spread", self.night_max - self.night_min))
        if any(employee.preferred_days_off for employee in self.employees):
            stages.append(("preference", self._preference_misses()))
        return stages

    def solve(self, params: SolveParams) -> RosterOutcome:
        stages = self._stages()
        stage_params = with_time_share(params, len(stages))
        results: list[SolveResult] = []
        best = None
        hints: dict[Any, int] = {}
        for _, expression in stages:
            self.model.proto.clear_solution_hint()
            for variable, value in hints.items():
                self.model.add_hint(variable, value)
            self.model.minimize(expression)
            solver, result = run_cp_model(self.model, stage_params)
            results.append(result)
            if result.objective is None:
                break
            best = solver
            self.model.add(expression <= round(result.objective))
            hints = {variable: solver.value(variable) for variable in self.all_vars}
        return self._outcome(best, tuple(results), len(stages))

    def _outcome(
        self, best: Any, results: tuple[SolveResult, ...], stage_count: int
    ) -> RosterOutcome:
        combined = _combine(results, stage_count)
        if best is None:
            return RosterOutcome(Solution(()), combined, results, None, None, None)
        return RosterOutcome(
            solution=self._solution(best),
            result=combined,
            phases=results,
            understaffed_hours=round(sum(best.value(short) for short in self.shortfall)),
            night_spread=(
                best.value(self.night_max) - best.value(self.night_min)
                if self.night_max is not None
                else None
            ),
            preference_misses=round(best.value(self._preference_misses())),
        )

    def _solution(self, best: Any) -> Solution:
        assignments: list[Assignment] = []
        for (e_index, day, s_index), work in sorted(self.work.items()):
            if not best.value(work):
                continue
            shift = self.shifts[s_index]
            offset = next(
                (
                    offset
                    for offset in shift.break_window(self.rules)
                    if best.value(self.breaks[(e_index, day, s_index, offset)])
                ),
                None,
            )
            assignments.append(Assignment(self.employees[e_index].id, day, shift.name, offset))
        return Solution(tuple(assignments))


def _combine(results: tuple[SolveResult, ...], stage_count: int) -> SolveResult:
    last = next((result for result in reversed(results) if result.objective is not None), None)
    if last is None:
        status = SolveStatus.UNKNOWN
    elif len(results) == stage_count and all(
        result.status is SolveStatus.OPTIMAL for result in results
    ):
        status = SolveStatus.OPTIMAL
    else:
        status = SolveStatus.FEASIBLE
    return SolveResult(
        status=status,
        objective=last.objective if last else None,
        bound=last.bound if last else None,
        gap=last.gap if last else None,
        wall_time_seconds=sum(result.wall_time_seconds for result in results),
        solver=SOLVER_NAME,
        solver_version=results[0].solver_version,
        log="\n".join(result.log for result in results),
    )
