import { Lock } from "lucide-react";
import { ROLES } from "@/lib/rbac";

/**
 * Shown wherever the current role cannot act.
 *
 * Says which role you are and how to get access, rather than silently
 * removing controls and leaving the person wondering where they went.
 */
export default function ReadOnlyNotice({ role }) {
  return (
    <div className="ua-readonly">
      <Lock size={14} />
      <span>
        You are signed in as {ROLES[role].label}. This page is read-only — ask a super admin for
        content access if you need to make changes.
      </span>
    </div>
  );
}
