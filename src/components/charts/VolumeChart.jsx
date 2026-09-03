import { useState } from "react";
import { smoothPath } from "./smoothPath";
import { nfmt } from "@/lib/format";

/**
 * Two-series area chart with a crosshair readout.
 *
 * Painted through CSS classes rather than hex attributes so it re-themes with
 * the rest of the console. The dashed line is WhatsApp alone, under the total,
 * because the useful question is how much of the load one channel carries.
 */
export default function VolumeChart({ data, animate }) {
  const [hover, setHover] = useState(null);

  const W = 760;
  const H = 210;
  const PL = 42;
  const PR = 10;
  const PT = 14;
  const PB = 24;
  const iw = W - PL - PR;
  const ih = H - PT - PB;

  const max = Math.max(...data.map((d) => d.wa + d.web)) * 1.08;
  const x = (i) => PL + (i / (data.length - 1)) * iw;
  const y = (v) => PT + ih - (v / max) * ih;

  const totalPts = data.map((d, i) => [x(i), y(d.wa + d.web)]);
  const waPts = data.map((d, i) => [x(i), y(d.wa)]);
  const areaD = `${smoothPath(totalPts)} L ${x(data.length - 1)} ${PT + ih} L ${PL} ${PT + ih} Z`;

  const onMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * W;
    const i = Math.round(((px - PL) / iw) * (data.length - 1));
    setHover(i >= 0 && i < data.length ? i : null);
  };

  return (
    <div style={{ position: "relative" }}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        style={{ width: "100%", display: "block" }}
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
        role="img"
        aria-label="Daily conversation volume by channel"
      >
        <defs>
          <linearGradient id="ua-volume-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" className="ch-g0" />
            <stop offset="100%" className="ch-g1" />
          </linearGradient>
        </defs>

        {[0, 0.5, 1].map((t, i) => {
          const v = Math.round(max * t);
          const yy = y(v);
          return (
            <g key={i}>
              <line className="ch-grid" x1={PL} x2={W - PR} y1={yy} y2={yy} />
              <text className="ch-txt" x={PL - 8} y={yy + 3.5} textAnchor="end" fontSize="9.5">
                {nfmt(v)}
              </text>
            </g>
          );
        })}

        <path d={areaD} fill="url(#ua-volume-fill)" />
        <path
          className={`ch-total${animate ? " ua-drawpath" : ""}`}
          d={smoothPath(totalPts)}
          fill="none"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <path
          className="ch-wa"
          d={smoothPath(waPts)}
          fill="none"
          strokeWidth="1.5"
          strokeDasharray="3 3"
          opacity="0.85"
        />

        {hover !== null && (
          <g>
            <line className="ch-cross" x1={x(hover)} x2={x(hover)} y1={PT} y2={PT + ih} />
            <circle
              className="ch-dot-total"
              cx={x(hover)}
              cy={y(data[hover].wa + data[hover].web)}
              r="3.5"
              strokeWidth="2"
            />
            <circle className="ch-dot-wa" cx={x(hover)} cy={y(data[hover].wa)} r="3" strokeWidth="2" />
          </g>
        )}

        <text className="ch-txt" x={PL} y={H - 6} fontSize="9.5">
          {data.length} days ago
        </text>
        <text className="ch-txt" x={W - PR} y={H - 6} fontSize="9.5" textAnchor="end">
          today
        </text>
      </svg>

      {hover !== null && (
        <div
          className="ua-tooltip"
          style={{
            top: 6,
            left: `${(hover / (data.length - 1)) * 88 + 6}%`,
            transform: "translateX(-50%)",
          }}
        >
          <div className="ua-num" style={{ fontWeight: 600, marginBottom: 3 }}>
            {nfmt(data[hover].wa + data[hover].web)} conversations
          </div>
          <div className="ua-num" style={{ color: "var(--t2)" }}>
            WhatsApp {nfmt(data[hover].wa)} · Web {nfmt(data[hover].web)}
          </div>
        </div>
      )}
    </div>
  );
}
