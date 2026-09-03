import { X } from "lucide-react";
import { useEscape } from "@/hooks/useEscape";

/**
 * Centred dialog. Closes on Escape and on a click that both starts and ends
 * on the backdrop — mousedown rather than click, so a drag that begins
 * inside the modal and releases outside does not dismiss it.
 */
export default function Modal({ open, onClose, title, desc, children, footer, wide }) {
  useEscape(open, onClose);
  if (!open) return null;

  return (
    <div
      className="ua-overlay"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className={`ua-modal${wide ? " wide" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="ua-modal-h">
          <div style={{ flex: 1 }}>
            <h3>{title}</h3>
            {desc && <p>{desc}</p>}
          </div>
          <button className="ua-mini" onClick={onClose} aria-label="Close">
            <X size={15} />
          </button>
        </div>
        <div className="ua-modal-b">{children}</div>
        {footer && <div className="ua-modal-f">{footer}</div>}
      </div>
    </div>
  );
}
