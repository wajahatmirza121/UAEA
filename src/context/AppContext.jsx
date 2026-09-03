import { createContext, useContext, useState, useCallback } from "react";
import {
  SERVICES,
  FEES,
  DEADLINES,
  DEPARTMENTS,
  DOCUMENTS,
  FLOWS,
  ADAPTERS,
  AUDIT_SEED,
} from "@/mocks";
import { CURRENT_USER, ISO_TODAY } from "@/lib/constants";
import { ROLES } from "@/lib/rbac";
import { auditStamp } from "@/lib/format";

const AppContext = createContext(null);

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside <AppProvider>");
  return ctx;
}

/**
 * Single source of state for the console.
 *
 * ┌──────────────────────────────────────────────────────────────────┐
 * │  ↯ API SEAM                                                      │
 * │  Phase 2 replaces `store` with server state and rewrites         │
 * │  mutate() to issue fetch calls. Nothing else in the tree         │
 * │  touches data directly, so no page or component changes.         │
 * └──────────────────────────────────────────────────────────────────┘
 */
export function AppProvider({ children }) {
  const [theme, setTheme] = useState("light");
  const [role, setRole] = useState("super_admin");
  const [urdu, setUrdu] = useState(false);

  const [store, setStore] = useState({
    services: SERVICES,
    fees: FEES,
    deadlines: DEADLINES,
    departments: DEPARTMENTS,
    documents: DOCUMENTS,
    flows: FLOWS,
    adapters: ADAPTERS,
  });

  const [audit, setAudit] = useState(AUDIT_SEED);

  /** Append-only. There is deliberately no removeAuditEntry. */
  const logAudit = useCallback(
    (entry) => {
      setAudit((prev) => [
        {
          id: `a-${Date.now()}`,
          at: auditStamp(),
          actor: CURRENT_USER.name,
          role: ROLES[role].label,
          changes: [],
          ...entry,
        },
        ...prev,
      ]);
    },
    [role]
  );

  /**
   * ↯ API SEAM — the one function Phase 2 rewrites.
   *
   *   mutate(table, id, patch, meta)
   *     id === null      create        → POST   /v1/admin/content/{table}
   *     patch === null   delete        → DELETE /v1/admin/content/{table}/{id}
   *     otherwise        update        → PATCH  /v1/admin/content/{table}/{id}
   *
   *   meta = { action, record, changes } feeds the audit trail (§9).
   */
  const mutate = useCallback(
    (table, id, patch, meta) => {
      setStore((prev) => {
        const rows = prev[table] || [];
        if (id === null) {
          return { ...prev, [table]: [{ ...patch, id: `${table}-${Date.now()}` }, ...rows] };
        }
        if (patch === null) {
          return { ...prev, [table]: rows.filter((r) => r.id !== id) };
        }
        return { ...prev, [table]: rows.map((r) => (r.id === id ? { ...r, ...patch } : r)) };
      });

      if (meta) {
        logAudit({
          action: meta.action,
          table,
          recordId: id || `${table}-new`,
          record: meta.record,
          changes: meta.changes || [],
        });
      }
    },
    [logAudit]
  );

  /** Marks a record checked today under the signed-in name. */
  const verifyRecord = useCallback(
    (table, record, nameOf) => {
      mutate(
        table,
        record.id,
        { verified: ISO_TODAY, by: CURRENT_USER.name },
        { action: "verify", record: nameOf(record), changes: [] }
      );
    },
    [mutate]
  );

  const value = {
    theme,
    setTheme,
    role,
    setRole,
    urdu,
    setUrdu,
    store,
    mutate,
    verifyRecord,
    audit,
    logAudit,
    user: CURRENT_USER,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
