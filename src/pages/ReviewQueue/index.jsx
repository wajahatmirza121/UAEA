import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import QueueList from "./QueueList";
import QueueDetail from "./QueueDetail";
import EmptyState from "@/components/ui/EmptyState";
import { QUEUE } from "@/mocks";
import { can } from "@/lib/rbac";
import { useApp } from "@/context/AppContext";
import { useToast } from "@/context/ToastContext";

const FILTERS = [
  ["all", "All"],
  ["roman", "Roman Urdu"],
  ["urdu", "Urdu script"],
];

/**
 * Questions the assistant could not answer confidently — the content growth
 * loop from §4.6. Each row is a gap in the catalogue that a real student
 * walked into.
 */
export default function ReviewQueue() {
  const { role } = useApp();
  const toast = useToast();
  const navigate = useNavigate();

  const [items, setItems] = useState(QUEUE);
  const [filter, setFilter] = useState("all");
  const [selectedId, setSelectedId] = useState(QUEUE[0].id);

  const mayWrite = can(role, "queue.write");
  const shown = items.filter((i) => filter === "all" || i.script === filter);
  const current = shown.find((i) => i.id === selectedId) || shown[0];

  // Changing the filter can strand the selection on a hidden row.
  useEffect(() => {
    if (current && current.id !== selectedId) setSelectedId(current.id);
  }, [filter, current, selectedId]);

  // ↯ API SEAM — PATCH /v1/admin/queue/{id}/dismiss
  const dismiss = (id) => {
    setItems((prev) => prev.filter((i) => i.id !== id));
    toast("Removed from queue", "It will come back if students keep asking.");
  };

  // ↯ API SEAM — POST /v1/admin/content/faq
  const publish = (id) => {
    setItems((prev) => prev.filter((i) => i.id !== id));
    toast("Answer published", "Live now on web and WhatsApp.");
  };

  return (
    <div className="ua-page">
      <div className="ua-head">
        <div>
          <h1 className="ua-h1">Review queue</h1>
          <p className="ua-sub">
            Questions the assistant could not answer confidently. Each one is a gap in the catalogue
            that real students walked into.
          </p>
        </div>
        <div className="ua-tabs">
          {FILTERS.map(([key, label]) => (
            <button
              key={key}
              className={`ua-tab${filter === key ? " on" : ""}`}
              onClick={() => setFilter(key)}
            >
              {label}
              <span className="n">
                {key === "all" ? items.length : items.filter((i) => i.script === key).length}
              </span>
            </button>
          ))}
        </div>
      </div>

      {shown.length === 0 ? (
        <div className="ua-card">
          <EmptyState
            title="Queue is clear"
            body="Every recent question matched a known intent. New gaps will land here automatically."
          />
        </div>
      ) : (
        <div className="ua-split">
          <QueueList items={shown} selectedId={current?.id} onSelect={setSelectedId} />
          {current && (
            <QueueDetail
              item={current}
              mayWrite={mayWrite}
              role={role}
              onPublish={publish}
              onDismiss={dismiss}
              onFixRecord={() => navigate("/admin/content")}
            />
          )}
        </div>
      )}
    </div>
  );
}
