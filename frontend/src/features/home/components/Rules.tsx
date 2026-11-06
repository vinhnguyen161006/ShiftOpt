import { Corners } from "../../../components/ui/Corners";
import { vi } from "../../../locales/vi";

const RULES = vi.home.rules;

export function Rules() {
  return (
    <section className="home-rules">
      <div className="container">
        <div className="home-section-head home-section-head-tight">
          <div className="home-rules-intro">
            <div className="home-eyebrow">{RULES.eyebrow}</div>
            <h2 className="home-how-title home-rules-title">{RULES.title}</h2>
            <p className="home-rules-lead">{RULES.lead}</p>
          </div>
        </div>
        <div className="home-rule-grid">
          {RULES.items.map((rule) => (
            <div key={rule.title} className="blueprint home-rule">
              <Corners />
              <div className="home-rule-value">{rule.value}</div>
              <h3 className="home-rule-title">{rule.title}</h3>
              <p className="home-rule-body">{rule.body}</p>
            </div>
          ))}
        </div>
        <p className="home-rules-note">{RULES.note}</p>
      </div>
    </section>
  );
}
