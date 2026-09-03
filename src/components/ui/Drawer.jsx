import { X } from "lucide-react";
import { useEscape } from "@/hooks/useEscape";

/**
 * Right-hand panel for context that belongs beside the page rather than on
 * top of it — record history, step editing, flow simulation.
 */
export default function Drawer({ open, onClose, title, desc, children, footer }) {
  useEscape(open, onClose);
  if (!open) return null;

  return (
    <div
      className="ua-drawerwrap"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="ua-drawer" role="dialog" aria-modal="true" aria-label={title}>
        <div className="ua-modal-h">
          <div style={{ flex: 1 }}>
            <h3>{title}</h3>
            {desc && <p>{desc}</p>}
          </div>
          <button className="ua-mini" onClick={onClose} aria-label="Close">
            <X size={15} />
          </button>
        </div>
        <div style={{ flex: 1, overflowY: "auto" }}>{children}</div>
        {footer && <div className="ua-modal-f">{footer}</div>}
      </div>
    </div>
  );
}
