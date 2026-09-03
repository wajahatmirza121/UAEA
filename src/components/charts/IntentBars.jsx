import { nfmt } from "@/lib/format";

/** Ranked bars. Opacity steps down the list so rank reads without colour. */
export default function IntentBars({ items, urdu }) {
  const max = Math.max(...items.map((i) => i.n));
  const total = items.reduce((s, i) => s + i.n, 0);

  return (
    <div style={{ padding: "13px 17px 17px", display: "grid", gap: 11 }}>
      {items.map((it, idx) => (
        <div key={it.key}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "baseline",
              marginBottom: 5,
              gap: 10,
            }}
          >
            <span className={urdu ? "ur" : ""} style={{ fontSize: 12.5 }}>
              {urdu ? it.ur : it.label}
            </span>
            <span className="ua-num" style={{ fontSize: 11.5, color: "var(--t3)" }}>
              {nfmt(it.n)} · {((it.n / total) * 100).toFixed(1)}%
            </span>
          </div>
          <div
            style={{
              height: 5,
              background: "var(--hover-2)",
              borderRadius: 5,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${(it.n / max) * 100}%`,
                borderRadius: 5,
                background: "var(--brass-bright)",
                opacity: 1 - idx * 0.09,
                transition: "width .6s cubic-bezier(.4,0,.2,1)",
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
