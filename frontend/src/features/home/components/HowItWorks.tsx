import { vi } from "../../../locales/vi";

const HOW = vi.home.how;

export function HowItWorks() {
  return (
    <section id="how" className="home-how">
      <div className="container">
        <div className="home-section-head">
          <div className="home-how-intro">
            <div className="home-eyebrow">{HOW.eyebrow}</div>
            <h2 className="home-how-title">{HOW.title}</h2>
          </div>
          <p className="home-how-note">{HOW.note}</p>
        </div>
        <div className="home-steps">
          {HOW.steps.map((step) => (
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
