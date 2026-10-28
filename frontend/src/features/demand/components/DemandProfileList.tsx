import { Table } from "../../../components/ui/Table";
import type { DemandProfileRead } from "../../../types/models";

type DemandProfileListProps = {
  profiles: DemandProfileRead[];
  selectedId: number | undefined;
  onSelect: (profileId: number) => void;
};

export function DemandProfileList({ profiles, selectedId, onSelect }: DemandProfileListProps) {
  return (
    <Table
      caption="Demand profiles"
      rows={profiles}
      rowKey={(profile) => profile.id}
      columns={[
        {
          key: "name",
          label: "Profile",
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
          label: "Peak",
          align: "end",
          render: (profile) => Math.max(0, ...profile.required_staff),
        },
      ]}
    />
  );
}
