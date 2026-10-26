import pytest
from shiftopt.time_grid import HOURS_PER_WEEK

from src.demand.csv_import import parse_demand_csv

EXPECTED = list(range(HOURS_PER_WEEK))
BYTE_ORDER_MARK = chr(0xFEFF)


def _grid_text(separator: str) -> str:
    return "\n".join(separator.join(str(day * 24 + hour) for hour in range(24)) for day in range(7))


def _with_cell(text: str, row: int, column: int, value: str) -> str:
    lines = text.splitlines()
    cells = lines[row].split(",")
    cells[column] = value
    lines[row] = ",".join(cells)
    return "\n".join(lines)


def _column_text() -> str:
    return "\n".join(str(index) for index in range(HOURS_PER_WEEK))


@pytest.mark.parametrize("separator", [",", ";", "\t"])
def test_grid_with_each_separator(separator: str) -> None:
    assert parse_demand_csv(_grid_text(separator)) == EXPECTED


def test_single_column_of_168_values() -> None:
    assert parse_demand_csv(_column_text()) == EXPECTED


def test_byte_order_mark_blank_lines_and_header_are_ignored() -> None:
    text = BYTE_ORDER_MARK + "mon,tue\n\n" + "\n\n".join(_grid_text(",").splitlines()) + "\n\n"
    assert parse_demand_csv(text) == EXPECTED


def test_hour_label_header_is_ignored() -> None:
    labels = ",".join(str(hour) for hour in range(24))
    assert parse_demand_csv(labels + "\n" + _grid_text(",")) == EXPECTED


def test_single_cell_header_with_semicolon_grid() -> None:
    assert parse_demand_csv("demand\n" + _grid_text(";")) == EXPECTED


def test_trailing_delimiter_is_ignored() -> None:
    lines = [line + "," for line in _grid_text(",").splitlines()]
    assert parse_demand_csv("\n".join(lines)) == EXPECTED


def test_windows_line_endings() -> None:
    assert parse_demand_csv(_grid_text(",").replace("\n", "\r\n")) == EXPECTED


@pytest.mark.parametrize("cells", [167, 169])
def test_wrong_cell_count_is_rejected(cells: int) -> None:
    text = "\n".join(str(index) for index in range(cells))
    with pytest.raises(ValueError, match="expected 7 rows"):
        parse_demand_csv(text)


def test_transposed_24_by_7_is_rejected() -> None:
    text = "\n".join(",".join("1" for _ in range(7)) for _ in range(24))
    with pytest.raises(ValueError, match="expected 7 rows"):
        parse_demand_csv(text)


def test_negative_cell_reports_position() -> None:
    text = _with_cell(_grid_text(","), 2, 0, "-1")
    with pytest.raises(ValueError, match="row 3, column 1: demand must be non-negative"):
        parse_demand_csv(text)


def test_fractional_cell_is_rejected() -> None:
    text = _with_cell(_grid_text(","), 1, 0, "1.5")
    with pytest.raises(ValueError, match=r"row 2, column 1: '1\.5' is not a whole number"):
        parse_demand_csv(text)


def test_text_cell_in_data_row_is_rejected() -> None:
    text = _with_cell(_grid_text(","), 4, 0, "abc")
    with pytest.raises(ValueError, match="row 5, column 1: 'abc' is not a whole number"):
        parse_demand_csv(text)


def test_empty_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="no demand values"):
        parse_demand_csv("\n\n")
