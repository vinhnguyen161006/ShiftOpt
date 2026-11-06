import "../home.css";
import { Hero } from "./Hero";
import { SiteFooter } from "./SiteFooter";
import { SiteHeader } from "./SiteHeader";

export function HomePage() {
  return (
    <div className="home">
      <SiteHeader />
      <Hero />
      <SiteFooter />
    </div>
  );
}
