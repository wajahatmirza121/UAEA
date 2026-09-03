import Badge from "@/components/ui/Badge";
import { fmtDate, nfmt } from "@/lib/format";

/** Left pane: every journey with a state machine behind it. */
export default function FlowList({ flows, selectedId, onSelect }) {
  return (
    <div className="ua-card" style={{ alignSelf: "start", overflow: "hidden" }}>
      <div className="ua-card-h">
        <div>
          <h3>Flows</h3>
          <p className="ua-num">
            {flows.filter((f) => f.status === "live").length} live ·{" "}
            {flows.filter((f) => f.status === "draft").length} draft
          </p>
        </div>
      </div>

      <div className="ua-list">
        {flows.map((f) => (
          <button
            key={f.id}
            className={`ua-listitem${selectedId === f.id ? " on" : ""}`}
            onClick={() => onSelect(f.id)}
          >
            <span style={{ flex: 1, minWidth: 0 }}>
              <span style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 3 }}>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{f.en}</span>
                {f.status === "live" ? (
                  <Badge tone="jade">Live</Badge>
                ) : (
                  <Badge tone="amber">Draft</Badge>
                )}
              </span>
              <span className="ur" style={{ fontSize: 12, color: "var(--t3)", display: "block" }}>
                {f.ur}
              </span>
              <span
                className="ua-num"
                style={{ fontSize: 11.5, color: "var(--t3)", display: "block", marginTop: 3 }}
              >
                {f.steps.length} steps ·{" "}
                {f.completions ? `${nfmt(f.completions)} completions` : "not yet live"} · updated{" "}
                {fmtDate(f.updated)}
              </span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
