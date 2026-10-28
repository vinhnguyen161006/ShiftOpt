const STEPS = [
  {
    num: "01",
    title: "Define Demand",
    body: "Enter hourly demand in a 7 x 24 grid, import a CSV, or generate a profile from a supported data source.",
  },
  {
    num: "02",
    title: "Configure Workforce",
    body: "Add employees, shift templates and the labor-rule parameters that apply to this run.",
  },
  {
    num: "03",
    title: "Run Optimization",
    body: "Submit the instance, then watch solver status, gap and wall time as the job returns.",
  },
  {
    num: "04",
    title: "Analyze Results",
    body: "Review the roster, coverage, cost breakdown, validator findings and sensitivity scenarios.",
  },
];

export function HowItWorks() {
  return (
    <section id="how" className="home-how">
      <div className="container">
        <div className="home-section-head">
          <div className="home-how-intro">
            <div className="home-eyebrow">How it works</div>
            <h2 className="home-how-title">Four steps from raw demand to a reviewed schedule</h2>
          </div>
          <p className="home-how-note">
            Each run is immutable: inputs, parameters, solver version and seed are stored with the
            result.
          </p>
        </div>
        <div className="home-steps">
          {STEPS.map((step) => (
            <div key={step.num} className="home-step">
              <div className="home-step-accent" />
              <div className="home-step-num">{step.num}</div>
              <h3 className="home-step-title">{step.title}</h3>
              <p className="home-step-body">{step.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
