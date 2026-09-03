/** Labelled toggle. Disabled when the current role cannot write. */
export default function Switch({ on, onChange, label, desc, disabled }) {
  return (
    <button
      className="ua-switchrow"
      role="switch"
      aria-checked={on}
      disabled={disabled}
      onClick={() => !disabled && onChange(!on)}
      style={{ cursor: disabled ? "not-allowed" : "pointer", opacity: disabled ? 0.6 : 1 }}
    >
      <span style={{ flex: 1 }}>
        <span style={{ fontSize: 13, display: "block" }}>{label}</span>
        {desc && (
          <span
            style={{
              fontSize: 11.5,
              color: "var(--t3)",
              display: "block",
              marginTop: 3,
              lineHeight: 1.55,
            }}
          >
            {desc}
          </span>
        )}
      </span>
      <span className={`ua-switch${on ? " on" : ""}`}>
        <i />
      </span>
    </button>
  );
}
