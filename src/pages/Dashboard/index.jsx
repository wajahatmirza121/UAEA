import { useState, useEffect } from "react";
import { Download, CheckCircle2, ShieldCheck, Sparkles, LifeBuoy } from "lucide-react";
import MetricTile from "./MetricTile";
import FreshnessPanel from "./FreshnessPanel";
import GuardrailFeed from "./GuardrailFeed";
import VolumeChart from "@/components/charts/VolumeChart";
import IntentBars from "@/components/charts/IntentBars";
import Button from "@/components/ui/Button";
import Skeleton from "@/components/ui/Skeleton";
import { VOLUME_90, INTENTS, METRICS } from "@/mocks";
import { exportCSV } from "@/lib/csv";
import { nfmt } from "@/lib/format";
import { useApp } from "@/context/AppContext";
import { useToast } from "@/context/ToastContext";

const METRIC_ICONS = {
  containment: CheckCircle2,
  accuracy: ShieldCheck,
  coverage: Sparkles,
  escalations: LifeBuoy,
};

export default function Dashboard() {
  const { urdu } = useApp();
  const toast = useToast();

  const [range, setRange] = useState(30);
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  // One orchestrated entrance for the whole page; everything after this
  // moves only in response to a click.
  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 60);
    return () => clearTimeout(t);
  }, []);

  // ↯ API SEAM — GET /v1/admin/analytics/overview?range=
  const changeRange = (r) => {
    setRange(r);
    setLoading(true);
    setTimeout(() => setLoading(false), 420);
  };

  const data = VOLUME_90.slice(-range);
  const total = data.reduce((s, d) => s + d.wa + d.web, 0);

  const onExport = () => {
    const ok = exportCSV(
      `uaea-volume-${range}d.csv`,
      [
        { label: "Day", value: (r) => r.day },
        { label: "WhatsApp", value: (r) => r.wa },
        { label: "Web", value: (r) => r.web },
      ],
      data.map((d, i) => ({ ...d, day: i + 1 }))
    );
    toast(
      ok ? "Export downloaded" : "Export blocked",
      ok
        ? `${range} days of volume saved as CSV.`
        : "Your browser blocked the download. Try again outside a sandboxed frame.",
      ok ? "jade" : "rose"
    );
  };

  return (
    <div className="ua-page">
      <div className="ua-head">
        <div>
          <h1 className={`ua-h1${urdu ? " ur" : ""}`}>{urdu ? "ڈیش بورڈ" : "Dashboard"}</h1>
          <p className="ua-sub">
            Autumn 2026 admissions are open. Volume is climbing and several records in the catalogue
            have not been checked since spring.
          </p>
        </div>

        <div style={{ display: "flex", gap: 9, alignItems: "center" }}>
          <div className="ua-tabs">
            {[7, 30, 90].map((r) => (
              <button
                key={r}
                className={`ua-tab${range === r ? " on" : ""}`}
                onClick={() => changeRange(r)}
              >
                {r} days
              </button>
            ))}
          </div>
          <Button icon={Download} onClick={onExport}>
            Export
          </Button>
        </div>
      </div>

      <div className="ua-metrics" style={{ marginBottom: 14 }}>
        {METRICS.map((m) => (
          <MetricTile key={m.key} metric={m} icon={METRIC_ICONS[m.key]} run={mounted && !loading} />
        ))}
      </div>

      <div className="ua-cols two" style={{ marginBottom: 14 }}>
        <div className="ua-card">
          <div className="ua-card-h">
            <div>
              <h3>Conversation volume</h3>
              <p className="ua-num">
                {nfmt(total)} conversations over {range} days
              </p>
            </div>
            <div style={{ display: "flex", gap: 13, fontSize: 11.5, color: "var(--t2)" }}>
              <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <i style={{ width: 12, height: 2, background: "var(--brass-bright)", borderRadius: 2 }} />
                Total
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <i style={{ width: 12, height: 2, background: "var(--sky-bright)", borderRadius: 2 }} />
                WhatsApp
              </span>
            </div>
          </div>
          <div style={{ padding: "14px 14px 4px" }}>
            {loading ? <Skeleton height={210} /> : <VolumeChart data={data} animate={mounted} />}
          </div>
        </div>

        <div className="ua-card">
          <div className="ua-card-h">
            <div>
              <h3>What students ask</h3>
              <p>Top intents this period</p>
            </div>
          </div>
          {loading ? (
            <div style={{ padding: 17 }}>
              <Skeleton height={22} rows={6} gap={15} />
            </div>
          ) : (
            <IntentBars items={INTENTS} urdu={urdu} />
          )}
        </div>
      </div>

      <div className="ua-cols two">
        <FreshnessPanel />
        <GuardrailFeed />
      </div>
    </div>
  );
}
