import { ChevronUp, ChevronDown, Plus, AlertTriangle, Play, Wrench } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Note from "@/components/ui/Note";
import { STEP_TYPES } from "@/mocks";
import { checkFlow } from "./flowChecks";
import { nfmt } from "@/lib/format";

/**
 * The state machine itself, as an ordered list.
 *
 * Kept vertical and boringly linear on purpose. A node graph looks better in
 * a screenshot, but the person maintaining this needs to see the order a
 * student experiences, and order is what a list shows best.
 */
export default function FlowCanvas({
  flow,
  selectedStepId,
  onSelectStep,
  onMoveStep,
  onAddStep,
  onSimulate,
  onPublish,
  mayWrite,
}) {
  const issues = checkFlow(flow);
  const errors = issues.filter((i) => i.level === "error");

  return (
    <div className="ua-card" style={{ alignSelf: "start" }}>
      <div className="ua-card-h">
        <div>
          <h3>{flow.en}</h3>
          <p>
            intent {flow.intent} · {flow.steps.length} steps ·{" "}
            {flow.completions ? `${nfmt(flow.completions)} completions` : "not yet live"}
            {flow.dropOff ? ` · ${Math.round(flow.dropOff * 100)}% drop-off` : ""}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Button size="sm" icon={Play} onClick={onSimulate}>
            Walk through
          </Button>
          {mayWrite && flow.status === "draft" && (
            <Button
              size="sm"
              variant="primary"
              disabled={errors.length > 0}
              onClick={onPublish}
              title={errors.length > 0 ? "Fix the errors below first" : undefined}
            >
              Publish
            </Button>
          )}
        </div>
      </div>

      <div style={{ padding: 17, display: "grid", gap: 0 }}>
        {flow.steps.map((step, i) => {
          const meta = STEP_TYPES[step.type] || {};
          return (
            <div key={step.id}>
              <div style={{ display: "flex", gap: 8, alignItems: "stretch" }}>
                <button
                  className={`ua-step${selectedStepId === step.id ? " on" : ""}`}
                  onClick={() => onSelectStep(step)}
                >
                  <span className="ua-stepnum">{i + 1}</span>
                  <span style={{ flex: 1, minWidth: 0 }}>
                    <span
                      style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap", marginBottom: 3 }}
                    >
                      <span style={{ fontSize: 13, fontWeight: 500 }}>{step.label}</span>
                      <Badge tone={meta.tone}>{meta.label}</Badge>
                      {step.slot && <Badge tone="grey">{step.slot}</Badge>}
                    </span>

                    {step.tool && (
                      <span
                        style={{
                          fontSize: 11.5,
                          color: "var(--sky)",
                          display: "flex",
                          alignItems: "center",
                          gap: 5,
                          fontFamily: "ui-monospace, Menlo, monospace",
                        }}
                      >
                        <Wrench size={10} />
                        {step.tool}({step.toolArgs})
                      </span>
                    )}

                    {!step.tool && (step.prompt_en || step.prompt_ur) && (
                      <span
                        style={{
                          fontSize: 11.5,
                          color: "var(--t3)",
                          display: "block",
                          lineHeight: 1.5,
                        }}
                      >
                        {step.prompt_en || step.prompt_ur}
                      </span>
                    )}
                  </span>
                </button>

                {mayWrite && (
                  <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", gap: 2 }}>
                    <button
                      className="ua-mini"
                      onClick={() => onMoveStep(i, -1)}
                      disabled={i === 0}
                      aria-label="Move step up"
                      style={{ opacity: i === 0 ? 0.3 : 1 }}
                    >
                      <ChevronUp size={14} />
                    </button>
                    <button
                      className="ua-mini"
                      onClick={() => onMoveStep(i, 1)}
                      disabled={i === flow.steps.length - 1}
                      aria-label="Move step down"
                      style={{ opacity: i === flow.steps.length - 1 ? 0.3 : 1 }}
                    >
                      <ChevronDown size={14} />
                    </button>
                  </div>
                )}
              </div>

              {i < flow.steps.length - 1 && <div className="ua-stepline" />}
            </div>
          );
        })}

        {mayWrite && (
          <Button style={{ marginTop: 12, justifySelf: "start" }} icon={Plus} onClick={onAddStep}>
            Add step
          </Button>
        )}
      </div>

      {issues.length > 0 && (
        <div style={{ padding: "0 17px 17px", display: "grid", gap: 8 }}>
          {issues.map((issue, i) => (
            <Note key={i} tone={issue.level === "error" ? "rose" : "amber"} icon={AlertTriangle}>
              {issue.text}
            </Note>
          ))}
        </div>
      )}
    </div>
  );
}
