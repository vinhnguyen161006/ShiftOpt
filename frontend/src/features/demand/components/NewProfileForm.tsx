import { type FormEvent, type ReactNode, useState } from "react";
import { Button } from "../../../components/ui/Button";
import { ErrorSummary, Notice } from "../../../components/ui/Feedback";
import { Field } from "../../../components/ui/Field";
import { errorsByPath, generalError, summaryErrors, toNumber } from "../../../lib/form";
import { HOURS_PER_WEEK } from "../../../lib/time";
import { vi } from "../../../locales/vi";
import type { ConversionParams, DemandProfileRead, SalesInspection } from "../../../types/models";
import {
  useCreateDemandProfile,
  useCreateDemandProfileFromCsv,
  useIngestSales,
  useInspectSales,
} from "../api/demand";
import { ConversionParamsForm, conversionFieldId } from "./ConversionParamsForm";

type SourceChoice = "manual" | "csv" | "sales";

const SOURCES: { value: SourceChoice; label: string }[] = (["manual", "csv", "sales"] as const).map(
  (value) => ({ value, label: vi.demand.form.sources[value] }),
);

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

const MAPPING_FIELDS = [
  { key: "date_column", required: true },
  { key: "sales_column", required: true },
  { key: "hour_column", required: false },
  { key: "stockout_column", required: false },
  { key: "product_column", required: false },
  { key: "store_column", required: false },
] as const;

type MappingKey = (typeof MAPPING_FIELDS)[number]["key"];
type Mapping = Record<MappingKey, string>;

const MAPPING_LABELS: Record<MappingKey, string> = {
  date_column: vi.demand.form.columnDate,
  sales_column: vi.demand.form.columnSales,
  hour_column: vi.demand.form.columnHour,
  stockout_column: vi.demand.form.columnStockout,
  product_column: vi.demand.form.columnProduct,
  store_column: vi.demand.form.columnStore,
};

function mappingFrom(guess: SalesInspection["guess"]): Mapping {
  return Object.fromEntries(MAPPING_FIELDS.map(({ key }) => [key, guess[key] ?? ""])) as Mapping;
}

function SalesForm({ onCreated }: { onCreated: CreatedHandler }) {
  const inspect = useInspectSales();
  const ingest = useIngestSales();
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [inspection, setInspection] = useState<SalesInspection | null>(null);
  const [mapping, setMapping] = useState<Mapping>(mappingFrom({}));
  const [store, setStore] = useState("");
  const [nightFromSales, setNightFromSales] = useState(false);
  const [conversion, setConversion] = useState(DEFAULT_CONVERSION);
  const errors = errorsByPath(ingest.error);

  function chooseFile(next: File | null) {
    setFile(next);
    setInspection(null);
    if (!next) {
      return;
    }
    inspect.mutate(next, {
      onSuccess: (result) => {
        setInspection(result);
        setMapping(mappingFrom(result.guess));
        setStore(result.stores.length === 1 ? result.stores[0] : "");
      },
    });
  }

  function submit() {
    if (!file || !inspection) {
      return;
    }
    ingest.mutate(
      {
        file,
        query: {
          name,
          ...mapping,
          store: mapping.store_column ? store.trim() || null : null,
          night_from_sales: nightFromSales,
          ...conversion,
        },
      },
      { onSuccess: onCreated },
    );
  }

  return (
    <FormShell
      error={ingest.error}
      pending={ingest.isPending}
      submitLabel={vi.demand.form.derive}
      onSubmit={submit}
    >
      <Notice kind="warning" title={vi.demand.salesTitle}>
        {vi.demand.form.salesBody}
      </Notice>
      <NameField value={name} onChange={setName} errors={errors} />
      <Field
        id="new-sales-file"
        label={vi.demand.form.salesFile}
        hint={vi.demand.form.salesFileHint}
      >
        {(control) => (
          <input
            {...control}
            className="input"
            type="file"
            accept=".csv,.parquet,text/csv,application/octet-stream"
            onChange={(event) => chooseFile(event.target.files?.[0] ?? null)}
          />
        )}
      </Field>
      {inspect.isPending && <Notice kind="info" title={vi.demand.form.inspecting} />}
      {inspect.error && <Notice kind="error" title={generalError(inspect.error) ?? ""} />}
      {inspection && (
        <>
          <p className="muted">{vi.demand.form.inspected(inspection.format, inspection.rows)}</p>
          <div className="form-grid">
            {MAPPING_FIELDS.map(({ key, required }) => (
              <Field
                key={key}
                id={`new-${key.replaceAll("_", "-")}`}
                label={MAPPING_LABELS[key]}
                error={errors.get(key)}
              >
                {(control) => (
                  <select
                    {...control}
                    className="input"
                    value={mapping[key]}
                    onChange={(event) => setMapping({ ...mapping, [key]: event.target.value })}
                  >
                    {!required && <option value="">{vi.demand.form.noColumn}</option>}
                    {inspection.columns.map((column) => (
                      <option key={column} value={column}>
                        {column}
                      </option>
                    ))}
                  </select>
                )}
              </Field>
            ))}
          </div>
          {mapping.store_column && (
            <Field
              id="new-store"
              label={vi.demand.form.storeId}
              hint={vi.demand.form.storeIdHint}
              error={errors.get("store")}
            >
              {(control) => (
                <input
                  {...control}
                  className="input"
                  list="new-store-options"
                  value={store}
                  onChange={(event) => setStore(event.target.value)}
                />
              )}
            </Field>
          )}
          <datalist id="new-store-options">
            {inspection.stores.map((value) => (
              <option key={value} value={value} />
            ))}
          </datalist>
          <label>
            <input
              type="checkbox"
              checked={nightFromSales}
              onChange={(event) => setNightFromSales(event.target.checked)}
            />{" "}
            {vi.demand.form.nightFromSales}
          </label>
          <ConversionParamsForm value={conversion} onChange={setConversion} errors={errors} />
        </>
      )}
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
      {source === "sales" && <SalesForm onCreated={onCreated} />}
    </div>
  );
}
