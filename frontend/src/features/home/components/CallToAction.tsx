import { Link } from "react-router";
import { Corners } from "../../../components/ui/Corners";
import { vi } from "../../../locales/vi";
import { WORKSPACE_LINKS } from "../links";

export function CallToAction() {
  return (
    <section id="cta" className="home-cta">
      <div className="container home-cta-inner">
        <div className="home-cta-copy">
          <h2 className="home-cta-title">{vi.home.cta.title}</h2>
          <p className="home-cta-text">{vi.home.cta.text}</p>
        </div>
        <div className="home-cta-actions">
          <Link className="btn btn-primary blueprint home-cta-button" to={WORKSPACE_LINKS.demand}>
            {vi.home.cta.button}
            <Corners />
          </Link>
          <span className="home-cta-hint">{vi.home.cta.hint}</span>
        </div>
      </div>
    </section>
  );
}
