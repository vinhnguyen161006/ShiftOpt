from collections import Counter
from dataclasses import dataclass

from shiftopt.domain import Assignment, Solution


@dataclass(frozen=True)
class ScheduleDiff:
    kept: tuple[Assignment, ...]
    added: tuple[Assignment, ...]
    removed: tuple[Assignment, ...]


def diff_solutions(previous: Solution, current: Solution) -> ScheduleDiff:
    """Compare two rosters as multisets of (employee, day, shift). Break offsets are ignored:
    moving a rest break does not change who works when."""
    before = Counter(_key(a) for a in previous.assignments)
    after = Counter(_key(a) for a in current.assignments)
    keep_budget = before & after
    kept: list[Assignment] = []
    added: list[Assignment] = []
    for assignment in current.assignments:
        if keep_budget[_key(assignment)] > 0:
            keep_budget[_key(assignment)] -= 1
            kept.append(assignment)
        else:
            added.append(assignment)
    drop_budget = before - after
    removed: list[Assignment] = []
    for assignment in previous.assignments:
        if drop_budget[_key(assignment)] > 0:
            drop_budget[_key(assignment)] -= 1
            removed.append(assignment)
    return ScheduleDiff(tuple(kept), tuple(added), tuple(removed))


def _key(assignment: Assignment) -> tuple[str, int, str]:
    return (assignment.employee_id, assignment.day, assignment.shift_name)
