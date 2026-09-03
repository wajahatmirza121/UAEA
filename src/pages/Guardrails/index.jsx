import { useState } from "react";
import { Languages } from "lucide-react";
import AnswerRules from "./AnswerRules";
import Button from "@/components/ui/Button";
import Field from "@/components/ui/Field";
import Note from "@/components/ui/Note";
import { can } from "@/lib/rbac";
import { useApp } from "@/context/AppContext";
import { useToast } from "@/context/ToastContext";

/**
 * The rules that decide when the assistant speaks and when it hands over.
 *
 * Every change here is written to the audit log alongside content changes,
 * because a threshold change is a policy change and §9 does not distinguish.
 */
export default function Guardrails() {
  const { role, logAudit } = useApp();
  const toast = useToast();

  const mayWrite = can(role, "guardrails.write");

  const [config, setConfig] = useState({
    blockUngrounded: true,
    requireCitation: true,
    blockPromises: true,
    blockAcademicDishonesty: true,
    blockUnauthenticated: true,
    showVerifiedDate: true,
  });

  const [threshold, setThreshold] = useState(65);
  const [savedThreshold, setSavedThreshold] = useState(65);
  const [model, setModel] = useState("claude-sonnet-4-6");
  const [savedModel, setSavedModel] = useState("claude-sonnet-4-6");
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  const setRule = (key, value) => {
    setConfig((p) => ({ ...p, [key]: value }));
    setDirty(true);
  };

  // ↯ API SEAM — PUT /v1/admin/guardrails
  const save = () => {
    setSaving(true);
    setTimeout(() => {
      const changes = [];
      if (threshold !== savedThreshold) {
        changes.push({ field: "Handover threshold", from: `${savedThreshold}%`, to: `${threshold}%` });
        setSavedThreshold(threshold);
      }
      if (model !== savedModel) {
        changes.push({ field: "Model", from: savedModel, to: model });
        setSavedModel(model);
      }

      logAudit({
        action: "guardrail",
        table: "settings",
        recordId: "cfg",
        record: "Guardrail configuration",
        changes: changes.length ? changes : [{ field: "Answer rules", from: "previous set", to: "updated" }],
      });

      setSaving(false);
      setDirty(false);
      toast("Guardrails saved", "Applied to new conversations immediately.");
    }, 700);
  };

  return (
    <div className="ua-page">
      <div className="ua-head">
        <div>
          <h1 className="ua-h1">Guardrails</h1>
          <p className="ua-sub">
            The rules that decide when the assistant speaks and when it hands over. Changes apply to
            new conversations right away and are written to the audit log.
          </p>
        </div>
        {mayWrite && (
          <Button variant="primary" disabled={!dirty} loading={saving} onClick={save}>
            {saving ? "Saving" : dirty ? "Save changes" : "Saved"}
          </Button>
        )}
      </div>

      <div className="ua-cols two">
        <AnswerRules config={config} onChange={setRule} mayWrite={mayWrite} role={role} />

        <div style={{ display: "grid", gap: 14, alignContent: "start" }}>
          <div className="ua-card">
            <div className="ua-card-h">
              <div>
                <h3>Handover threshold</h3>
                <p>Below this confidence, offer a human</p>
              </div>
            </div>
            <div style={{ padding: 17 }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 13 }}>
                <span className="ua-num" style={{ fontSize: 30, fontWeight: 600 }}>
                  {threshold}
                </span>
                <span style={{ color: "var(--t3)", fontSize: 13 }}>% confidence</span>
              </div>

              <input
                type="range"
                min="40"
                max="90"
                value={threshold}
                disabled={!mayWrite}
                style={{ width: "100%", accentColor: "var(--brass-bright)" }}
                onChange={(e) => {
                  setThreshold(Number(e.target.value));
                  setDirty(true);
                }}
                aria-label="Handover confidence threshold"
              />

              <p style={{ fontSize: 12, color: "var(--t3)", marginTop: 11, lineHeight: 1.6 }}>
                At {threshold}%, roughly {Math.round((100 - threshold) * 3.4)} conversations a day
                would reach a staff member. Raising it protects accuracy; lowering it protects your
                team&apos;s time.
              </p>
            </div>
          </div>

          <div className="ua-card">
            <div className="ua-card-h">
              <div>
                <h3>Model</h3>
                <p>Conversational layer only — facts come from the catalogue</p>
              </div>
            </div>
            <div style={{ padding: 17, display: "grid", gap: 13 }}>
              <Field label="Active model">
                <select
                  className="ua-select"
                  value={model}
                  disabled={!mayWrite}
                  onChange={(e) => {
                    setModel(e.target.value);
                    setDirty(true);
                  }}
                >
                  <option value="claude-sonnet-4-6">Claude Sonnet 4.6</option>
                  <option value="claude-opus-5">Claude Opus 5</option>
                  <option value="claude-haiku-4-5">Claude Haiku 4.5</option>
                </select>
              </Field>

              <Note tone="sky" icon={Languages}>
                Roman Urdu intent accuracy is measured separately from chat fluency. Current eval
                set: <span className="ua-num">1,240</span> labelled queries, last run 28 August 2026.
              </Note>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
