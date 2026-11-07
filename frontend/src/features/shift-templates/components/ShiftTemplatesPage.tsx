import { useState } from "react";
import { Button } from "../../../components/ui/Button";
import { EmptyState, Loading, Notice } from "../../../components/ui/Feedback";
import { PageHeader } from "../../../components/ui/Layout";
import { Modal } from "../../../components/ui/Modal";
import { errorMessage } from "../../../lib/api-client";
import { useLaborRules } from "../../../lib/labor-rules";
import type { ShiftTemplateRead } from "../../../types/models";
import { useDeleteShiftTemplate, useShiftTemplates } from "../api/shift-templates";
import "../shift-templates.css";
import { vi } from "../../../locales/vi";
import { ShiftTemplateForm } from "./ShiftTemplateForm";
import { ShiftTemplateList } from "./ShiftTemplateList";

type Editing = { template?: ShiftTemplateRead } | undefined;

export function ShiftTemplatesPage() {
  const templates = useShiftTemplates();
  const rules = useLaborRules();
  const remove = useDeleteShiftTemplate();
  const [editing, setEditing] = useState<Editing>(undefined);
  const [deleting, setDeleting] = useState<ShiftTemplateRead | undefined>(undefined);

  const addButton = (
    <Button variant="primary" onClick={() => setEditing({})}>
      {vi.shifts.add}
    </Button>
  );

  return (
    <div className="page">
      <PageHeader
        eyebrow={vi.shifts.eyebrow}
        title={vi.shifts.title}
        lead={vi.shifts.lead}
        actions={addButton}
      />
      {(templates.isPending || rules.isPending) && <Loading label={vi.shifts.loading} />}
      {templates.isError && (
        <Notice kind="error" title={vi.shifts.loadError}>
          {errorMessage(templates.error)}
        </Notice>
      )}
      {templates.data && templates.data.length > 0 && (
        <>
          <ShiftTemplateList
            templates={templates.data}
            rules={rules.data}
            onEdit={(template) => setEditing({ template })}
            onDelete={setDeleting}
          />
          <div className="legend">
            <span className="legend-item">
              <span className="swatch shift-strip-hour is-worked" />
              {vi.shifts.legendWorked}
            </span>
            <span className="legend-item">
              <span className="swatch shift-strip-hour is-worked is-night" />
              {vi.shifts.legendNightWorked}
            </span>
            <span className="legend-item">
              <span className="swatch shift-strip-hour is-night" />
              {vi.shifts.legendNightIdle}
            </span>
          </div>
        </>
      )}
      {templates.data?.length === 0 && (
        <EmptyState title={vi.shifts.emptyTitle} action={addButton}>
          {vi.shifts.emptyBody}
        </EmptyState>
      )}
      <Modal
        title={editing?.template ? vi.shifts.editTitle(editing.template.name) : vi.shifts.add}
        open={editing !== undefined}
        onClose={() => setEditing(undefined)}
      >
        <ShiftTemplateForm
          template={editing?.template}
          rules={rules.data}
          onDone={() => setEditing(undefined)}
        />
      </Modal>
      <Modal
        title={vi.shifts.deleteTitle}
        open={deleting !== undefined}
        onClose={() => setDeleting(undefined)}
      >
        <p>{vi.shifts.deleteBody(deleting?.name ?? "")}</p>
        {remove.isError && <Notice kind="error" title={errorMessage(remove.error)} />}
        <div className="form-actions">
          <Button onClick={() => setDeleting(undefined)}>{vi.common.cancel}</Button>
          <Button
            variant="primary"
            disabled={remove.isPending}
            onClick={() =>
              deleting && remove.mutate(deleting.id, { onSuccess: () => setDeleting(undefined) })
            }
          >
            {vi.common.delete}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
