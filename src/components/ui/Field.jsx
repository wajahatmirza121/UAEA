import { AlertTriangle } from "lucide-react";

/** Label + control + inline error. Errors only render once touched. */
export default function Field({ label, hint, error, children }) {
  return (
    <div className="ua-field">
      {label && (
        <label className="ua-label">
          {label}
          {hint && <span style={{ color: "var(--t3)", fontSize: 11 }}>{hint}</span>}
        </label>
      )}
      {children}
      {error && (
        <span className="ua-err">
          <AlertTriangle size={11} />
          {error}
        </span>
      )}
    </div>
  );
}
