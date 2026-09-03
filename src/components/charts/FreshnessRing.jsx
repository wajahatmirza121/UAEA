/**
 * Donut showing how much of the catalogue a human has vouched for recently.
 * The centre figure is the verified share, because that is the number anyone
 * opening this page actually wants.
 */
export default function FreshnessRing({ buckets }) {
  const total = buckets.reduce((s, b) => s + b.n, 0) || 1;
  const R = 52;
  const C = 2 * Math.PI * R;
  let offset = 0;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 20, padding: 17, flexWrap: "wrap" }}>
      <svg viewBox="0 0 130 130" width="118" height="118" style={{ flex: "0 0 auto" }}>
        <circle className="ch-ring" cx="65" cy="65" r={R} fill="none" strokeWidth="13" />
        {buckets.map((b) => {
          const len = (b.n / total) * C;
          const arc = (
            <circle
              key={b.tone}
              className={`ch-ring-${b.tone}`}
              cx="65"
              cy="65"
              r={R}
              fill="none"
              strokeWidth="13"
              strokeDasharray={`${len} ${C - len}`}
              strokeDashoffset={-offset}
              transform="rotate(-90 65 65)"
              style={{ transition: "stroke-dasharray .7s cubic-bezier(.4,0,.2,1)" }}
            />
          );
          offset += len;
          return arc;
        })}
        <text className="ch-big" x="65" y="61" textAnchor="middle" fontSize="24" fontWeight="600">
          {Math.round((buckets[0].n / total) * 100)}%
        </text>
        <text className="ch-txt" x="65" y="78" textAnchor="middle" fontSize="9.5">
          verified
        </text>
      </svg>

      <div style={{ display: "grid", gap: 10, flex: 1, minWidth: 140 }}>
        {buckets.map((b) => (
          <div key={b.tone} style={{ display: "flex", alignItems: "center", gap: 9, fontSize: 12.5 }}>
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: 2,
                flex: "0 0 7px",
                background: `var(--${b.tone}-bright)`,
              }}
            />
            <span style={{ flex: 1, color: "var(--t2)" }}>{b.label}</span>
            <span className="ua-num" style={{ fontWeight: 500 }}>
              {b.n}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
