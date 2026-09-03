import { Wrench, ShieldCheck } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Ladder from "@/components/ui/Ladder";

/**
 * A real answer, shown in full including its receipts.
 *
 * This is the most persuasive thing on the page: not a claim that the
 * assistant is accurate, but a worked example of what accountability looks
 * like when it answers.
 */
export default function TrustStrip() {
  return (
    <section className="st-section" style={{ borderTop: "1px solid var(--line)" }}>
      <div className="st-wrap st-grid two" style={{ alignItems: "center", gap: 32 }}>
        <div>
          <p className="st-eyebrow">Why you can check it</p>
          <h2 className="st-h2">Every answer shows its receipts</h2>
          <p className="st-lede">
            A fee or a deadline is never paraphrased from memory. It is read from a specific record,
            and the answer names the circular it came from and the date a member of staff last
            confirmed it. If that date is old, you will be told.
          </p>
        </div>

        <div className="st-sample">
          <div className="q">Q — BS CS ki fees kitni hai autumn 2026 ke liye?</div>

          <div className="st-route" style={{ marginBottom: 11 }}>
            <span>
              Routed to <b>Fees &amp; Finance</b> · Directorate of Finance
            </span>
            <span className="st-conf">94% match</span>
          </div>

          <p style={{ margin: "0 0 11px", fontSize: 14.5, lineHeight: 1.65 }}>
            BS Computer Science ki fee Rs 28,500 hai. Ye rate 1 Jul 2026 se lagoo hai.
          </p>

          <div className="ua-toolcall" style={{ marginBottom: 11 }}>
            <Wrench size={11} style={{ verticalAlign: -1, marginRight: 6 }} />
            <b>get_fee_tariff</b>(program=&quot;BS Computer Science&quot;)
            <span>amount=28500 PKR · Fee Circular A-26 §3.1</span>
          </div>

          <div className="st-source">
            <Badge tone="grey">
              <ShieldCheck size={11} />
              Fee Circular A-26 §3.1
            </Badge>
            <Ladder verified="2026-08-24" />
            <span>last checked 24 Aug 2026</span>
          </div>
        </div>
      </div>
    </section>
  );
}
