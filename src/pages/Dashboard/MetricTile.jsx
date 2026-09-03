import { TrendingUp, TrendingDown } from "lucide-react";
import { useCountUp } from "@/hooks/useCountUp";
import { useApp } from "@/context/AppContext";

/** One success metric (§13), counting up once on mount. */
export default function MetricTile({ metric, icon: Icon, run }) {
  const { urdu } = useApp();
  const value = useCountUp(metric.value, run);
  const up = metric.delta > 0;

  return (
    <div className="ua-metric">
      <div className="k">
        <Icon size={13} color="var(--t3)" />
        <span className={urdu ? "ur" : ""}>{urdu ? metric.ur : metric.label}</span>
      </div>

      <div className="v">
        {metric.unit === "%" ? value.toFixed(1) : Math.round(value).toLocaleString()}
        {metric.unit && <em>{metric.unit}</em>}
      </div>

      <div className="f">
        <span style={{ fontSize: 11.5, color: "var(--t3)" }}>{metric.note}</span>
        <span className={`ua-delta ${up ? "up" : "dn"}`}>
          {up ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {Math.abs(metric.delta)}%
        </span>
      </div>
    </div>
  );
}
