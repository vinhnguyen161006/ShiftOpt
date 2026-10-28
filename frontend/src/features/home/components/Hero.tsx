import { Link } from "react-router";
import { Corners } from "../../../components/ui/Corners";
import { WORKSPACE_LINKS } from "../links";
import { WorkspacePreview } from "./WorkspacePreview";

const PRINCIPLES = [
  {
    title: "Solver, then validator",
    body: "Every schedule is re-checked against hard constraints by code independent of the model.",
  },
  {
    title: "Assumptions on screen",
    body: "Conversion factors and labor-rule parameters are inputs you can see and change, not constants buried in code.",
  },
];

export function Hero() {
  return (
    <section id="top" className="home-hero">
      <div className="container home-split">
        <div className="home-hero-copy">
          <div className="home-eyebrow-row">
            <span className="home-eyebrow-rule" />
            <span className="home-eyebrow">Workforce Optimization Platform</span>
          </div>
          <h1 className="home-hero-title">
            Smarter Schedules.
            <br />
            Better Workforce Decisions.
          </h1>
          <p className="home-hero-lead">
            Turn hourly staffing demand into optimized employee schedules. Balance workforce
            coverage, labor costs, and scheduling constraints with mathematical optimization.
          </p>
          <div className="home-hero-actions">
            <Link
              className="btn btn-primary blueprint home-hero-primary"
              to={WORKSPACE_LINKS.schedule}
            >
              Optimize a Schedule
              <Corners />
            </Link>
            <a className="btn btn-secondary home-hero-secondary" href="#features">
              Explore Features
            </a>
          </div>
          <div className="home-principles">
            {PRINCIPLES.map((principle) => (
              <div key={principle.title} className="home-principle">
                <div className="home-principle-title">{principle.title}</div>
                <p className="home-principle-body">{principle.body}</p>
              </div>
            ))}
          </div>
        </div>
        <WorkspacePreview />
      </div>
    </section>
  );
}
