import { useEffect } from "react";

/** Escape closes any overlay. Applied by Modal, Drawer and CommandPalette. */
export function useEscape(active, onClose) {
  useEffect(() => {
    if (!active) return undefined;
    const handler = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [active, onClose]);
}
