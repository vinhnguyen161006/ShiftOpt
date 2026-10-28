import { Link } from "react-router";
import { Corners } from "../../../components/ui/Corners";
import { WORKSPACE_LINKS } from "../links";

export function CallToAction() {
  return (
    <section id="cta" className="home-cta">
      <div className="container home-cta-inner">
        <div className="home-cta-copy">
          <h2 className="home-cta-title">Build a Better Workforce Schedule.</h2>
          <p className="home-cta-text">
            Start with your staffing requirements, configure your workforce, and explore an
            optimized scheduling plan.
          </p>
        </div>
        <div className="home-cta-actions">
          <Link className="btn btn-primary blueprint home-cta-button" to={WORKSPACE_LINKS.demand}>
            Open ShiftOpt
            <Corners />
          </Link>
          <span className="home-cta-hint">Opens the workspace. No account, no sample tenant.</span>
        </div>
      </div>
    </section>
  );
}
