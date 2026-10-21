import type { ReactNode } from "react";

export type Column<T> = {
  key: string;
  label: string;
  render: (row: T) => ReactNode;
};

type TableProps<T> = {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
};

export function Table<T>({ columns, rows, rowKey }: TableProps<T>) {
  return (
    <p className="todo">
      TODO: data table with {columns.length} columns and {rows.length} rows, sticky header.
    </p>
  );
}
