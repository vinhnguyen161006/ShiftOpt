import { Link } from "react-router";
import { BrandMark, Wordmark } from "../../components/ui/BrandMark";
import { vi } from "../../locales/vi";

export function PrivacyRoute() {
  return (
    <article className="auth-page privacy-page" aria-labelledby="privacy-title">
      <Link to="/" className="brand auth-brand">
        <BrandMark />
        <Wordmark />
      </Link>
      <div className="auth-panel blueprint">
        <h1 id="privacy-title" className="auth-title">
          {vi.privacy.title}
        </h1>
        <p className="auth-lead">{vi.privacy.updated}</p>
        <p className="auth-lead">{vi.privacy.lead}</p>
        {vi.privacy.sections.map((section) => (
          <section key={section.heading}>
            <h2 className="panel-title">{section.heading}</h2>
            <p className="auth-lead">{section.body}</p>
          </section>
        ))}
        <Link to="/">{vi.privacy.back}</Link>
      </div>
    </article>
  );
}
