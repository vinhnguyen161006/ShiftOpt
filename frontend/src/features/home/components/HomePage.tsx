import "../home.css";
import { Analytics } from "./Analytics";
import { CallToAction } from "./CallToAction";
import { Features, ProductStrip } from "./Features";
import { Hero } from "./Hero";
import { HowItWorks } from "./HowItWorks";
import { Rules } from "./Rules";
import { SiteFooter } from "./SiteFooter";
import { SiteHeader } from "./SiteHeader";

export function HomePage() {
  return (
    <div className="home">
      <SiteHeader />
      <Hero />
      <ProductStrip />
      <Features />
      <HowItWorks />
      <Analytics />
      <Rules />
      <CallToAction />
      <SiteFooter />
    </div>
  );
}
