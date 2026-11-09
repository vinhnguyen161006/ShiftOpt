import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { Button } from "../../components/ui/Button";
import { EmptyState, Loading, Notice } from "../../components/ui/Feedback";
import { PageHeader, Panel } from "../../components/ui/Layout";
import { Modal } from "../../components/ui/Modal";
import { useCompliance } from "../../features/compliance/api/compliance";
import { ManualEditor } from "../../features/compliance/components/ManualEditor";
import { ReplacementList } from "../../features/compliance/components/ReplacementList";
import { ShortfallExplanation } from "../../features/compliance/components/ShortfallExplanation";
import { ViolationList } from "../../features/compliance/components/ViolationList";
import { useDemandProfiles } from "../../features/demand/api/demand";
import { useEmployees } from "../../features/employees/api/employees";
import { ChangesSummary } from "../../features/reroster/components/ChangesSummary";
import { RerosterForm } from "../../features/reroster/components/RerosterForm";
import {
  isActive,
  useScheduleKpi,
  useScheduleRun,
  useScheduleRuns,
  useStaleness,
} from "../../features/schedule/api/schedules";
import { CostSummary } from "../../features/schedule/components/CostSummary";
import { NewRunForm } from "../../features/schedule/components/NewRunForm";
import { RepairForm } from "../../features/schedule/components/RepairForm";
import { ExportLinks, ScheduleKpis } from "../../features/schedule/components/RunResults";
import { RunsTable } from "../../features/schedule/components/RunsTable";
import { RunWorkspace } from "../../features/schedule/components/RunWorkspace";
import { SolveDetails, SolveNotice } from "../../features/schedule/components/SolveStatusPanel";
import { useShiftTemplates } from "../../features/shift-templates/api/shift-templates";
import { errorMessage } from "../../lib/api-client";
import { useLaborRules } from "../../lib/labor-rules";
import { isRepairRun } from "../../lib/run-kind";
import { vi } from "../../locales/vi";

function Prerequisites({ missing }: { missing: { label: string; to: string }[] }) {
  return (
    <EmptyState title={vi.schedule.missingTitle}>
      {vi.schedule.missingBody}{" "}
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
      <Notice kind="error" title={vi.schedule.inputsError}>
        {errorMessage(failed.error)}
      </Notice>
    );
  }
  if (!profiles.data || !templates.data || !employees.data || !rules.data) {
    return <Loading label={vi.schedule.loadingInputs} />;
  }
  const missing = [
    profiles.data.length === 0 ? { label: vi.schedule.missingProfile, to: "/demand" } : null,
    templates.data.length === 0
      ? { label: vi.schedule.missingTemplate, to: "/shift-templates" }
      : null,
    employees.data.length === 0 ? { label: vi.schedule.missingEmployee, to: "/employees" } : null,
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
      <PageHeader eyebrow={vi.schedule.eyebrow} title={vi.schedule.title} lead={vi.schedule.lead} />
      <Panel title={vi.schedule.newPanel} labelledBy="new-run-title">
        <NewRunPanel />
      </Panel>
      <Panel title={vi.schedule.runsPanel} labelledBy="runs-title">
        {runs.isPending && <Loading label={vi.schedule.loadingRuns} />}
        {runs.isError && <Notice kind="error" title={errorMessage(runs.error)} />}
        {runs.data?.length === 0 && (
          <EmptyState title={vi.schedule.noRunsTitle}>{vi.schedule.noRunsBody}</EmptyState>
        )}
        {runs.data && runs.data.length > 0 && <RunsTable runs={runs.data} />}
      </Panel>
    </div>
  );
}

function StaleNotice({ runId, enabled }: { runId: number; enabled: boolean }) {
  const staleness = useStaleness(runId, enabled);
  if (staleness.data?.state !== "stale") {
    return null;
  }
  return (
    <Notice kind="warning" title={vi.schedule.stale.title}>
      {vi.schedule.stale.reasons[staleness.data.reason ?? ""] ?? vi.schedule.stale.fallback}{" "}
      {vi.schedule.stale.hint}
    </Notice>
  );
}

function RunView({ runId }: { runId: number }) {
  const navigate = useNavigate();
  const run = useScheduleRun(runId);
  const hasSchedule = run.data?.assignments !== null && run.data?.assignments !== undefined;
  const kpi = useScheduleKpi(runId, hasSchedule);
  const compliance = useCompliance(runId, hasSchedule);
  const [editing, setEditing] = useState(false);
  const [repairing, setRepairing] = useState(false);
  const [rerostering, setRerostering] = useState(false);

  if (run.isPending) {
    return <Loading label={vi.schedule.loadingRun(runId)} />;
  }
  if (run.isError) {
    return (
      <EmptyState
        title={vi.schedule.runLoadError(runId)}
        action={<Link to="/schedule">{vi.schedule.backToRuns}</Link>}
      >
        {errorMessage(run.error)}
      </EmptyState>
    );
  }
  const data = run.data;
  return (
    <div className="page">
      <PageHeader
        eyebrow={vi.schedule.runEyebrow(data.id, data.parent_run_id, isRepairRun(data))}
        title={vi.schedule.resultTitle}
        lead={vi.schedule.resultLead(
          new Date(data.created_at).toLocaleString("vi-VN"),
          data.employee_codes.length,
          data.shift_types.length,
        )}
        actions={
          <span className="run-header-actions">
            <Link to="/schedule">{vi.schedule.allRuns}</Link>
            {hasSchedule && <ExportLinks runId={data.id} />}
          </span>
        }
      />
      <SolveNotice run={data} />
      <StaleNotice runId={runId} enabled={hasSchedule} />
      {hasSchedule && kpi.isError && <Notice kind="error" title={errorMessage(kpi.error)} />}
      {hasSchedule && <RunWorkspace run={data} kpi={kpi.data} />}
      {hasSchedule && (
        <Panel
          title={vi.schedule.compliance}
          labelledBy="compliance-title"
          aside={
            <span className="run-header-actions">
              {data.status === "succeeded" && (
                <Button size="sm" onClick={() => setRerostering(true)}>
                  {vi.schedule.reroster.button}
                </Button>
              )}
              <Button size="sm" onClick={() => setRepairing(true)}>
                {vi.schedule.repairButton}
              </Button>
              <Button size="sm" onClick={() => setEditing(true)}>
                {vi.schedule.editByHand}
              </Button>
            </span>
          }
        >
          {compliance.isPending && <Loading label={vi.schedule.checking} />}
          {compliance.isError && <Notice kind="error" title={errorMessage(compliance.error)} />}
          {compliance.data && <ViolationList compliance={compliance.data} />}
        </Panel>
      )}
      {hasSchedule && (data.understaffed_hours ?? 0) > 0 && (
        <Panel title={vi.schedule.shortfallPanel} labelledBy="shortfall-title">
          <ShortfallExplanation run={data} />
        </Panel>
      )}
      {hasSchedule && (
        <Panel title={vi.schedule.replacementsPanel} labelledBy="replacements-title">
          <ReplacementList
            run={data}
            onCreated={(createdId) => navigate(`/schedule/${createdId}`)}
          />
        </Panel>
      )}
      {hasSchedule && data.parent_run_id !== null && !isActive(data.status) && (
        <Panel title={vi.schedule.reroster.changesTitle} labelledBy="changes-title">
          <ChangesSummary runId={data.id} parentId={data.parent_run_id} />
        </Panel>
      )}
      {!isActive(data.status) && (
        <Panel title={vi.schedule.runDetails} labelledBy="details-title">
          <div className="form-stack">
            <SolveDetails run={data} />
            {kpi.data && <ScheduleKpis kpi={kpi.data} />}
          </div>
        </Panel>
      )}
      {hasSchedule && (
        <>
          <Panel title={vi.schedule.laborCost} labelledBy="cost-title">
            {kpi.data && <CostSummary kpi={kpi.data} weeklyBudget={data.weekly_budget} />}
          </Panel>
          <Modal
            title={vi.schedule.reroster.modalTitle(data.id)}
            open={rerostering}
            onClose={() => setRerostering(false)}
            wide
          >
            <RerosterForm
              run={data}
              onCreated={(createdId) => {
                setRerostering(false);
                navigate(`/schedule/${createdId}`);
              }}
            />
          </Modal>
          <Modal
            title={vi.schedule.repairTitle(data.id)}
            open={repairing}
            onClose={() => setRepairing(false)}
            wide
          >
            <RepairForm
              run={data}
              onCreated={(jobId) => {
                setRepairing(false);
                navigate(`/schedule/${jobId}`);
              }}
            />
          </Modal>
          <Modal
            title={vi.schedule.editTitle(data.id)}
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
