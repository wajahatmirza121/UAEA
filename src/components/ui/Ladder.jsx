import { freshness } from "@/lib/freshness";

/**
 * The freshness ladder — the console's signature element.
 *
 * Four rungs that drain as a record ages away from its last human check.
 * Deliberately identical everywhere it appears so the decay reads the same
 * in a table row, a dashboard list and a history drawer.
 */
export default function Ladder({ verified, withText = true }) {
  const f = freshness(verified);

  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
      <span
        className="ua-ladder"
        title={`${f.label} · ${f.days} days since verification`}
        aria-label={`${f.label}, ${f.days} days since verification`}
      >
        {[1, 2, 3, 4].map((i) => (
          <i key={i} className={i <= f.rungs ? `f-${f.tone}` : ""} />
        ))}
      </span>
      {withText && (
        <span className="ua-num" style={{ fontSize: 12, color: "var(--t2)" }}>
          {f.days === 0 ? "today" : `${f.days}d`}
        </span>
      )}
    </span>
  );
}
