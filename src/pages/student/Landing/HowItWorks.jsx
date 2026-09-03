import { Route, Database, UserCheck } from "lucide-react";

/**
 * The trust model, said plainly.
 *
 * Students are right to be wary of a chatbot answering questions about their
 * degree. Rather than asking them to trust it, this explains the mechanism:
 * routed, looked up, or handed to a person.
 */
const STEPS = [
  {
    icon: Route,
    title: "Your question is routed",
    body: "It is matched to a department and a service first — fees to Finance, results to Examinations — so the answer comes from the right place.",
  },
  {
    icon: Database,
    title: "The answer is looked up",
    body: "Fees, dates and document lists are read from the University's records, never invented. You see the source and the date staff last checked it.",
  },
  {
    icon: UserCheck,
    title: "Or you get a person",
    body: "If something is not recorded, the assistant says so and gives you the right office, its number and its opening hours. It will not guess.",
  },
];

export default function HowItWorks() {
  return (
    <section className="st-section">
      <div className="st-wrap">
        <p className="st-eyebrow">How it works</p>
        <h2 className="st-h2">Three steps, and no guessing</h2>
        <p className="st-lede" style={{ marginBottom: 26 }}>
          A wrong answer about a fee or a deadline costs a student real money and a wasted trip.
          This is built so that cannot happen quietly.
        </p>

        <div className="st-grid three">
          {STEPS.map((s, i) => (
            <div key={s.title} className="st-card">
              <div className="st-step-n">{i + 1}</div>
              <span className="st-card-icon" style={{ marginBottom: 12 }}>
                <s.icon size={17} color="var(--brass)" />
              </span>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
