import re

from shiftopt.time_grid import DAYS_PER_WEEK, HOURS_PER_DAY, HOURS_PER_WEEK

DELIMITERS = (",", ";", "\t")
WHOLE_NUMBER = re.compile(r"[+-]?[0-9]+")
BYTE_ORDER_MARK = "\ufeff"


def parse_demand_csv(text: str) -> list[int]:
    """Read a demand grid from CSV text and return 168 head counts, Monday 00:00 first. Accepts
    7 rows of 24 hourly cells (one row per weekday) or one column of 168 cells. Blank lines, a
    byte order mark, a header row, a trailing delimiter and comma, semicolon or tab separators
    are tolerated. Raise ValueError with the row and column of the first bad cell."""
    rows = _split_rows(text.removeprefix(BYTE_ORDER_MARK))
    if rows and (_is_header(rows[0]) or _is_hour_labels(rows[0], rows)):
        rows = rows[1:]
    if not rows:
        raise ValueError("CSV has no demand values")
    grid_shape = len(rows) == DAYS_PER_WEEK and all(len(row) == HOURS_PER_DAY for row in rows)
    column_shape = len(rows) == HOURS_PER_WEEK and all(len(row) == 1 for row in rows)
    if not (grid_shape or column_shape):
        raise ValueError(
            f"expected {DAYS_PER_WEEK} rows of {HOURS_PER_DAY} hours or one column of "
            f"{HOURS_PER_WEEK} values"
        )
    return [
        _parse_count(cell, row_number, column_number)
        for row_number, row in enumerate(rows, start=1)
        for column_number, cell in enumerate(row, start=1)
    ]


def _split_rows(text: str) -> list[list[str]]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    delimiter = max(DELIMITERS, key=lambda candidate: sum(line.count(candidate) for line in lines))
    rows: list[list[str]] = []
    for line in lines:
        cells = [cell.strip() for cell in line.split(delimiter)]
        while cells and cells[-1] == "":
            cells.pop()
        rows.append(cells)
    return rows


def _is_header(row: list[str]) -> bool:
    return any(not _is_number(cell) for cell in row if cell)


def _is_hour_labels(row: list[str], rows: list[list[str]]) -> bool:
    return len(rows) == DAYS_PER_WEEK + 1 and row == [str(hour) for hour in range(HOURS_PER_DAY)]


def _is_number(cell: str) -> bool:
    try:
        float(cell)
    except ValueError:
        return False
    return True


def _parse_count(cell: str, row_number: int, column_number: int) -> int:
    if not WHOLE_NUMBER.fullmatch(cell):
        raise ValueError(
            f"row {row_number}, column {column_number}: '{cell}' is not a whole number"
        )
    value = int(cell)
    if value < 0:
        raise ValueError(f"row {row_number}, column {column_number}: demand must be non-negative")
    return value
