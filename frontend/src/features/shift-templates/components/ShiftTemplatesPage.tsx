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
      Add shift template
    </Button>
  );

  return (
    <div className="page">
      <PageHeader
        eyebrow="Workforce"
        title="Shift templates"
        lead="The shift types the optimizer may assign. A shift that crosses midnight counts its hours on the next day. Night hours fall between 22:00 and 06:00 and carry the night allowance."
        actions={addButton}
      />
      {(templates.isPending || rules.isPending) && <Loading label="Loading shift templates" />}
      {templates.isError && (
        <Notice kind="error" title="Could not load shift templates">
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
              Working hour
            </span>
            <span className="legend-item">
              <span className="swatch shift-strip-hour is-worked is-night" />
              Night hour (allowance applies)
            </span>
            <span className="legend-item">
              <span className="swatch shift-strip-hour is-night" />
              Night window, not worked
            </span>
          </div>
        </>
      )}
      {templates.data?.length === 0 && (
        <EmptyState title="Define the shifts you can staff" action={addButton}>
          Add each shift type once, for example 06:00-14:00, 14:00-22:00 and 22:00-06:00. The
          optimizer picks how many people work each shift on each day.
        </EmptyState>
      )}
      <Modal
        title={editing?.template ? `Edit ${editing.template.name}` : "Add shift template"}
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
        title="Delete shift template?"
        open={deleting !== undefined}
        onClose={() => setDeleting(undefined)}
      >
        <p>
          {deleting?.name} will be removed. Schedules already solved keep their own copy of this
          shift type.
        </p>
        {remove.isError && <Notice kind="error" title={errorMessage(remove.error)} />}
        <div className="form-actions">
          <Button onClick={() => setDeleting(undefined)}>Cancel</Button>
          <Button
            variant="primary"
            disabled={remove.isPending}
            onClick={() =>
              deleting && remove.mutate(deleting.id, { onSuccess: () => setDeleting(undefined) })
            }
          >
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  );
}
