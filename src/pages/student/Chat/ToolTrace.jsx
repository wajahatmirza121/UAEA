import { Wrench, ChevronDown } from "lucide-react";

/**
 * "How I found this" — the lookups behind an answer, collapsed by default.
 *
 * Most students will never open it. The ones who are about to pay Rs 44,000
 * on the strength of a chatbot reply deserve to be able to.
 */
/** Backend tool calls carry objects; show them compactly. */
const fmtArgs = (args) =>
  Object.entries(args || {})
    .filter(([, v]) => v !== null && v !== undefined && v !== "")
    .map(([k, v]) => `${k}="${v}"`)
    .join(", ");

function fmtResult(r) {
  if (!r || typeof r !== "object") return String(r ?? "");
  if (r.otp_required) return `verification required · code sent to ${r.masked_phone || "WhatsApp"}`;
  if (r.error) return `no data · ${r.error}`;
  const src = r.source ? ` · ${r.source}` : "";
  const counts = ["events", "slots", "courses", "faculty", "hostels", "routes", "scholarships", "programs", "chunks"]
    .filter((k) => Array.isArray(r[k]))
    .map((k) => `${r[k].length} ${k}`);
  if (counts.length) return counts.join(" · ") + src;
  if (r.amount !== undefined) return `${r.program} · ${r.category} · Rs ${Number(r.amount).toLocaleString("en-PK")}${src}`;
  if (r.date) return `${r.service || ""} · ${r.date}${src}`;
  return (r.name_en || r.name || r.service || "result") + src;
}

export default function ToolTrace({ toolCalls }) {
  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <details className="st-how">
      <summary>
        <ChevronDown size={13} />
        How I found this — {toolCalls.length} lookup{toolCalls.length > 1 ? "s" : ""}
      </summary>
      <div className="st-how-body">
        {toolCalls.map((c, i) => (
          <div key={i} className="ua-toolcall">
            <Wrench size={11} style={{ verticalAlign: -1, marginRight: 6 }} />
            <b>{c.name}</b>({typeof c.args === "string" ? c.args : fmtArgs(c.args)})
            <span>{typeof c.result === "string" ? c.result : fmtResult(c.result)}</span>
          </div>
        ))}
      </div>
    </details>
  );
}
