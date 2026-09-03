import { useState } from "react";
import { Play, RotateCcw, Bot, User, Wrench } from "lucide-react";
import Drawer from "@/components/ui/Drawer";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import { STEP_TYPES } from "@/mocks";
import { useApp } from "@/context/AppContext";

/** Stand-in tool results so the walkthrough shows grounded values. */
const SAMPLE_RESULTS = {
  get_fee_tariff: "amount=28500 PKR · effective 2026-07-01 · Fee Circular A-26 §3.1",
  get_deadline: "2026-09-30 · Autumn 2026 · Admission Notice A-26/11",
  get_document_checklist: "4 items · CNIC (copy), previous degree (copy), 2 photographs, paid challan",
  get_department: "Regional Campus Rawalpindi · 051-4567890 · 08:30–16:00",
  get_eligibility: "eligible · Intermediate with 45% minimum",
  search_knowledge_base: "3 chunks · Prospectus 2026-27 §2.1",
  create_escalation_ticket: "ticket ESC-2212 created",
};

/**
 * Steps through a flow one state at a time, filling slots as it goes.
 *
 * The point is to make the state machine legible before it ships: you can see
 * exactly which slot is filled when, and where a lookup fires. Reading a step
 * list does not surface an out-of-order slot; walking it does.
 */
export default function FlowSimulator({ flow, open, onClose }) {
  const { urdu } = useApp();
  const [cursor, setCursor] = useState(-1);
  const [slots, setSlots] = useState({});

  const steps = flow?.steps || [];
  const done = cursor >= steps.length - 1;

  const reset = () => {
    setCursor(-1);
    setSlots({});
  };

  const advance = () => {
    const next = cursor + 1;
    const step = steps[next];
    if (!step) return;
    if (step.type === "ask" && step.slot) {
      setSlots((p) => ({ ...p, [step.slot]: `«${step.slot} from student»` }));
    }
    setCursor(next);
  };

  const played = steps.slice(0, cursor + 1);

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={`Walk through ${flow?.en || ""}`}
      desc="Step the state machine forward and watch the slots fill."
      footer={
        <>
          <Button variant="ghost" icon={RotateCcw} onClick={reset}>
            Reset
          </Button>
          <div style={{ flex: 1 }} />
          <Button variant="primary" icon={Play} onClick={advance} disabled={done}>
            {cursor < 0 ? "Start" : done ? "Finished" : "Next step"}
          </Button>
        </>
      }
    >
      <div style={{ padding: 20, display: "grid", gap: 12 }}>
        {Object.keys(slots).length > 0 && (
          <div
            style={{
              border: "1px solid var(--line)",
              borderRadius: 10,
              padding: "10px 12px",
              background: "var(--panel-2)",
            }}
          >
            <div style={{ fontSize: 11, color: "var(--t3)", marginBottom: 6 }}>Slots filled</div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {Object.keys(slots).map((s) => (
                <Badge key={s} tone="sky">
                  {s}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {played.length === 0 && (
          <p style={{ fontSize: 12.5, color: "var(--t3)", lineHeight: 1.65, margin: 0 }}>
            Nothing has run yet. Press start to move through the flow one state at a time, exactly
            as the orchestrator would.
          </p>
        )}

        {played.map((step) => {
          const meta = STEP_TYPES[step.type];

          if (step.type === "lookup") {
            return (
              <div key={step.id} className="ua-toolcall">
                <Wrench size={11} style={{ verticalAlign: -1, marginRight: 6 }} />
                <b>{step.tool}</b>({step.toolArgs})
                <span>{SAMPLE_RESULTS[step.tool] || "no sample result configured"}</span>
              </div>
            );
          }

          const text = urdu ? step.prompt_ur : step.prompt_en;

          return (
            <div key={step.id} style={{ display: "grid", gap: 5 }}>
              <span style={{ display: "flex", alignItems: "center", gap: 7 }}>
                <Badge tone={meta.tone}>{meta.label}</Badge>
                <span style={{ fontSize: 11.5, color: "var(--t3)" }}>{step.label}</span>
              </span>
              <div style={{ display: "flex", gap: 10 }}>
                <span
                  className="ua-icontile"
                  style={{
                    width: 26,
                    height: 26,
                    flex: "0 0 26px",
                    background: "var(--brass-soft)",
                    borderColor: "var(--brass-line)",
                  }}
                >
                  <Bot size={13} color="var(--brass)" />
                </span>
                <div className={`ua-bubble b${urdu ? " ur" : ""}`} style={{ maxWidth: "100%" }}>
                  {text || <span style={{ color: "var(--t3)" }}>No prompt written for this step.</span>}
                </div>
              </div>

              {step.type === "ask" && (
                <div style={{ display: "flex", gap: 10, flexDirection: "row-reverse" }}>
                  <span className="ua-icontile" style={{ width: 26, height: 26, flex: "0 0 26px" }}>
                    <User size={13} color="var(--t2)" />
                  </span>
                  <div className="ua-bubble u" style={{ color: "var(--t3)", fontStyle: "italic" }}>
                    student answers, {step.slot} is filled
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {done && played.length > 0 && (
          <div style={{ textAlign: "center", fontSize: 12, color: "var(--t3)", padding: "8px 0" }}>
            Flow complete. Every path ended without leaving the student waiting.
          </div>
        )}
      </div>
    </Drawer>
  );
}
