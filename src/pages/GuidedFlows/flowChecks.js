/**
 * Publishability checks for a flow.
 *
 * A flow that ends on an `ask` step leaves the student mid-conversation with
 * no answer and no human — which is exactly the failure §4.3.3 warns about.
 * These run live in the editor so a draft cannot be promoted while broken.
 */
export function checkFlow(flow) {
  const steps = flow.steps || [];
  const issues = [];

  if (steps.length === 0) {
    issues.push({ level: "error", text: "The flow has no steps." });
    return issues;
  }

  const last = steps[steps.length - 1];
  if (last.type !== "handoff" && last.type !== "confirm") {
    issues.push({
      level: "error",
      text: "The last step is not a confirm or hand-off, so the conversation ends without resolution.",
    });
  }

  if (!steps.some((s) => s.type === "handoff")) {
    issues.push({
      level: "error",
      text: "No hand-off step. Every guided flow must offer a human at the end.",
    });
  }

  const asks = steps.filter((s) => s.type === "ask");
  asks.forEach((s) => {
    if (!s.slot) {
      issues.push({ level: "error", text: `“${s.label}” asks a question but fills no slot.` });
    }
    if (!s.validation) {
      issues.push({ level: "warn", text: `“${s.label}” has no validation rule on its slot.` });
    }
  });

  // Slots must be collected before the lookup that consumes them.
  steps.forEach((step, i) => {
    if (step.type !== "lookup" || !step.toolArgs) return;
    asks.forEach((ask) => {
      if (!ask.slot) return;
      if (step.toolArgs.includes(ask.slot)) {
        const askIndex = steps.indexOf(ask);
        if (askIndex > i) {
          issues.push({
            level: "error",
            text: `“${step.label}” uses ${ask.slot} before it has been collected.`,
          });
        }
      }
    });
  });

  if (!steps.some((s) => s.type === "lookup" || s.type === "confirm")) {
    issues.push({
      level: "warn",
      text: "No tool call anywhere in the flow, so nothing it says will be grounded in the catalogue.",
    });
  }

  return issues;
}
