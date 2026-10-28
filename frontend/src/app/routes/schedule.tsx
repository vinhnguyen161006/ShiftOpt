import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { Button } from "../../components/ui/Button";
import { EmptyState, Loading, Notice } from "../../components/ui/Feedback";
import { PageHeader, Panel } from "../../components/ui/Layout";
import { Modal } from "../../components/ui/Modal";
import { useCompliance } from "../../features/compliance/api/compliance";
import { ManualEditor } from "../../features/compliance/components/ManualEditor";
import { ViolationList } from "../../features/compliance/components/ViolationList";
import { useDemandProfiles } from "../../features/demand/api/demand";
import { useEmployees } from "../../features/employees/api/employees";
import {
  useScheduleKpi,
  useScheduleRun,
  useScheduleRuns,
} from "../../features/schedule/api/schedules";
import { CostSummary } from "../../features/schedule/components/CostSummary";
import { CoverageChart } from "../../features/schedule/components/CoverageChart";
import { NewRunForm } from "../../features/schedule/components/NewRunForm";
import { ExportLinks, ScheduleKpis } from "../../features/schedule/components/RunResults";
import { RunsTable } from "../../features/schedule/components/RunsTable";
import { ScheduleGrid } from "../../features/schedule/components/ScheduleGrid";
import { SolveStatusPanel } from "../../features/schedule/components/SolveStatusPanel";
import { useShiftTemplates } from "../../features/shift-templates/api/shift-templates";
import { errorMessage } from "../../lib/api-client";
import { useLaborRules } from "../../lib/labor-rules";

function Prerequisites({ missing }: { missing: { label: string; to: string }[] }) {
  return (
    <EmptyState title="A few inputs are still missing">
      The optimizer needs a demand profile, at least one shift template and at least one employee.
      Still to add:{" "}
      {missing.map((item, index) => (
        <span key={item.to}>
          {index > 0 && ", "}
          <Link to={item.to}>{item.label}</Link>
        </span>
      ))}
      .
    </EmptyState>
  );
}

function NewRunPanel() {
  const navigate = useNavigate();
  const profiles = useDemandProfiles();
  const templates = useShiftTemplates();
  const employees = useEmployees();
  const rules = useLaborRules();
  const queries = [profiles, templates, employees, rules];
  const failed = queries.find((query) => query.isError);

  if (failed) {
    return (
      <Notice kind="error" title="Could not load the inputs">
        {errorMessage(failed.error)}
      </Notice>
    );
  }
  if (!profiles.data || !templates.data || !employees.data || !rules.data) {
    return <Loading label="Loading demand, shift templates and employees" />;
  }
  const missing = [
    profiles.data.length === 0 ? { label: "a demand profile", to: "/demand" } : null,
    templates.data.length === 0 ? { label: "a shift template", to: "/shift-templates" } : null,
    employees.data.length === 0 ? { label: "an employee", to: "/employees" } : null,
  ].filter((item) => item !== null);
  if (missing.length > 0) {
    return <Prerequisites missing={missing} />;
  }
  return (
    <NewRunForm
      profiles={profiles.data}
      templates={templates.data}
      employeeCount={employees.data.length}
      rules={rules.data}
      onCreated={(runId) => navigate(`/schedule/${runId}`)}
    />
  );
}

function ScheduleHome() {
  const runs = useScheduleRuns();
  return (
    <div className="page">
      <PageHeader
        eyebrow="Schedule"
        title="Optimize a weekly schedule"
        lead="Pick a demand profile and the shift types to use, then optimize. Every result is re-checked by the independent validator before it is shown as compliant."
      />
      <Panel title="New optimization" labelledBy="new-run-title">
        <NewRunPanel />
      </Panel>
      <Panel title="Runs" labelledBy="runs-title">
        {runs.isPending && <Loading label="Loading runs" />}
        {runs.isError && <Notice kind="error" title={errorMessage(runs.error)} />}
        {runs.data?.length === 0 && (
          <EmptyState title="No runs yet">
            Results appear here once you optimize. Each run keeps its inputs, solver version and
            seed, so it can be reproduced.
          </EmptyState>
        )}
        {runs.data && runs.data.length > 0 && <RunsTable runs={runs.data} />}
      </Panel>
    </div>
  );
}

function RunView({ runId }: { runId: number }) {
  const navigate = useNavigate();
  const run = useScheduleRun(runId);
  const hasSchedule = run.data?.assignments !== null && run.data?.assignments !== undefined;
  const kpi = useScheduleKpi(runId, hasSchedule);
  const compliance = useCompliance(runId, hasSchedule);
  const [editing, setEditing] = useState(false);

  if (run.isPending) {
    return <Loading label={`Loading run ${runId}`} />;
  }
  if (run.isError) {
    return (
      <EmptyState
        title={`Run ${runId} could not be loaded`}
        action={<Link to="/schedule">Back to runs</Link>}
      >
        {errorMessage(run.error)}
      </EmptyState>
    );
  }
  const data = run.data;
  return (
    <div className="page">
      <PageHeader
        eyebrow={`Run ${data.id}${data.parent_run_id === null ? "" : `, edited from run ${data.parent_run_id}`}`}
        title="Schedule result"
        lead={`Created ${new Date(data.created_at).toLocaleString("en-GB")} for ${data.employee_codes.length} employees and ${data.shift_types.length} shift types.`}
        actions={
          <span className="run-header-actions">
            <Link to="/schedule">All runs</Link>
            {hasSchedule && <ExportLinks runId={data.id} />}
          </span>
        }
      />
      <SolveStatusPanel run={data} />
      {hasSchedule && (
        <>
          <Panel
            title="Compliance"
            labelledBy="compliance-title"
            aside={
              <Button size="sm" onClick={() => setEditing(true)}>
                Edit schedule by hand
              </Button>
            }
          >
            {compliance.isPending && <Loading label="Checking constraints" />}
            {compliance.isError && <Notice kind="error" title={errorMessage(compliance.error)} />}
            {compliance.data && <ViolationList compliance={compliance.data} />}
          </Panel>
          <Panel title="Coverage" labelledBy="coverage-title">
            {kpi.isPending && <Loading label="Computing KPIs" />}
            {kpi.isError && <Notice kind="error" title={errorMessage(kpi.error)} />}
            {kpi.data && (
              <div className="form-stack">
                <ScheduleKpis kpi={kpi.data} />
                <CoverageChart kpi={kpi.data} />
              </div>
            )}
          </Panel>
          <Panel title="Weekly roster" labelledBy="roster-title">
            <ScheduleGrid run={data} />
          </Panel>
          <Panel title="Labor cost" labelledBy="cost-title">
            {kpi.data && <CostSummary kpi={kpi.data} />}
          </Panel>
          <Modal
            title={`Edit run ${data.id} by hand`}
            open={editing}
            onClose={() => setEditing(false)}
            wide
          >
            <ManualEditor
              run={data}
              onCreated={(createdId) => {
                setEditing(false);
                navigate(`/schedule/${createdId}`);
              }}
            />
          </Modal>
        </>
      )}
    </div>
  );
}

export function ScheduleRoute() {
  const { runId } = useParams();
  const parsed = Number(runId);
  return runId && Number.isInteger(parsed) ? (
    <RunView key={parsed} runId={parsed} />
  ) : (
    <ScheduleHome />
  );
}
