import { useState } from "react";
import { Plug } from "lucide-react";
import AdapterCard from "./AdapterCard";
import Note from "@/components/ui/Note";
import ReadOnlyNotice from "@/components/ui/ReadOnlyNotice";
import { can } from "@/lib/rbac";
import { useApp } from "@/context/AppContext";
import { useToast } from "@/context/ToastContext";

/**
 * Integration adapters (§4.5, §15).
 *
 * The doc calls this the most future-proofing decision in the architecture:
 * the orchestrator, the flow state machines and the UI all talk to the
 * StudentSystemAdapter interface, never to CMS or OAS directly. Phase 1 ships
 * against the mock so the flows can be built without waiting on University IT.
 */
export default function Integrations() {
  const { store, mutate, role } = useApp();
  const toast = useToast();
  const [checking, setChecking] = useState(null);

  const mayWrite = can(role, "integrations.write");
  const adapters = store.adapters;
  const active = adapters.find((a) => a.active);

  // ↯ API SEAM — GET /v1/admin/integrations/{id}/health
  const runCheck = (adapter) => {
    setChecking(adapter.id);
    setTimeout(() => {
      setChecking(null);
      if (adapter.status === "not_configured") {
        toast(
          "No credentials configured",
          `${adapter.name} has no endpoint or service account yet.`,
          "rose"
        );
      } else {
        toast("Adapter healthy", `${adapter.name} responded in ${adapter.latency || 4} ms.`);
      }
    }, 900);
  };

  // ↯ API SEAM — PUT /v1/admin/integrations/active
  const activate = (adapter) => {
    adapters.forEach((a) => {
      if (a.active && a.id !== adapter.id) mutate("adapters", a.id, { active: false });
    });
    mutate("adapters", adapter.id, { active: true }, {
      action: "update",
      record: "Active adapter",
      changes: [{ field: "Adapter", from: active?.name || "—", to: adapter.name }],
    });
    toast("Adapter switched", `Live traffic now routes through ${adapter.name}.`);
  };

  return (
    <div className="ua-page">
      <div className="ua-head">
        <div>
          <h1 className="ua-h1">Integrations</h1>
          <p className="ua-sub">
            Nothing in the orchestrator, the flows or this console talks to University systems
            directly. Everything goes through one interface, so swapping the mock for a real API is
            one implementation rather than a rewrite.
          </p>
        </div>
      </div>

      {!mayWrite && (
        <div className="ua-card" style={{ marginBottom: 14 }}>
          <ReadOnlyNotice role={role} />
        </div>
      )}

      <div style={{ marginBottom: 14 }}>
        <Note tone="brass" icon={Plug}>
          <b style={{ color: "var(--t1)" }}>{active?.name}</b> is handling live traffic. Phase 1 is
          designed to ship fully functional on the mock — the informational and guided-flow layers
          have zero dependency on University IT timelines.
        </Note>
      </div>

      <div className="ua-cols even">
        {adapters.map((a) => (
          <AdapterCard
            key={a.id}
            adapter={a}
            mayWrite={mayWrite}
            checking={checking === a.id}
            onCheck={runCheck}
            onActivate={activate}
          />
        ))}
      </div>
    </div>
  );
}
