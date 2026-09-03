import { useState, useEffect } from "react";
import { Trash2 } from "lucide-react";
import Drawer from "@/components/ui/Drawer";
import Field from "@/components/ui/Field";
import Button from "@/components/ui/Button";
import Note from "@/components/ui/Note";
import { STEP_TYPES, TOOLS } from "@/mocks";

/**
 * Edit one step of a flow.
 *
 * Which fields appear depends on the step type, because an `ask` needs a slot
 * and a validation rule while a `lookup` needs a tool and its arguments, and
 * showing both to everyone is how flows end up half-configured.
 */
export default function StepEditor({ step, open, onClose, onSave, onDelete, mayWrite }) {
  const [draft, setDraft] = useState(step || {});

  useEffect(() => {
    if (open && step) setDraft(step);
  }, [open, step]);

  const set = (key) => (e) =>
    setDraft((p) => ({ ...p, [key]: e?.target ? e.target.value : e }));

  if (!step) return null;

  const meta = STEP_TYPES[draft.type] || {};

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={draft.label || "Step"}
      desc={meta.note}
      footer={
        mayWrite && (
          <>
            <Button variant="danger" icon={Trash2} onClick={() => onDelete(step.id)}>
              Remove step
            </Button>
            <div style={{ flex: 1 }} />
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="primary" onClick={() => onSave(draft)}>
              Save step
            </Button>
          </>
        )
      }
    >
      <div style={{ padding: 20, display: "grid", gap: 15 }}>
        <Field label="Step name" hint="shown in the canvas only">
          <input
            className="ua-input"
            value={draft.label || ""}
            onChange={set("label")}
            disabled={!mayWrite}
          />
        </Field>

        <Field label="Type">
          <select
            className="ua-select"
            value={draft.type}
            onChange={set("type")}
            disabled={!mayWrite}
          >
            {Object.entries(STEP_TYPES).map(([key, t]) => (
              <option key={key} value={key}>
                {t.label} — {t.note}
              </option>
            ))}
          </select>
        </Field>

        {draft.type === "ask" && (
          <>
            <Field label="Slot name" hint="the variable this fills">
              <input
                className="ua-input"
                placeholder="programme"
                value={draft.slot || ""}
                onChange={set("slot")}
                disabled={!mayWrite}
              />
            </Field>
            <Field label="Validation rule">
              <input
                className="ua-input"
                placeholder="must match a programme in the fee tariff"
                value={draft.validation || ""}
                onChange={set("validation")}
                disabled={!mayWrite}
              />
            </Field>
          </>
        )}

        {(draft.type === "lookup" || draft.type === "confirm") && (
          <>
            <Field label="Tool">
              <select
                className="ua-select"
                value={draft.tool || ""}
                onChange={set("tool")}
                disabled={!mayWrite}
              >
                <option value="">No tool</option>
                {TOOLS.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Arguments" hint="slot names or literals">
              <input
                className="ua-input"
                placeholder='service="Fee Challan"'
                value={draft.toolArgs || ""}
                onChange={set("toolArgs")}
                disabled={!mayWrite}
              />
            </Field>
          </>
        )}

        {draft.type !== "lookup" && (
          <div className="ua-grid2">
            <Field label="What it says in English">
              <textarea
                className="ua-textarea"
                value={draft.prompt_en || ""}
                onChange={set("prompt_en")}
                disabled={!mayWrite}
              />
            </Field>
            <Field label="What it says in Urdu">
              <textarea
                className="ua-textarea ur"
                value={draft.prompt_ur || ""}
                onChange={set("prompt_ur")}
                disabled={!mayWrite}
              />
            </Field>
          </div>
        )}

        {draft.type === "lookup" && (
          <Note tone="sky">
            Lookup steps produce no words of their own. The model may only state what the tool
            returned, which is the rule that keeps an invented fee out of the answer.
          </Note>
        )}
      </div>
    </Drawer>
  );
}
