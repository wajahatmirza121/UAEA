/**
 * Barrel for the mock data layer.
 *
 * Phase 2 deletes this folder. Every consumer imports from "@/mocks", so the
 * swap to real fetches touches the context provider and nothing else.
 */
export { SERVICES } from "./services";
export { FEES } from "./fees";
export { DEADLINES } from "./deadlines";
export { DEPARTMENTS } from "./departments";
export { DOCUMENTS, RETRIEVAL_SAMPLE } from "./documents";
export { QUEUE } from "./queue";
export { CONVERSATIONS } from "./conversations";
export { ESCALATIONS } from "./escalations";
export { AUDIT_SEED } from "./audit";
export { FLOWS, STEP_TYPES, TOOLS } from "./flows";
export { ADAPTERS, ADAPTER_INTERFACE } from "./adapters";
export { VOLUME_90, INTENTS, METRICS, GUARDRAIL_EVENTS } from "./analytics";
