import { createContext, useContext, useState, useCallback } from "react";
import Toast from "@/components/ui/Toast";

const ToastContext = createContext(null);

/** useToast() returns push(title, desc, tone). Auto-dismisses after 3.6s. */
export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside <ToastProvider>");
  return ctx;
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const push = useCallback((title, desc, tone = "jade") => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, title, desc, tone }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3600);
  }, []);

  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="ua-toasts">
        {toasts.map((t) => (
          <Toast key={t.id} title={t.title} desc={t.desc} tone={t.tone} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}
