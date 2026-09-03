import { useEffect } from "react";

/**
 * Cmd/Ctrl + key shortcut.
 * Prevents the browser default so Cmd+K does not open the browser's own
 * search bar.
 */
export function useHotkey(key, handler) {
  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === key.toLowerCase()) {
        e.preventDefault();
        handler();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [key, handler]);
}
