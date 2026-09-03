import { Trash2, AlertTriangle } from "lucide-react";
import Modal from "@/components/ui/Modal";
import Button from "@/components/ui/Button";
import Note from "@/components/ui/Note";
import { fmtDate, nfmt } from "@/lib/format";
import { TABLE_IMPACT } from "@/lib/constants";
import { nameOf } from "./columns";

/**
 * Delete confirmation.
 *
 * States the consequence in students rather than in rows: removing a record
 * does not just empty a table, it sends every conversation that depended on
 * it to a human.
 */
export default function DeleteRecordModal({ record, tab, onClose, onConfirm }) {
  return (
    <Modal
      open={Boolean(record)}
      onClose={onClose}
      title="Delete this record?"
      desc="The assistant will stop answering questions that depend on it and will offer a human handoff instead."
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Keep it
          </Button>
          <Button variant="danger" icon={Trash2} onClick={onConfirm}>
            Delete record
          </Button>
        </>
      }
    >
      {record && (
        <>
          <div style={{ fontSize: 13, color: "var(--t2)", lineHeight: 1.65 }}>
            <b style={{ color: "var(--t1)" }}>{nameOf(record)}</b> was last verified by {record.by}{" "}
            on {fmtDate(record.verified)}.
          </div>
          <Note tone="rose" icon={AlertTriangle}>
            Students asked about this roughly {nfmt(TABLE_IMPACT[tab](record))} times in the last 90
            days. Deleting it sends every one of those conversations to a human.
          </Note>
        </>
      )}
    </Modal>
  );
}
