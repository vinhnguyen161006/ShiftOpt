import { type FormEvent, useState } from "react";
import { Button } from "../../../components/ui/Button";
import { Notice } from "../../../components/ui/Feedback";
import { Field } from "../../../components/ui/Field";
import { errorMessage } from "../../../lib/api-client";
import { vi } from "../../../locales/vi";
import { useImportEmployees } from "../api/employees";

export function EmployeeCsvForm({ onDone }: { onDone: () => void }) {
  const importEmployees = useImportEmployees();
  const [text, setText] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    importEmployees.mutate({ csv_text: text }, { onSuccess: onDone });
  }

  return (
    <form className="form-stack" onSubmit={handleSubmit} noValidate>
      <Field id="employee-csv-file" label={vi.employees.csv.file} hint={vi.employees.csv.fileHint}>
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
        id="employee-csv-text"
        label={vi.employees.csv.content}
        hint={vi.employees.csv.contentHint}
      >
        {(control) => (
          <textarea
            {...control}
            className="input"
            rows={8}
            placeholder={vi.employees.csv.example}
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
        )}
      </Field>
      {importEmployees.isError && (
        <Notice kind="error" title={errorMessage(importEmployees.error)} />
      )}
      <div className="form-actions">
        <Button onClick={onDone}>{vi.common.cancel}</Button>
        <Button
          type="submit"
          variant="primary"
          disabled={importEmployees.isPending || text.trim() === ""}
        >
          {importEmployees.isPending ? vi.employees.csv.importing : vi.employees.csv.submit}
        </Button>
      </div>
    </form>
  );
}
