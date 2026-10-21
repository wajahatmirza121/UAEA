import { useRef, useEffect } from "react";
import { ArrowUp } from "lucide-react";
import { useApp } from "@/context/AppContext";

/** Auto-growing input. Enter sends, Shift+Enter breaks the line. */
export default function Composer({ value, onChange, onSend, disabled }) {
  const ref = useRef(null);
  const { urdu } = useApp();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 130)}px`;
  }, [value]);

  const keyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="st-composer">
      <div className="st-composer-in">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={keyDown}
          placeholder={
            urdu ? "اپنا سوال لکھیں…" : "Sawal likhein — Urdu, Roman Urdu ya English…"
          }
          aria-label="Your message"
        />
        <button
          className="st-send"
          onClick={onSend}
          disabled={disabled || !value.trim()}
          aria-label="Send"
        >
          <ArrowUp size={18} />
        </button>
      </div>
      <p style={{ fontSize: 11, color: "var(--t3)", textAlign: "center", margin: "9px 0 0" }}>
        Answers come from University records. Results, fee status and attendance are shown only
        after a verification code sent to the student's WhatsApp.
      </p>
    </div>
  );
}
