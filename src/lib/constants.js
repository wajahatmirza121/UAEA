/**
 * Fixed points the whole console reads from.
 *
 * TODAY is pinned so the mock data tells a coherent story: Autumn 2026
 * admissions are open, some deadlines have passed, some records are stale.
 * Phase 2 replaces it with `new Date()`.
 */
export const TODAY = new Date("2026-09-01");
export const ISO_TODAY = "2026-09-01";

/** Replaced by the authenticated session in Phase 2. */
export const CURRENT_USER = {
  name: "Ayesha Tariq",
  initials: "AT",
  email: "a.tariq@uni.edu.pk",
};

/** Roughly how often each table is quoted, used for change-impact warnings. */
export const TABLE_IMPACT = {
  services: (r) => r?.queries || 900,
  fees: () => 6140,
  deadlines: () => 4820,
  departments: () => 1290,
};

export const TABLE_LABELS = {
  services: "Services",
  fees: "Fee tariff",
  deadlines: "Deadlines",
  departments: "Departments",
  documents: "Source documents",
  flows: "Guided flows",
  settings: "Guardrails",
};
