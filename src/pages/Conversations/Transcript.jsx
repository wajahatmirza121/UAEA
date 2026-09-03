import { Wrench, User, Bot } from "lucide-react";
import Badge from "@/components/ui/Badge";
import { isUrduText } from "@/lib/format";

export function OutcomeBadge({ outcome }) {
  if (outcome === "resolved") return <Badge tone="jade">Resolved</Badge>;
  if (outcome === "escalated") return <Badge tone="amber">Escalated</Badge>;
  return <Badge tone="rose">Unresolved</Badge>;
}

/**
 * Full transcript with the tool calls left in.
 *
 * This is the screen that makes the tool-grounding architecture visible: an
 * answer containing a fee or a date should always have a lookup directly
 * above it. One that does not is exactly what the guardrail layer exists to
 * catch, and this is where you would notice.
 */
export default function Transcript({ conversation }) {
  return (
    <div className="ua-card" style={{ alignSelf: "start" }}>
      <div className="ua-card-h">
        <div>
          <h3 className="ua-num">{conversation.id}</h3>
          <p>
            {conversation.channel === "whatsapp" ? "WhatsApp Business" : "Web chat widget"} ·{" "}
            {conversation.lang} · intent {conversation.intent}
          </p>
        </div>
        <OutcomeBadge outcome={conversation.outcome} />
      </div>

      <div style={{ padding: 17, display: "grid", gap: 12 }}>
        {conversation.messages.map((m, i) => {
          if (m.role === "tool") {
            return (
              <div key={i} className="ua-toolcall">
                <Wrench size={11} style={{ verticalAlign: -1, marginRight: 6 }} />
                <b>{m.name}</b>({m.args})
                <span>{m.result}</span>
              </div>
            );
          }

          if (m.role === "system") {
            return (
              <div
                key={i}
                style={{ textAlign: "center", fontSize: 11.5, color: "var(--t3)", padding: "5px 0" }}
              >
                {m.text}
              </div>
            );
          }

          const isUser = m.role === "user";
          return (
            <div
              key={i}
              style={{ display: "flex", gap: 10, flexDirection: isUser ? "row-reverse" : "row" }}
            >
              <span
                className="ua-icontile"
                style={{
                  width: 26,
                  height: 26,
                  flex: "0 0 26px",
                  background: isUser ? "var(--panel-2)" : "var(--brass-soft)",
                  borderColor: isUser ? "var(--line)" : "var(--brass-line)",
                }}
              >
                {isUser ? <User size={13} color="var(--t2)" /> : <Bot size={13} color="var(--brass)" />}
              </span>
              <div
                className={`ua-bubble ${isUser ? "u" : "b"}${isUrduText(m.text) ? " ur" : ""}`}
              >
                {m.text}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
