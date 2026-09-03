import Hero from "./Hero";
import DeadlineStrip from "./DeadlineStrip";
import HowItWorks from "./HowItWorks";
import CategoryGrid from "./CategoryGrid";
import TrustStrip from "./TrustStrip";

/**
 * Student landing page.
 *
 * Ordered by what someone arriving actually needs: a box to type in, the
 * dates they are probably worried about, then an explanation of why the
 * answers can be trusted — persuasion last, not first.
 */
export default function Landing() {
  return (
    <>
      <Hero />
      <DeadlineStrip />
      <HowItWorks />
      <CategoryGrid />
      <TrustStrip />
    </>
  );
}
