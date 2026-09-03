import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, ArrowRight } from "lucide-react";
import { useApp } from "@/context/AppContext";

/**
 * The entry point from anywhere on the site. Hands the question to /chat as a
 * navigation state so the student never has to retype it.
 */
export default function AskBar({ autoFocus }) {
  const [value, setValue] = useState("");
  const navigate = useNavigate();
  const { urdu } = useApp();

  const go = () => {
    const q = value.trim();
    if (!q) return;
    navigate("/chat", { state: { question: q } });
  };

  return (
    <div className="st-ask">
      <Search size={17} color="var(--t3)" style={{ flex: "0 0 17px" }} />
      <input
        autoFocus={autoFocus}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && go()}
        className={urdu ? "ur" : ""}
        placeholder={
          urdu ? "اپنا سوال اردو یا رومن اردو میں لکھیں" : "Apna sawal likhein — Urdu, Roman Urdu ya English"
        }
        aria-label="Ask a question"
      />
      <button className="st-send" onClick={go} disabled={!value.trim()} aria-label="Send question">
        <ArrowRight size={17} />
      </button>
    </div>
  );
}
