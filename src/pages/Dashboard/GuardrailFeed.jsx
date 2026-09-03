import { AlertTriangle, ShieldCheck, Check } from "lucide-react";
import { GUARDRAIL_EVENTS } from "@/mocks";

const ICONS = { rose: AlertTriangle, amber: ShieldCheck, sky: Check };

/**
 * What the safety layer stopped before it reached a student (§4.3.5).
 * Worth its space on the dashboard: a rising count of ungrounded numbers is
 * the earliest signal that a source document has drifted from the catalogue.
 */
export default function GuardrailFeed() {
  return (
    <div className="ua-card">
      <div className="ua-card-h">
        <div>
          <h3>Guardrail activity</h3>
          <p>What the safety layer stopped before it reached a student</p>
        </div>
      </div>

      <div className="ua-list">
        {GUARDRAIL_EVENTS.map((g) => {
          const Icon = ICONS[g.tone] || Check;
          return (
            <div key={g.id} className="ua-listitem">
              <span
                className="ua-icontile"
                style={{ background: `var(--${g.tone}-soft)`, borderColor: `var(--${g.tone}-line)` }}
              >
                <Icon size={13} color={`var(--${g.tone})`} />
              </span>
              <span style={{ flex: 1, minWidth: 0 }}>
                <span style={{ fontSize: 12.5, display: "block", lineHeight: 1.5 }}>{g.text}</span>
                <span style={{ fontSize: 11, color: "var(--t3)" }}>
                  {g.conv} · {g.at}
                </span>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
