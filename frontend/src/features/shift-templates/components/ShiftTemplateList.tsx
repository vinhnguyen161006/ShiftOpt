import { Button } from "../../../components/ui/Button";
import { Table } from "../../../components/ui/Table";
import { shiftSpan } from "../../../lib/time";
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
      caption="Shift templates"
      rows={templates}
      rowKey={(template) => template.id}
      columns={[
        { key: "name", label: "Name", render: (template) => template.name },
        {
          key: "hours",
          label: "Hours",
          render: (template) => shiftSpan(template.start_hour, template.length_hours),
        },
        {
          key: "day",
          label: "Over the day",
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
          label: "Length",
          align: "end",
          render: (template) => `${template.length_hours} h`,
        },
        {
          key: "night",
          label: "Night hours",
          align: "end",
          render: (template) => `${template.night_hours} h`,
        },
        {
          key: "break",
          label: "Rest break",
          render: (template) => (template.break_required ? "Required" : "Not required"),
        },
        {
          key: "actions",
          label: "Actions",
          render: (template) => (
            <span className="tag-row">
              <Button size="sm" onClick={() => onEdit(template)}>
                Edit<span className="visually-hidden"> {template.name}</span>
              </Button>
              <Button size="sm" onClick={() => onDelete(template)}>
                Delete<span className="visually-hidden"> {template.name}</span>
              </Button>
            </span>
          ),
        },
      ]}
    />
  );
}
