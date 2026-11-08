from shiftopt.domain import Assignment, Solution
from shiftopt.schedule_diff import diff_solutions


def test_identical_rosters_have_no_changes() -> None:
    roster = Solution((Assignment("e0", 0, "day"), Assignment("e1", 3, "night")))

    diff = diff_solutions(roster, roster)

    assert len(diff.kept) == 2
    assert diff.added == ()
    assert diff.removed == ()


def test_swapped_person_is_one_removed_and_one_added() -> None:
    before = Solution((Assignment("e0", 2, "day"),))
    after = Solution((Assignment("e1", 2, "day"),))

    diff = diff_solutions(before, after)

    assert diff.kept == ()
    assert [a.employee_id for a in diff.added] == ["e1"]
    assert [a.employee_id for a in diff.removed] == ["e0"]


def test_break_offset_move_is_not_a_change() -> None:
    before = Solution((Assignment("e0", 0, "day", break_offset=2),))
    after = Solution((Assignment("e0", 0, "day", break_offset=4),))

    diff = diff_solutions(before, after)

    assert len(diff.kept) == 1
    assert diff.added == ()
    assert diff.removed == ()


def test_duplicate_keys_are_matched_as_multisets() -> None:
    before = Solution((Assignment("e0", 1, "day"), Assignment("e0", 1, "day")))
    after = Solution((Assignment("e0", 1, "day"),))

    diff = diff_solutions(before, after)

    assert len(diff.kept) == 1
    assert diff.added == ()
    assert len(diff.removed) == 1
