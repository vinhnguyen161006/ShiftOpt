import { useState } from "react";
import { Button } from "../../../components/ui/Button";
import { ErrorSummary, Notice } from "../../../components/ui/Feedback";
import { Field } from "../../../components/ui/Field";
import { Panel } from "../../../components/ui/Layout";
import { Modal } from "../../../components/ui/Modal";
import { errorsByPath, generalError, summaryErrors } from "../../../lib/form";
import { vi } from "../../../locales/vi";
import type { DemandProfileRead } from "../../../types/models";
import {
  useCreateDemandProfile,
  useDeleteDemandProfile,
  useUpdateDemandProfile,
} from "../api/demand";
import { cellId, DemandGridEditor } from "./DemandGridEditor";

type DemandProfileViewProps = {
  profile: DemandProfileRead;
  onSelect: (profileId: number | undefined) => void;
};

const SOURCE_LABELS = vi.demand.sources;

const EDITABLE_SOURCES = new Set(["manual", "csv"]);
const PARAMS_PREFIX = "required_staff.";

function invalidCells(errors: Map<string, string>): Set<number> {
  const cells = new Set<number>();
  for (const path of errors.keys()) {
    if (path.startsWith(PARAMS_PREFIX)) {
      cells.add(Number(path.slice(PARAMS_PREFIX.length)));
    }
  }
  return cells;
}

function fieldIdFor(path: string): string | undefined {
  if (path.startsWith(PARAMS_PREFIX)) {
    return cellId(Number(path.slice(PARAMS_PREFIX.length)));
  }
  return path === "name" ? "profile-name" : undefined;
}

function SourceNotice({ profile }: { profile: DemandProfileRead }) {
  if (profile.source === "freshretailnet") {
    return (
      <Notice kind="warning" title={vi.demand.salesTitle}>
        {vi.demand.salesBody}
      </Notice>
    );
  }
  if (profile.source === "call_center") {
    return (
      <Notice kind="info" title={vi.demand.callTitle}>
        {vi.demand.callBody}
      </Notice>
    );
  }
  return null;
}

function Assumptions({ profile }: { profile: DemandProfileRead }) {
  const params = Object.entries(profile.conversion_params);
  const metadata = Object.entries(profile.source_metadata).filter(([key]) => key !== "label");
  if (params.length === 0 && metadata.length === 0) {
    return null;
  }
  return (
    <details className="data-details" open={profile.source !== "manual"}>
      <summary>{vi.demand.assumptions}</summary>
      <dl className="dl">
        {params.map(([key, value]) => (
          <div key={`param-${key}`} className="dl-row">
            <dt>{key}</dt>
            <dd>{value}</dd>
          </div>
        ))}
        {metadata.map(([key, value]) => (
          <div key={`meta-${key}`} className="dl-row">
            <dt>{key}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}

export function DemandProfileView({ profile, onSelect }: DemandProfileViewProps) {
  const update = useUpdateDemandProfile();
  const copy = useCreateDemandProfile();
  const remove = useDeleteDemandProfile();
  const [name, setName] = useState(profile.name);
  const [grid, setGrid] = useState(profile.required_staff);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const editable = EDITABLE_SOURCES.has(profile.source);
  const error = update.error ?? copy.error;
  const errors = errorsByPath(error);
  const general = generalError(error) ?? generalError(remove.error);
  const dirty =
    name !== profile.name || grid.some((count, index) => count !== profile.required_staff[index]);
  const peak = Math.max(0, ...grid);
  const total = grid.reduce((sum, count) => sum + count, 0);

  function save() {
    update.mutate({
      id: profile.id,
      body: { name, source: profile.source, mode: profile.mode, required_staff: grid },
    });
  }

  function copyAsManual() {
    copy.mutate(
      {
        name: `${profile.name}${vi.demand.copySuffix}`.slice(0, 120),
        source: "manual",
        mode: profile.mode,
        required_staff: profile.required_staff,
      },
      { onSuccess: (created) => onSelect(created.id) },
    );
  }

  return (
    <Panel
      title={profile.name}
      labelledBy="profile-title"
      aside={
        <span className="tag-row">
          <span className="tag tag-outline">{SOURCE_LABELS[profile.source] ?? profile.source}</span>
          <span className="tag tag-neutral">
            {profile.mode === "erlang" ? vi.demand.modeErlang : vi.demand.modeLinear}
          </span>
        </span>
      }
    >
      <div className="form-stack">
        <ErrorSummary errors={summaryErrors(error, fieldIdFor)} />
        <SourceNotice profile={profile} />
        <p className="muted profile-stats">
          {vi.demand.stats(total.toLocaleString("vi-VN"), peak)}
        </p>
        {editable && (
          <Field id="profile-name" label={vi.demand.profileName} error={errors.get("name")}>
            {(control) => (
              <input
                {...control}
                className="input"
                value={name}
                maxLength={120}
                onChange={(event) => setName(event.target.value)}
              />
            )}
          </Field>
        )}
        <DemandGridEditor
          caption={vi.demand.gridCaption(profile.name)}
          value={grid}
          onChange={editable ? setGrid : undefined}
          invalidCells={invalidCells(errors)}
        />
        {!editable && <p className="muted">{vi.demand.readOnlyNote}</p>}
        <Assumptions profile={profile} />
        {general && <Notice kind="error" title={general} />}
        {update.isSuccess && !dirty && <Notice kind="success" title={vi.demand.saved} />}
        <div className="form-actions">
          <Button onClick={() => setConfirmDelete(true)}>{vi.demand.deleteProfile}</Button>
          {editable ? (
            <>
              <Button
                disabled={!dirty}
                onClick={() => {
                  setName(profile.name);
                  setGrid(profile.required_staff);
                }}
              >
                {vi.demand.discard}
              </Button>
              <Button variant="primary" disabled={!dirty || update.isPending} onClick={save}>
                {update.isPending ? vi.common.saving : vi.demand.save}
              </Button>
            </>
          ) : (
            <Button variant="primary" disabled={copy.isPending} onClick={copyAsManual}>
              {copy.isPending ? vi.demand.copying : vi.demand.copy}
            </Button>
          )}
        </div>
      </div>
      <Modal
        title={vi.demand.deleteTitle}
        open={confirmDelete}
        onClose={() => setConfirmDelete(false)}
      >
        <p>{vi.demand.deleteBody(profile.name)}</p>
        <div className="form-actions">
          <Button onClick={() => setConfirmDelete(false)}>{vi.common.cancel}</Button>
          <Button
            variant="primary"
            disabled={remove.isPending}
            onClick={() =>
              remove.mutate(profile.id, {
                onSuccess: () => {
                  setConfirmDelete(false);
                  onSelect(undefined);
                },
              })
            }
          >
            {vi.common.delete}
          </Button>
        </div>
      </Modal>
    </Panel>
  );
}
