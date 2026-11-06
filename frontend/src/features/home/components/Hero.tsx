import { Link } from "react-router";
import { Corners } from "../../../components/ui/Corners";
import { vi } from "../../../locales/vi";
import { WORKSPACE_LINKS } from "../links";
import { WorkspacePreview } from "./WorkspacePreview";

export function Hero() {
  return (
    <section id="top" className="home-hero">
      <div className="container home-split">
        <div className="home-hero-copy">
          <div className="home-eyebrow-row">
            <span className="home-eyebrow-rule" />
            <span className="home-eyebrow">{vi.home.eyebrow}</span>
          </div>
          <h1 className="home-hero-title">
            {vi.home.titleTop}
            <br />
            {vi.home.titleBottom}
          </h1>
          <p className="home-hero-lead">{vi.home.lead}</p>
          <div className="home-hero-actions">
            <Link
              className="btn btn-primary blueprint home-hero-primary"
              to={WORKSPACE_LINKS.schedule}
            >
              {vi.home.primary}
              <Corners />
            </Link>
            <Link className="btn btn-secondary home-hero-secondary" to={WORKSPACE_LINKS.demand}>
              {vi.home.secondary}
            </Link>
          </div>
        </div>
        <WorkspacePreview />
      </div>
    </section>
  );
}
