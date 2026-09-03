/**
 * Role-based access control (§9 of the architecture doc).
 *
 * IMPORTANT: this gates the UI only. Hiding a delete button is a courtesy,
 * not a security control. The Phase 2 API must enforce this same PERMS map
 * server-side on every endpoint — the shape below is deliberately the shape
 * the middleware should use.
 */

export const ROLES = {
  super_admin: {
    label: "Super admin",
    note: "Full access, including guardrails and roles",
  },
  content_editor: {
    label: "Content editor",
    note: "Add, edit and verify catalogue records",
  },
  analytics_viewer: {
    label: "Analytics viewer",
    note: "Read-only across dashboards and logs",
  },
};

export const PERMS = {
  super_admin: [
    "content.write",
    "content.verify",
    "content.delete",
    "documents.write",
    "queue.write",
    "escalations.write",
    "flows.write",
    "integrations.write",
    "guardrails.write",
    "audit.read",
  ],
  content_editor: [
    "content.write",
    "content.verify",
    "documents.write",
    "queue.write",
    "escalations.write",
    "flows.write",
    "audit.read",
  ],
  analytics_viewer: ["audit.read"],
};

export const can = (role, perm) => (PERMS[role] || []).includes(perm);
