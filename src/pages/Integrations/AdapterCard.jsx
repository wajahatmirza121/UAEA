import { Check, X, Activity, Loader2 } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { ADAPTER_INTERFACE } from "@/mocks";

function StatusBadge({ status }) {
  if (status === "healthy") return <Badge tone="jade">Healthy</Badge>;
  if (status === "degraded") return <Badge tone="amber">Degraded</Badge>;
  if (status === "planned") return <Badge tone="grey">Planned</Badge>;
  return <Badge tone="grey">Not configured</Badge>;
}

/**
 * One adapter implementation.
 *
 * The method list is the point: it shows at a glance how much of the
 * StudentSystemAdapter interface each implementation actually covers, so
 * "we have CMS access now" can be checked rather than assumed.
 */
export default function AdapterCard({ adapter, mayWrite, checking, onActivate, onCheck }) {
  return (
    <div className="ua-card" style={{ borderColor: adapter.active ? "var(--brass-line)" : undefined }}>
      <div className="ua-card-h">
        <div>
          <h3 style={{ fontFamily: "ui-monospace, Menlo, monospace" }}>{adapter.name}</h3>
          <p>
            {adapter.target} · {adapter.phase}
          </p>
        </div>
        <div style={{ display: "flex", gap: 7, alignItems: "center" }}>
          {adapter.active && <Badge tone="brass">Active</Badge>}
          <StatusBadge status={adapter.status} />
        </div>
      </div>

      <div style={{ padding: 17, display: "grid", gap: 13 }}>
        <p style={{ margin: 0, fontSize: 12.5, color: "var(--t2)", lineHeight: 1.65 }}>
          {adapter.note}
        </p>

        <div style={{ display: "grid", gap: 6 }}>
          {ADAPTER_INTERFACE.map((m) => {
            const done = adapter.implemented.includes(m.method);
            return (
              <div
                key={m.method}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 9,
                  fontSize: 12,
                  fontFamily: "ui-monospace, Menlo, monospace",
                  color: done ? "var(--t1)" : "var(--t3)",
                }}
              >
                {done ? (
                  <Check size={13} color="var(--jade)" style={{ flex: "0 0 13px" }} />
                ) : (
                  <X size={13} color="var(--t3)" style={{ flex: "0 0 13px" }} />
                )}
                <span style={{ flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis" }}>
                  {m.method}({m.args})
                </span>
              </div>
            );
          })}
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <Button
            size="sm"
            icon={checking ? Loader2 : Activity}
            loading={checking}
            onClick={() => onCheck(adapter)}
            disabled={adapter.status === "planned"}
          >
            Health check
          </Button>

          {mayWrite && !adapter.active && adapter.implemented.length > 0 && (
            <Button size="sm" variant="primary" onClick={() => onActivate(adapter)}>
              Make active
            </Button>
          )}

          {adapter.latency !== null && adapter.latency !== undefined && (
            <span className="ua-num" style={{ fontSize: 11.5, color: "var(--t3)" }}>
              last response {adapter.latency} ms
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
