import pytest

from src.demand.csv_import import BYTE_ORDER_MARK
from src.employees.csv_import import parse_employees_csv


def test_reads_required_and_optional_columns() -> None:
    text = (
        "code,name,hourly_wage,max_weekly_hours,unavailable_days,preferred_days_off\n"
        "E01,Ada,100,40,T7 CN,0\n"
        "E02,Grace,120,,,\n"
    )
    first, second = parse_employees_csv(text)
    assert (first.code, first.hourly_wage, first.max_weekly_hours) == ("E01", 100, 40)
    assert first.unavailable_days == [5, 6]
    assert first.preferred_days_off == [0]
    assert second.max_weekly_hours is None
    assert second.unavailable_days == []


def test_accepts_semicolons_bom_blank_lines_and_header_case() -> None:
    text = BYTE_ORDER_MARK + "Code;Name;Hourly_Wage;unavailable_days\n\nE01;Ada;100;1|2\n"
    (employee,) = parse_employees_csv(text)
    assert employee.unavailable_days == [1, 2]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "no rows"),
        ("code,name\nE01,Ada\n", "missing columns: hourly_wage"),
        ("code,name,hourly_wage,team\nE01,Ada,100,A\n", "unknown columns: team"),
        ("code,name,hourly_wage\n", "no employees"),
        ("code,name,hourly_wage\nE01,Ada,abc\n", "row 2, hourly_wage"),
        ("code,name,hourly_wage\nE01,Ada,100,9\n", "row 2: more cells"),
        ("code,name,hourly_wage,unavailable_days\nE01,Ada,100,T9\n", "'T9' is not a day"),
        ("code,name,hourly_wage,max_weekly_hours\nE01,Ada,100,60\n", "row 2, max_weekly_hours"),
        ("code,name,hourly_wage\nE01,Ada,100\nE01,Bob,100\n", "row 3: code E01 repeats row 2"),
    ],
)
def test_rejects_bad_files_with_the_row(text: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_employees_csv(text)
