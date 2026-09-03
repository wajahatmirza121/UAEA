/**
 * Integration adapter registry (§4.5, §15).
 *
 * The doc calls this the most future-proofing decision in the architecture:
 * the orchestrator, the flow state machines and the UI all talk to the
 * StudentSystemAdapter interface, never to CMS/OAS/LMS directly. Phase 1
 * ships against MockAdapter so the flows can be built and tested without
 * waiting on University IT.
 */
export const ADAPTER_INTERFACE = [
  { method: "getFeeStatus", args: "rollNumber", returns: "FeeStatus" },
  { method: "getResult", args: "rollNumber, semester", returns: "Result" },
  { method: "getAssignmentStatus", args: "rollNumber, course", returns: "AssignmentStatus" },
  { method: "submitServiceRequest", args: "type, payload", returns: "RequestReceipt" },
  { method: "trackRequest", args: "requestId", returns: "RequestStatus" },
];

export const ADAPTERS = [
  {
    id: "mock",
    name: "MockAdapter",
    target: "In-memory fixtures",
    phase: "Phase 1",
    active: true,
    status: "healthy",
    latency: 4,
    implemented: ["getFeeStatus", "getResult", "getAssignmentStatus", "submitServiceRequest", "trackRequest"],
    note: "Returns canned data so conversational flows can be built and tested end to end with zero dependency on University IT timelines.",
  },
  {
    id: "cms",
    name: "CmsApiAdapter",
    target: "University CMS",
    phase: "Phase 2",
    active: false,
    status: "not_configured",
    latency: null,
    implemented: [],
    note: "Awaiting API credentials and a scoped service account. Read-only to begin with: fee status and result status only.",
  },
  {
    id: "oas",
    name: "OasApiAdapter",
    target: "Online Admission System",
    phase: "Phase 2",
    active: false,
    status: "not_configured",
    latency: null,
    implemented: [],
    note: "No published API yet. An RPA bridge behind the same interface is the fallback if access is not granted.",
  },
  {
    id: "lms",
    name: "LmsAdapter",
    target: "Learning Management System",
    phase: "Phase 3",
    active: false,
    status: "planned",
    latency: null,
    implemented: [],
    note: "Assignment status and e-content access. Not scoped until the informational layer has proven accuracy in the pilot.",
  },
];
