import csv
from pathlib import Path

from scripts.run_experiments import COLUMNS, employee_count, summary, write_csv


def test_employee_count_has_a_floor_and_a_slack() -> None:
    assert employee_count(0) == 8
    assert employee_count(468) == 15


def test_write_csv_uses_the_fixed_header(tmp_path: Path) -> None:
    path = tmp_path / "out.csv"
    write_csv([{"store": 18, "scenario": "base", "method": "cpsat"}], path)
    with path.open(encoding="utf-8") as handle:
        assert next(csv.reader(handle)) == list(COLUMNS)


def _row(method: str, cost: str, understaffed: str) -> dict[str, str]:
    values = dict.fromkeys(COLUMNS, "")
    values.update(
        store="18",
        scenario="base",
        method=method,
        status="feasible",
        tiers="optimal/optimal/feasible",
        labor_cost=cost,
        understaffed=understaffed,
    )
    return values


def _summary_of(tmp_path: Path, rows: list[dict[str, str]]) -> list[str]:
    path = tmp_path / "rows.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return summary(path).splitlines()


def test_cost_gap_is_shown_only_when_coverage_is_equal(tmp_path: Path) -> None:
    lines = _summary_of(
        tmp_path,
        [_row("cpsat", "100", "5"), _row("greedy", "80", "5")],
    )
    assert "-20.0%" in lines[-1]


def test_cost_gap_is_hidden_when_coverage_differs(tmp_path: Path) -> None:
    lines = _summary_of(
        tmp_path,
        [_row("cpsat", "100", "5"), _row("greedy", "80", "9")],
    )
    assert "%" not in lines[-1]
    assert "optimal/optimal/feasible" in lines[-1]
