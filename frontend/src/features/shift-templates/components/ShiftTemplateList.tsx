import { Button } from "../../../components/ui/Button";
import { Table } from "../../../components/ui/Table";
import { shiftSpan } from "../../../lib/time";
import { vi } from "../../../locales/vi";
import type { LaborRulesRead, ShiftTemplateRead } from "../../../types/models";
import { ShiftStrip } from "./ShiftStrip";

type ShiftTemplateListProps = {
  templates: ShiftTemplateRead[];
  rules: LaborRulesRead | undefined;
  onEdit: (template: ShiftTemplateRead) => void;
  onDelete: (template: ShiftTemplateRead) => void;
};

export function ShiftTemplateList({ templates, rules, onEdit, onDelete }: ShiftTemplateListProps) {
  return (
    <Table
      caption={vi.shifts.table.caption}
      rows={templates}
      rowKey={(template) => template.id}
      columns={[
        { key: "name", label: vi.shifts.table.name, render: (template) => template.name },
        {
          key: "hours",
          label: vi.shifts.table.hours,
          render: (template) => shiftSpan(template.start_hour, template.length_hours),
        },
        {
          key: "day",
          label: vi.shifts.table.overDay,
          render: (template) =>
            rules && (
              <ShiftStrip
                startHour={template.start_hour}
                length={template.length_hours}
                nightStart={rules.night_start}
                nightEnd={rules.night_end}
              />
            ),
        },
        {
          key: "length",
          label: vi.shifts.table.length,
          align: "end",
          render: (template) => vi.home.sample.hours(template.length_hours),
        },
        {
          key: "night",
          label: vi.shifts.table.night,
          align: "end",
          render: (template) => vi.home.sample.hours(template.night_hours),
        },
        {
          key: "break",
          label: vi.shifts.table.break,
          render: (template) =>
            template.break_required ? vi.shifts.table.required : vi.shifts.table.notRequired,
        },
        {
          key: "actions",
          label: vi.common.actions,
          render: (template) => (
            <span className="tag-row">
              <Button size="sm" onClick={() => onEdit(template)}>
                {vi.common.edit}
                <span className="visually-hidden"> {template.name}</span>
              </Button>
              <Button size="sm" onClick={() => onDelete(template)}>
                {vi.common.delete}
                <span className="visually-hidden"> {template.name}</span>
              </Button>
            </span>
          ),
        },
      ]}
    />
  );
}
