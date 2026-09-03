import { Route, AlertTriangle } from "lucide-react";
import { CONFIDENCE_FLOOR } from "@/lib/classify";

/**
 * Shows where a question landed before the answer appears.
 *
 * This is deliberately visible rather than hidden plumbing. A student who can
 * see their fee question went to Finance can tell instantly when it has gone
 * somewhere wrong, which is far better than discovering it three replies later.
 */
export default function RoutingCard({ classification }) {
  const { label, category, department, confidence } = classification;
  const low = confidence < CONFIDENCE_FLOOR;

  return (
    <div
      className="st-route"
      style={
        low
          ? { background: "var(--amber-soft)", borderColor: "var(--amber-line)" }
          : undefined
      }
    >
      {low ? (
        <AlertTriangle size={14} color="var(--amber)" style={{ flex: "0 0 14px" }} />
      ) : (
        <Route size={14} color="var(--sky)" style={{ flex: "0 0 14px" }} />
      )}

      {low ? (
        <span>I am not confident what this is about.</span>
      ) : (
        <span>
          Looks like <b>{label}</b>
          {category && ` · ${category}`}
          {department && ` · handled by ${department.en}`}
        </span>
      )}

      <span className="st-conf">{Math.round(confidence * 100)}% match</span>
    </div>
  );
}
