import { useState } from "react";
import { useSearchParams } from "react-router";
import { Button } from "../../../components/ui/Button";
import { EmptyState, Loading, Notice } from "../../../components/ui/Feedback";
import { PageHeader } from "../../../components/ui/Layout";
import { Modal } from "../../../components/ui/Modal";
import { errorMessage } from "../../../lib/api-client";
import { useDemandProfiles } from "../api/demand";
import "../demand.css";
import { DemandProfileList } from "./DemandProfileList";
import { DemandProfileView } from "./DemandProfileView";
import { NewProfileForm } from "./NewProfileForm";

const PROFILE_PARAM = "profile";

export function DemandPage() {
  const [params, setParams] = useSearchParams();
  const profiles = useDemandProfiles();
  const [creating, setCreating] = useState(false);
  const requestedId = Number(params.get(PROFILE_PARAM)) || undefined;
  const selected =
    profiles.data?.find((profile) => profile.id === requestedId) ?? profiles.data?.[0];

  function select(profileId: number | undefined) {
    setParams(profileId === undefined ? {} : { [PROFILE_PARAM]: String(profileId) });
  }

  const newButton = (
    <Button variant="primary" onClick={() => setCreating(true)}>
      New demand profile
    </Button>
  );

  return (
    <div className="page">
      <PageHeader
        eyebrow="Demand"
        title="Hourly staffing demand"
        lead="A demand profile is the head count required in each of the 168 hours of the week. Enter it by hand, import a CSV, derive it from FreshRetailNet sales with visible assumptions, or staff simulated call arrivals with Erlang A."
        actions={newButton}
      />
      {profiles.isPending && <Loading label="Loading demand profiles" />}
      {profiles.isError && (
        <Notice kind="error" title="Could not load demand profiles">
          {errorMessage(profiles.error)}
        </Notice>
      )}
      {profiles.data?.length === 0 && (
        <EmptyState title="Start with a demand profile" action={newButton}>
          Optimization needs the required head count for every hour of the week. Create one from a
          grid, a CSV file, a FreshRetailNet store or a simulated call center.
        </EmptyState>
      )}
      {profiles.data && selected && (
        <div className="split">
          <DemandProfileList profiles={profiles.data} selectedId={selected.id} onSelect={select} />
          <DemandProfileView key={selected.id} profile={selected} onSelect={select} />
        </div>
      )}
      <Modal title="New demand profile" open={creating} onClose={() => setCreating(false)} wide>
        <NewProfileForm
          onCreated={(profile) => {
            setCreating(false);
            select(profile.id);
          }}
        />
      </Modal>
    </div>
  );
}
