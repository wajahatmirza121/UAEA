import { History, ShieldCheck, Pencil, Trash2 } from "lucide-react";
import { can } from "@/lib/rbac";

/** Row controls, filtered by role. History is visible to everyone. */
export default function RowActions({ role, record, onHistory, onVerify, onEdit, onDelete }) {
  return (
    <div className="ua-rowact">
      <button className="ua-mini" title="Change history" onClick={() => onHistory(record)}>
        <History size={14} />
      </button>

      {can(role, "content.verify") && (
        <button className="ua-mini" title="Mark verified" onClick={() => onVerify(record)}>
          <ShieldCheck size={14} />
        </button>
      )}

      {can(role, "content.write") && (
        <button className="ua-mini" title="Edit" onClick={() => onEdit(record)}>
          <Pencil size={14} />
        </button>
      )}

      {can(role, "content.delete") && (
        <button className="ua-mini danger" title="Delete" onClick={() => onDelete(record)}>
          <Trash2 size={14} />
        </button>
      )}
    </div>
  );
}
