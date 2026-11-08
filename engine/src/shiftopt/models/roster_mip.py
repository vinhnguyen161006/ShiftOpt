from typing import Any

import pulp

from shiftopt.constraints.sequences import consecutive_day_windows, forbidden_shift_pairs
from shiftopt.domain import Assignment, Employee, Instance, RepairSpec, ShiftType, Solution
from shiftopt.models.roster_cpsat import RosterOutcome
from shiftopt.solvers.base import (
    SolveParams,
    SolveResult,
    combine_tiers,
    with_time_share,
)
from shiftopt.solvers.pulp_backend import run_problem
from shiftopt.time_grid import DAYS_PER_WEEK, HOURS_PER_WEEK, hour_of_week, shift_hours

TIER_TOLERANCE = 1e-6


def solve_roster_mip(
    instance: Instance,
    params: SolveParams,
    *,
    repair: RepairSpec | None = None,
    relax: bool = False,
) -> RosterOutcome:
    """Per-employee roster as an integer linear program, solved by HiGHS through PuLP.

    Same constraints and lexicographic tiers as solve_roster (see docs/model.md section 2a, rows
    C1 to C8): shortfall, changes (repair only), labour cost with the night premium, night-shift
    spread, then preference misses. Each tier is capped at the optimum of the tier before. Breaks
    use one binary per break offset, so a break removes its worker from coverage at one hour.
    relax=True keeps the same rows and makes every variable continuous; it is used only to measure
    the integrality gap, never to produce a roster.

    Unlike the CP-SAT model there are no solution hints between tiers, and symmetry breaking and
    decomposition are not offered. Status is OPTIMAL only when every tier is proven optimal by
    HiGHS.
    """
    model = _RosterMip(instance, repair, relax)
    return model.solve(params)


def roster_model_size(instance: Instance) -> tuple[int, int]:
    """Number of PuLP variables and constraints of the per-employee ILP, built but not solved."""
    model = _RosterMip(instance, None, relax=False)
    return len(model.problem.variables()), model.rows


class _RosterMip:
    def __init__(self, instance: Instance, repair: RepairSpec | None, relax: bool) -> None:
        self.instance = instance
        self.rules = instance.rules
        self.employees: tuple[Employee, ...] = instance.employees
        self.relax = relax
        self.repair = repair
        self.shifts: tuple[ShiftType, ...] = tuple(
            shift for shift in instance.shift_types if shift.length <= self.rules.max_daily_hours
        )
        self.shift_index = {shift.name: index for index, shift in enumerate(self.shifts)}
        self.employee_index = {employee.id: index for index, employee in enumerate(self.employees)}
        self.problem = pulp.LpProblem("roster_mip", pulp.LpMinimize)
        self.rows = 0
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
        self.baseline_keys: dict[tuple[int, int, int], int | None] = {}
        self.changes: Any = None
        self._build()

    def _var(self, name: str, *, upper: float | None = None) -> Any:
        if self.relax:
            return self.problem.add_variable(name, lowBound=0, upBound=upper, cat=pulp.LpContinuous)
        return self.problem.add_variable(name, lowBound=0, upBound=upper, cat=pulp.LpInteger)

    def _binary(self, name: str) -> Any:
        if self.relax:
            return self.problem.add_variable(name, lowBound=0, upBound=1, cat=pulp.LpContinuous)
        return self.problem.add_variable(name, lowBound=0, upBound=1, cat=pulp.LpBinary)

    def _row(self, expression: Any, name: str) -> None:
        self.rows += 1
        self.problem += expression, f"{name}_{self.rows}"

    def _build(self) -> None:
        self._create_shift_variables()
        self._add_one_shift_per_day()
        self._add_weekly_hours()
        self._add_rest_between_shifts()
        self._add_consecutive_days()
        self._add_weekly_rest()
        self._add_breaks_and_coverage()
        self._add_night_spread()
        if self.repair is not None:
            self._add_repair(self.repair)

    def _create_shift_variables(self) -> None:
        for e_index, employee in enumerate(self.employees):
            for day in range(DAYS_PER_WEEK):
                if day in employee.unavailable_days:
                    continue
                for s_index, shift in enumerate(self.shifts):
                    key = (e_index, day, s_index)
                    work = self._binary(f"work_{e_index}_{day}_{s_index}")
                    self.work[key] = work
                    for hour in shift_hours(day, shift.start_hour, shift.length):
                        self.hour_work[e_index][hour].append(work)
                    for offset in shift.break_window(self.rules):
                        broken = self._binary(f"break_{e_index}_{day}_{s_index}_{offset}")
                        self.breaks[(*key, offset)] = broken
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
                    self._row(pulp.lpSum(day_shifts) <= 1, "one_shift")

    def _add_weekly_hours(self) -> None:
        for e_index, employee in enumerate(self.employees):
            terms = [
                self.shifts[s_index].length * work
                for (e, _, s_index), work in self.work.items()
                if e == e_index
            ]
            if terms:
                self._row(pulp.lpSum(terms) <= employee.weekly_cap(self.rules), "weekly_hours")

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
                            self._row(prev + nxt <= 1, "rest_110")

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
                    self._row(pulp.lpSum(terms) <= self.rules.max_consecutive_days, "consecutive")

    def _add_weekly_rest(self) -> None:
        for e_index in range(len(self.employees)):
            rest_starts = []
            for start in range(HOURS_PER_WEEK):
                rest_start = self._binary(f"rest_{e_index}_{start}")
                rest_starts.append(rest_start)
                blocked: list[Any] = []
                for offset in range(self.rules.weekly_rest_hours):
                    for work in self.hour_work[e_index][(start + offset) % HOURS_PER_WEEK]:
                        if not any(work is seen for seen in blocked):
                            blocked.append(work)
                for work in blocked:
                    self._row(work + rest_start <= 1, "rest_111")
            self._row(pulp.lpSum(rest_starts) >= 1, "rest_111_once")

    def _add_breaks_and_coverage(self) -> None:
        for (e_index, day, s_index), work in self.work.items():
            window = self.shifts[s_index].break_window(self.rules)
            if window:
                breaks = [self.breaks[(e_index, day, s_index, offset)] for offset in window]
                self._row(pulp.lpSum(breaks) == work, "break_109")
        for hour in range(HOURS_PER_WEEK):
            present = pulp.lpSum(
                work for employee_hours in self.hour_work for work in employee_hours[hour]
            )
            on_break = pulp.lpSum(self.break_at[hour])
            shortfall = self._var(f"short_{hour}", upper=self.instance.demand[hour])
            self.shortfall.append(shortfall)
            self._row(present - on_break + shortfall >= self.instance.demand[hour], "cover")

    def _employee_nights(self, e_index: int) -> Any:
        return pulp.lpSum(
            work
            for (e, _, s_index), work in self.work.items()
            if e == e_index and self.shifts[s_index].is_night_shift(self.rules)
        )

    def _add_night_spread(self) -> None:
        if len(self.employees) < 2:
            return
        bound = len(self.work) + 1
        self.night_max = self._var("night_max", upper=bound)
        self.night_min = self._var("night_min", upper=bound)
        for e_index in range(len(self.employees)):
            nights = self._employee_nights(e_index)
            self._row(self.night_max >= nights, "night_max")
            self._row(self.night_min <= nights, "night_min")

    def _cost(self) -> Any:
        return pulp.lpSum(
            self.employees[e].hourly_wage
            * self.shifts[s_index].cost_per_wage_unit(self.rules)
            * work
            for (e, _, s_index), work in self.work.items()
        )

    def _preference_misses(self) -> Any:
        return pulp.lpSum(
            work
            for (e, day, _), work in self.work.items()
            if day in self.employees[e].preferred_days_off
        )

    def _add_repair(self, spec: RepairSpec) -> None:
        self.baseline_keys = self._keys_of(spec.baseline.assignments)
        locked = self._keys_of(spec.locked())
        for key in locked:
            if key not in self.work:
                raise ValueError("locked shift falls on a day the employee cannot work")
        for key, work in self.work.items():
            if key[1] < spec.from_day or key in locked:
                self._row(work == (1 if key in locked else 0), "repair_fix")
        for key, offset in locked.items():
            window = self.shifts[key[2]].break_window(self.rules)
            if offset in window:
                for candidate in window:
                    value = 1 if candidate == offset else 0
                    self._row(self.breaks[(*key, candidate)] == value, "repair_break")
        unmatched = sum(1 for key in self.baseline_keys if key not in self.work)
        terms = [1 - work if key in self.baseline_keys else work for key, work in self.work.items()]
        self.changes = pulp.lpSum(terms) + unmatched

    def _keys_of(
        self, assignments: tuple[Assignment, ...]
    ) -> dict[tuple[int, int, int], int | None]:
        keys: dict[tuple[int, int, int], int | None] = {}
        for item in assignments:
            if (
                item.employee_id not in self.employee_index
                or item.shift_name not in self.shift_index
            ):
                raise ValueError(
                    f"repair refers to unknown employee or shift: {item.employee_id} "
                    f"{item.shift_name}"
                )
            key = (
                self.employee_index[item.employee_id],
                item.day,
                self.shift_index[item.shift_name],
            )
            keys[key] = item.break_offset
        return keys

    def _stages(self) -> list[tuple[str, Any]]:
        stages: list[tuple[str, Any]] = [("shortfall", pulp.lpSum(self.shortfall))]
        if self.changes is not None:
            stages.append(("changes", self.changes))
        stages.append(("cost", self._cost()))
        if self.night_max is not None:
            stages.append(("night_spread", self.night_max - self.night_min))
        if any(employee.preferred_days_off for employee in self.employees):
            stages.append(("preference", self._preference_misses()))
        return stages

    def solve(self, params: SolveParams) -> RosterOutcome:
        stages = self._stages()
        stage_params = with_time_share(params, len(stages))
        results: list[SolveResult] = []
        snapshot: dict[str, float] | None = None
        for name, expression in stages:
            self.problem.setObjective(expression)
            result = run_problem(self.problem, stage_params, mip=not self.relax)
            results.append(result)
            if result.objective is None:
                break
            snapshot = self._values()
            self._row(expression <= result.objective + TIER_TOLERANCE, f"tier_{name}")
        return self._outcome(snapshot, tuple(results), len(stages))

    def _values(self) -> dict[str, float]:
        values: dict[str, float] = {}
        for variable in self.problem.variables():
            values[variable.name] = variable.value() or 0.0
        return values

    def _outcome(
        self, values: dict[str, float] | None, results: tuple[SolveResult, ...], stage_count: int
    ) -> RosterOutcome:
        combined = combine_tiers(results, stage_count)
        if values is None:
            return RosterOutcome(Solution(()), combined, results, None, None, None)
        taken = self._taken(values)
        return RosterOutcome(
            solution=self._solution(values),
            result=combined,
            phases=results,
            understaffed_hours=round(sum(values.get(short.name, 0.0) for short in self.shortfall)),
            night_spread=(
                round(values.get(self.night_max.name, 0.0) - values.get(self.night_min.name, 0.0))
                if self.night_max is not None
                else None
            ),
            preference_misses=sum(
                1 for e, day, _ in taken if day in self.employees[e].preferred_days_off
            ),
            changes=self._changes_from(taken) if self.repair is not None else None,
        )

    def _taken(self, values: dict[str, float]) -> list[tuple[int, int, int]]:
        return [key for key, work in sorted(self.work.items()) if values.get(work.name, 0.0) > 0.5]

    def _changes_from(self, taken_keys: list[tuple[int, int, int]]) -> int:
        taken = set(taken_keys)
        unmatched = sum(1 for key in self.baseline_keys if key not in self.work)
        return (
            sum(1 for key in self.baseline_keys if key in self.work and key not in taken)
            + sum(1 for key in taken if key not in self.baseline_keys)
            + unmatched
        )

    def _solution(self, values: dict[str, float]) -> Solution:
        assignments: list[Assignment] = []
        for (e_index, day, s_index), work in sorted(self.work.items()):
            if values.get(work.name, 0.0) <= 0.5:
                continue
            shift = self.shifts[s_index]
            offset = next(
                (
                    offset
                    for offset in shift.break_window(self.rules)
                    if values.get(self.breaks[(e_index, day, s_index, offset)].name, 0.0) > 0.5
                ),
                None,
            )
            assignments.append(Assignment(self.employees[e_index].id, day, shift.name, offset))
        return Solution(tuple(assignments))
