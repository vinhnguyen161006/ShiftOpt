import type { ShiftTemplateRead } from "../../../types/models";

type ShiftTemplateListProps = {
  templates: ShiftTemplateRead[];
  onDelete: (templateId: number) => void;
};

export function ShiftTemplateList({ templates, onDelete }: ShiftTemplateListProps) {
  return (
    <p className="todo">
      TODO: list of templates with start hour, end hour (next day when overnight) and length.
      Templates: {templates.length}.
    </p>
  );
}
