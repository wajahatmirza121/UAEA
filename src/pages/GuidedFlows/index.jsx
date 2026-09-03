import { useState } from "react";
import FlowList from "./FlowList";
import FlowCanvas from "./FlowCanvas";
import StepEditor from "./StepEditor";
import FlowSimulator from "./FlowSimulator";
import ReadOnlyNotice from "@/components/ui/ReadOnlyNotice";
import { checkFlow } from "./flowChecks";
import { can } from "@/lib/rbac";
import { ISO_TODAY, CURRENT_USER } from "@/lib/constants";
import { useApp } from "@/context/AppContext";
import { useToast } from "@/context/ToastContext";

/**
 * Guided flows (§4.3.3).
 *
 * The doc is explicit that multi-turn journeys must be explicit state
 * machines rather than LLM improvisation — that is what stops the assistant
 * skipping a required document or asking for the campus after it has already
 * answered. This is where those machines are edited, checked and walked.
 */
export default function GuidedFlows() {
  const { store, mutate, role } = useApp();
  const toast = useToast();

  const flows = store.flows;
  const [selectedId, setSelectedId] = useState(flows[0].id);
  const [editingStep, setEditingStep] = useState(null);
  const [simulating, setSimulating] = useState(false);

  const mayWrite = can(role, "flows.write");
  const flow = flows.find((f) => f.id === selectedId) || flows[0];

  // ↯ API SEAM — PATCH /v1/admin/flows/{id}
  const saveSteps = (steps, meta) => {
    mutate(
      "flows",
      flow.id,
      { steps, updated: ISO_TODAY, by: CURRENT_USER.name },
      { action: "update", record: flow.en, changes: meta }
    );
  };

  const moveStep = (index, delta) => {
    const target = index + delta;
    if (target < 0 || target >= flow.steps.length) return;
    const next = [...flow.steps];
    [next[index], next[target]] = [next[target], next[index]];
    saveSteps(next, [
      { field: "Step order", from: `${index + 1}`, to: `${target + 1}` },
    ]);
  };

  const addStep = () => {
    const step = {
      id: `s${Date.now()}`,
      type: "ask",
      label: "New step",
      slot: "",
      validation: "",
      prompt_en: "",
      prompt_ur: "",
    };
    saveSteps([...flow.steps, step], [{ field: "Steps", from: `${flow.steps.length}`, to: `${flow.steps.length + 1}` }]);
    setEditingStep(step);
  };

  const saveStep = (draft) => {
    const before = flow.steps.find((s) => s.id === draft.id) || {};
    const changes = Object.keys(draft)
      .filter((k) => k !== "id" && String(draft[k] ?? "") !== String(before[k] ?? ""))
      .map((k) => ({ field: k, from: String(before[k] ?? "—"), to: String(draft[k] ?? "—") }));

    saveSteps(
      flow.steps.map((s) => (s.id === draft.id ? draft : s)),
      changes
    );
    setEditingStep(null);
    toast("Step saved", "The flow updates for new conversations immediately.");
  };

  const deleteStep = (id) => {
    const removed = flow.steps.find((s) => s.id === id);
    saveSteps(
      flow.steps.filter((s) => s.id !== id),
      [{ field: "Removed step", from: removed?.label || id, to: "—" }]
    );
    setEditingStep(null);
    toast("Step removed", "Check the flow still ends in a hand-off.");
  };

  const publish = () => {
    const issues = checkFlow(flow).filter((i) => i.level === "error");
    if (issues.length > 0) {
      toast("Cannot publish", "Fix the errors listed under the flow first.", "rose");
      return;
    }
    // ↯ API SEAM — POST /v1/admin/flows/{id}/publish
    mutate(
      "flows",
      flow.id,
      { status: "live", updated: ISO_TODAY, by: CURRENT_USER.name },
      { action: "publish", record: flow.en, changes: [{ field: "Status", from: "draft", to: "live" }] }
    );
    toast("Flow published", `${flow.en} is now live on web and WhatsApp.`);
  };

  return (
    <div className="ua-page">
      <div className="ua-head">
        <div>
          <h1 className="ua-h1">Guided flows</h1>
          <p className="ua-sub">
            The top journeys run as explicit state machines rather than letting the model improvise
            the sequence. That is what stops it skipping a required document.
          </p>
        </div>
      </div>

      {!mayWrite && (
        <div className="ua-card" style={{ marginBottom: 14 }}>
          <ReadOnlyNotice role={role} />
        </div>
      )}

      <div className="ua-split">
        <FlowList flows={flows} selectedId={flow.id} onSelect={setSelectedId} />
        <FlowCanvas
          flow={flow}
          selectedStepId={editingStep?.id}
          onSelectStep={setEditingStep}
          onMoveStep={moveStep}
          onAddStep={addStep}
          onSimulate={() => setSimulating(true)}
          onPublish={publish}
          mayWrite={mayWrite}
        />
      </div>

      <StepEditor
        step={editingStep}
        open={Boolean(editingStep)}
        onClose={() => setEditingStep(null)}
        onSave={saveStep}
        onDelete={deleteStep}
        mayWrite={mayWrite}
      />

      <FlowSimulator flow={flow} open={simulating} onClose={() => setSimulating(false)} />
    </div>
  );
}
