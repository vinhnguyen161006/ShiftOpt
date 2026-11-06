import { Link } from "react-router";
import { BrandMark, Wordmark } from "../../../components/ui/BrandMark";
import { Corners } from "../../../components/ui/Corners";
import { vi } from "../../../locales/vi";
import { WORKSPACE_LINKS } from "../links";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="container site-header-bar">
        <a href="#top" className="brand">
          <BrandMark />
          <Wordmark />
        </a>
        <Link className="btn btn-primary blueprint home-header-cta" to={WORKSPACE_LINKS.demand}>
          {vi.home.headerCta}
          <Corners />
        </Link>
      </div>
    </header>
  );
}
