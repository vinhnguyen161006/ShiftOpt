import type { ReactNode } from "react";
import { Corners } from "./Corners";

type WorkspacePanelProps = {
  name: string;
  meta?: string;
  tag?: string;
  children: ReactNode;
};

export function WorkspacePanel({ name, meta, tag, children }: WorkspacePanelProps) {
  return (
    <section className="blueprint workspace">
      <Corners />
      <div className="workspace-head">
        <h2 className="workspace-name">
          <span className="workspace-dot" aria-hidden="true" />
          {name}
        </h2>
        {meta && <span className="workspace-meta">{meta}</span>}
        {tag && <span className="tag tag-outline workspace-tag">{tag}</span>}
      </div>
      {children}
    </section>
  );
}

type WorkspaceBlockProps = {
  title: string;
  caption?: string;
  aside?: ReactNode;
  children: ReactNode;
};

export function WorkspaceBlock({ title, caption, aside, children }: WorkspaceBlockProps) {
  return (
    <div className="workspace-block">
      <div className={aside ? "block-head block-head-center" : "block-head"}>
        <h3 className="block-title">{title}</h3>
        {caption && <span className="block-caption">{caption}</span>}
        {aside && <div className="block-aside">{aside}</div>}
      </div>
      {children}
    </div>
  );
}
