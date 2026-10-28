import { Corners } from "../../../components/ui/Corners";

const RULES = [
  {
    value: "12 h",
    title: "Rest between shifts",
    body: "A late shift followed by an early shift the next morning is excluded by the model, not flagged afterwards.",
  },
  {
    value: "24 h",
    title: "Weekly continuous rest",
    body: "Measured on the hour axis, so a night shift ending in the morning does not quietly consume the rest day.",
  },
  {
    value: "48 h",
    title: "Weekly working limit",
    body: "Per-employee hour ceiling, configurable down to 40 hours for alternative scenarios.",
  },
  {
    value: "6 d",
    title: "Consecutive working days",
    body: "A sliding window guarantees at least one non-working day in every seven.",
  },
  {
    value: "0",
    title: "Hard violations allowed",
    body: "The independent validator re-checks the produced schedule; a run with any hard violation is not reported as compliant.",
  },
];

export function Rules() {
  return (
    <section className="home-rules">
      <div className="container">
        <div className="home-section-head home-section-head-tight">
          <div className="home-rules-intro">
            <div className="home-eyebrow">Constraints &amp; reliability</div>
            <h2 className="home-how-title home-rules-title">
              Rules the schedule is not allowed to break
            </h2>
            <p className="home-rules-lead">
              Labor-rule limits are configurable parameters of a run, held as hard constraints in
              the model and checked again afterwards by the validator.
            </p>
          </div>
        </div>
        <div className="home-rule-grid">
          {RULES.map((rule) => (
            <div key={rule.title} className="blueprint home-rule">
              <Corners />
              <div className="home-rule-value">{rule.value}</div>
              <h3 className="home-rule-title">{rule.title}</h3>
              <p className="home-rule-body">{rule.body}</p>
            </div>
          ))}
        </div>
        <p className="home-rules-note">
          Default values follow the labor rules documented for the project and can be changed per
          run for what-if scenarios. The schedule shown above is sample data and has not been
          through a validation pass.
        </p>
      </div>
    </section>
  );
}
