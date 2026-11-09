import csv
import re

from pydantic import ValidationError
from shiftopt.time_grid import DAYS_PER_WEEK

from src.demand.csv_import import BYTE_ORDER_MARK
from src.employees.schemas import EmployeeCreate

DELIMITERS = (",", ";", "\t")
REQUIRED_COLUMNS = ("code", "name", "hourly_wage")
OPTIONAL_COLUMNS = (
    "max_weekly_hours",
    "min_weekly_hours",
    "unavailable_days",
    "preferred_days_off",
)
DAY_COLUMNS = frozenset({"unavailable_days", "preferred_days_off"})
DAY_LABELS = ("T2", "T3", "T4", "T5", "T6", "T7", "CN")
DAY_SEPARATOR = re.compile(r"[\s|]+")
FIRST_DATA_ROW = 2


def parse_employees_csv(text: str) -> list[EmployeeCreate]:
    """Read employees from CSV text with a header row naming the API fields. code, name and
    hourly_wage are required; max_weekly_hours, min_weekly_hours, unavailable_days and
    preferred_days_off may be missing or blank. A day list holds 0-6 (0 is Monday) or T2..T7, CN,
    separated by spaces or |. Comma, semicolon or tab separators and a byte order mark are
    accepted. Raise ValueError naming the first bad row, counting the header as row 1 and
    skipping blank lines."""
    lines = [line for line in text.removeprefix(BYTE_ORDER_MARK).splitlines() if line.strip()]
    if not lines:
        raise ValueError("CSV has no rows")
    delimiter = max(DELIMITERS, key=lines[0].count)
    reader = csv.DictReader(lines, delimiter=delimiter)
    reader.fieldnames = _columns(list(reader.fieldnames or []))
    employees: list[EmployeeCreate] = []
    first_row_of: dict[str, int] = {}
    for row_number, row in enumerate(reader, start=FIRST_DATA_ROW):
        employee = _employee(row, row_number)
        if employee.code in first_row_of:
            raise ValueError(
                f"row {row_number}: code {employee.code} repeats row {first_row_of[employee.code]}"
            )
        first_row_of[employee.code] = row_number
        employees.append(employee)
    if not employees:
        raise ValueError("CSV has a header but no employees")
    return employees


def _columns(header: list[str]) -> list[str]:
    columns = [name.strip().lower() for name in header]
    missing = [name for name in REQUIRED_COLUMNS if name not in columns]
    if missing:
        raise ValueError(f"missing columns: {', '.join(missing)}")
    unknown = [name for name in columns if name not in REQUIRED_COLUMNS + OPTIONAL_COLUMNS]
    if unknown:
        raise ValueError(f"unknown columns: {', '.join(unknown)}")
    return columns


def _employee(row: dict[str | None, str | list[str] | None], row_number: int) -> EmployeeCreate:
    if row.get(None):
        raise ValueError(f"row {row_number}: more cells than columns")
    data: dict[str, object] = {}
    for column, cell in row.items():
        value = cell.strip() if isinstance(cell, str) else ""
        if column is None or not value:
            continue
        data[column] = _days(value, row_number, column) if column in DAY_COLUMNS else value
    try:
        return EmployeeCreate.model_validate(data)
    except ValidationError as error:
        first = error.errors()[0]
        field = ".".join(str(part) for part in first["loc"]) or "row"
        raise ValueError(f"row {row_number}, {field}: {first['msg']}") from error


def _days(value: str, row_number: int, column: str) -> list[int]:
    days: list[int] = []
    for token in DAY_SEPARATOR.split(value):
        label = token.upper()
        if label in DAY_LABELS:
            days.append(DAY_LABELS.index(label))
        elif token.isdigit() and int(token) < DAYS_PER_WEEK:
            days.append(int(token))
        else:
            raise ValueError(
                f"row {row_number}, {column}: '{token}' is not a day (0-6 or T2..T7, CN)"
            )
    return days
