import { Table } from "../../../components/ui/Table";
import { vi } from "../../../locales/vi";
import type { DemandProfileRead } from "../../../types/models";

type DemandProfileListProps = {
  profiles: DemandProfileRead[];
  selectedId: number | undefined;
  onSelect: (profileId: number) => void;
};

export function DemandProfileList({ profiles, selectedId, onSelect }: DemandProfileListProps) {
  return (
    <Table
      caption={vi.demand.listCaption}
      rows={profiles}
      rowKey={(profile) => profile.id}
      columns={[
        {
          key: "name",
          label: vi.demand.profile,
          render: (profile) => (
            <button
              type="button"
              className="link-button"
              aria-current={profile.id === selectedId}
              onClick={() => onSelect(profile.id)}
            >
              {profile.name}
            </button>
          ),
        },
        {
          key: "peak",
          label: vi.demand.peak,
          align: "end",
          render: (profile) => Math.max(0, ...profile.required_staff),
        },
      ]}
    />
  );
}
