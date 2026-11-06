import { type FormEvent, type ReactNode, useState } from "react";
import { Button } from "../../../components/ui/Button";
import { ErrorSummary, Notice } from "../../../components/ui/Feedback";
import { Field } from "../../../components/ui/Field";
import { errorsByPath, generalError, summaryErrors, toNumber } from "../../../lib/form";
import { HOURS_PER_WEEK } from "../../../lib/time";
import { vi } from "../../../locales/vi";
import type {
  CallCenterDemandRequest,
  ConversionParams,
  DemandProfileRead,
} from "../../../types/models";
import {
  useCreateDemandProfile,
  useCreateDemandProfileFromCallCenter,
  useCreateDemandProfileFromCsv,
  useCreateDemandProfileFromDataset,
} from "../api/demand";
import { ConversionParamsForm, conversionFieldId } from "./ConversionParamsForm";

type SourceChoice = "manual" | "csv" | "freshretailnet" | "call_center";

const SOURCES: { value: SourceChoice; label: string }[] = (
  ["manual", "csv", "freshretailnet", "call_center"] as const
).map((value) => ({ value, label: vi.demand.form.sources[value] }));

const DEFAULT_CONVERSION: Required<ConversionParams> = {
  alpha: 1,
  productivity: 1,
  min_staff: 1,
  night_min_staff: 1,
};

type CreatedHandler = (profile: DemandProfileRead) => void;

function fieldIdFor(path: string): string | undefined {
  const [head, tail] = path.split(".");
  if (head === "conversion_params" && tail) {
    return conversionFieldId(tail);
  }
  return head ? `new-${head.replaceAll("_", "-")}` : undefined;
}

type FormShellProps = {
  error: unknown;
  pending: boolean;
  submitLabel: string;
  onSubmit: () => void;
  children: ReactNode;
};

function FormShell({ error, pending, submitLabel, onSubmit, children }: FormShellProps) {
  const general = generalError(error);
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit();
  }
  return (
    <form className="form-stack" onSubmit={handleSubmit} noValidate>
      <ErrorSummary errors={summaryErrors(error, fieldIdFor)} />
      {children}
      {general && <Notice kind="error" title={general} />}
      <div className="form-actions">
        <Button type="submit" variant="primary" disabled={pending}>
          {pending ? vi.demand.form.creating : submitLabel}
        </Button>
      </div>
    </form>
  );
}

function NameField({
  value,
  onChange,
  errors,
}: {
  value: string;
  onChange: (value: string) => void;
  errors: Map<string, string>;
}) {
  return (
    <Field id="new-name" label={vi.demand.profileName} error={errors.get("name")}>
      {(control) => (
        <input
          {...control}
          className="input"
          value={value}
          maxLength={120}
          onChange={(event) => onChange(event.target.value)}
        />
      )}
    </Field>
  );
}

function ManualForm({ onCreated }: { onCreated: CreatedHandler }) {
  const create = useCreateDemandProfile();
  const [name, setName] = useState("");
  const [fill, setFill] = useState("0");
  const errors = errorsByPath(create.error);
  return (
    <FormShell
      error={create.error}
      pending={create.isPending}
      submitLabel={vi.demand.form.createProfile}
      onSubmit={() =>
        create.mutate(
          {
            name,
            source: "manual",
            mode: "linear",
            required_staff: new Array<number>(HOURS_PER_WEEK).fill(
              Math.max(0, toNumber(fill) || 0),
            ),
          },
          { onSuccess: onCreated },
        )
      }
    >
      <NameField value={name} onChange={setName} errors={errors} />
      <Field id="new-fill" label={vi.demand.form.fill} hint={vi.demand.form.fillHint}>
        {(control) => (
          <input
            {...control}
            className="input"
            type="number"
            min={0}
            step={1}
            value={fill}
            onChange={(event) => setFill(event.target.value)}
          />
        )}
      </Field>
    </FormShell>
  );
}

function CsvForm({ onCreated }: { onCreated: CreatedHandler }) {
  const create = useCreateDemandProfileFromCsv();
  const [name, setName] = useState("");
  const [text, setText] = useState("");
  const errors = errorsByPath(create.error);
  return (
    <FormShell
      error={create.error}
      pending={create.isPending}
      submitLabel={vi.demand.form.importCsv}
      onSubmit={() => create.mutate({ name, csv_text: text }, { onSuccess: onCreated })}
    >
      <NameField value={name} onChange={setName} errors={errors} />
      <Field id="new-file" label={vi.demand.form.csvFile} hint={vi.demand.form.csvFileHint}>
        {(control) => (
          <input
            {...control}
            className="input"
            type="file"
            accept=".csv,text/csv,text/plain"
            onChange={async (event) => {
              const file = event.target.files?.[0];
              if (file) {
                setText(await file.text());
              }
            }}
          />
        )}
      </Field>
      <Field
        id="new-csv-text"
        label={vi.demand.form.csvContent}
        hint={vi.demand.form.csvContentHint}
        error={errors.get("csv_text")}
      >
        {(control) => (
          <textarea
            {...control}
            className="input"
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
        )}
      </Field>
    </FormShell>
  );
}

function DatasetForm({ onCreated }: { onCreated: CreatedHandler }) {
  const create = useCreateDemandProfileFromDataset();
  const [name, setName] = useState("");
  const [storeId, setStoreId] = useState("");
  const [conversion, setConversion] = useState(DEFAULT_CONVERSION);
  const errors = errorsByPath(create.error);
  return (
    <FormShell
      error={create.error}
      pending={create.isPending}
      submitLabel={vi.demand.form.derive}
      onSubmit={() =>
        create.mutate(
          { name, store_id: toNumber(storeId), conversion_params: conversion },
          { onSuccess: onCreated },
        )
      }
    >
      <Notice kind="warning" title={vi.demand.salesTitle}>
        {vi.demand.form.datasetBody}
      </Notice>
      <NameField value={name} onChange={setName} errors={errors} />
      <Field
        id="new-store-id"
        label={vi.demand.form.storeId}
        hint={vi.demand.form.storeIdHint}
        error={errors.get("store_id")}
      >
        {(control) => (
          <input
            {...control}
            className="input"
            type="number"
            min={0}
            step={1}
            value={storeId}
            onChange={(event) => setStoreId(event.target.value)}
          />
        )}
      </Field>
      <ConversionParamsForm value={conversion} onChange={setConversion} errors={errors} />
    </FormShell>
  );
}

const CALL_TEXT = vi.demand.form.callFields;

const CALL_FIELDS = [
  { key: "base_rate", ...CALL_TEXT.base_rate, step: "any" },
  { key: "handle_seconds", ...CALL_TEXT.handle_seconds, step: "any" },
  { key: "patience_seconds", ...CALL_TEXT.patience_seconds, step: "any" },
  { key: "service_level", ...CALL_TEXT.service_level, step: "any" },
  { key: "answer_seconds", ...CALL_TEXT.answer_seconds, step: "any" },
  { key: "min_staff", ...CALL_TEXT.min_staff, step: "1" },
  { key: "noise", ...CALL_TEXT.noise, step: "any" },
  { key: "seed", ...CALL_TEXT.seed, step: "1" },
] as const;

type CallFieldKey = (typeof CALL_FIELDS)[number]["key"];

const CALL_DEFAULTS: Record<CallFieldKey, string> = {
  base_rate: "",
  handle_seconds: "",
  patience_seconds: "",
  service_level: "0.8",
  answer_seconds: "20",
  min_staff: "1",
  noise: "0",
  seed: "0",
};

function CallCenterForm({ onCreated }: { onCreated: CreatedHandler }) {
  const create = useCreateDemandProfileFromCallCenter();
  const [name, setName] = useState("");
  const [values, setValues] = useState(CALL_DEFAULTS);
  const errors = errorsByPath(create.error);
  function submit() {
    const numbers = Object.fromEntries(
      CALL_FIELDS.flatMap((field) => {
        const parsed = toNumber(values[field.key]);
        return Number.isNaN(parsed) ? [] : [[field.key, parsed]];
      }),
    );
    create.mutate({ name, ...numbers } as CallCenterDemandRequest, { onSuccess: onCreated });
  }
  return (
    <FormShell
      error={create.error}
      pending={create.isPending}
      submitLabel={vi.demand.form.simulate}
      onSubmit={submit}
    >
      <Notice kind="info" title={vi.demand.callTitle}>
        {vi.demand.form.callBody}
      </Notice>
      <NameField value={name} onChange={setName} errors={errors} />
      <div className="form-grid">
        {CALL_FIELDS.map((field) => (
          <Field
            key={field.key}
            id={`new-${field.key.replaceAll("_", "-")}`}
            label={field.label}
            hint={field.hint || undefined}
            error={errors.get(field.key)}
          >
            {(control) => (
              <input
                {...control}
                className="input"
                type="number"
                min={0}
                step={field.step}
                value={values[field.key]}
                onChange={(event) => setValues({ ...values, [field.key]: event.target.value })}
              />
            )}
          </Field>
        ))}
      </div>
    </FormShell>
  );
}

export function NewProfileForm({ onCreated }: { onCreated: CreatedHandler }) {
  const [source, setSource] = useState<SourceChoice>("manual");
  return (
    <div className="form-stack">
      <fieldset className="field">
        <legend>{vi.demand.form.source}</legend>
        <div className="seg">
          {SOURCES.map((option) => (
            <label key={option.value} className="seg-opt">
              <input
                type="radio"
                name="profile-source"
                value={option.value}
                checked={source === option.value}
                onChange={() => setSource(option.value)}
              />
              {option.label}
            </label>
          ))}
        </div>
      </fieldset>
      {source === "manual" && <ManualForm onCreated={onCreated} />}
      {source === "csv" && <CsvForm onCreated={onCreated} />}
      {source === "freshretailnet" && <DatasetForm onCreated={onCreated} />}
      {source === "call_center" && <CallCenterForm onCreated={onCreated} />}
    </div>
  );
}
