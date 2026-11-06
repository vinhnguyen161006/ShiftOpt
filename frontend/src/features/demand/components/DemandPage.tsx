import { useState } from "react";
import { useSearchParams } from "react-router";
import { Button } from "../../../components/ui/Button";
import { EmptyState, Loading, Notice } from "../../../components/ui/Feedback";
import { PageHeader } from "../../../components/ui/Layout";
import { Modal } from "../../../components/ui/Modal";
import { errorMessage } from "../../../lib/api-client";
import { useDemandProfiles } from "../api/demand";
import "../demand.css";
import { vi } from "../../../locales/vi";
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
      {vi.demand.newProfile}
    </Button>
  );

  return (
    <div className="page">
      <PageHeader
        eyebrow={vi.demand.eyebrow}
        title={vi.demand.title}
        lead={vi.demand.lead}
        actions={newButton}
      />
      {profiles.isPending && <Loading label={vi.demand.loading} />}
      {profiles.isError && (
        <Notice kind="error" title={vi.demand.loadError}>
          {errorMessage(profiles.error)}
        </Notice>
      )}
      {profiles.data?.length === 0 && (
        <EmptyState title={vi.demand.emptyTitle} action={newButton}>
          {vi.demand.emptyBody}
        </EmptyState>
      )}
      {profiles.data && selected && (
        <div className="split">
          <DemandProfileList profiles={profiles.data} selectedId={selected.id} onSelect={select} />
          <DemandProfileView key={selected.id} profile={selected} onSelect={select} />
        </div>
      )}
      <Modal title={vi.demand.newProfile} open={creating} onClose={() => setCreating(false)} wide>
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
