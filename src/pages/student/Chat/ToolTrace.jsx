import { Wrench, ChevronDown } from "lucide-react";

/**
 * "How I found this" — the lookups behind an answer, collapsed by default.
 *
 * Most students will never open it. The ones who are about to pay Rs 44,000
 * on the strength of a chatbot reply deserve to be able to.
 */
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
            <b>{c.name}</b>({c.args})
            <span>{c.result}</span>
          </div>
        ))}
      </div>
    </details>
  );
}
