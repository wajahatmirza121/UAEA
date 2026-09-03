import { useNavigate } from "react-router-dom";
import AskBar from "@/components/student/AskBar";
import { QUICK_ASKS } from "@/mocks/routing";
import { useApp } from "@/context/AppContext";

export default function Hero() {
  const navigate = useNavigate();
  const { urdu } = useApp();

  return (
    <section className="st-hero">
      <div className="st-wrap st-hero-in">
        <h1>Your University. Your Language.</h1>
        <p className="ur ur-head" style={{ direction: "rtl" }}>
          آپ کی یونیورسٹی۔ آپ کی زبان۔
        </p>
        <p>
          {urdu
            ? "فیس، تاریخوں، دستاویزات اور شعبوں کے بارے میں اردو یا رومن اردو میں پوچھیں۔ ہر جواب یونیورسٹی کے اپنے ریکارڈ سے آتا ہے۔"
            : "Ask about fees, deadlines, documents and departments in Urdu, Roman Urdu or English. Every answer comes from the University's own records — and tells you when it was last checked."}
        </p>

        <AskBar />

        <div className="st-chips">
          {QUICK_ASKS.slice(0, 5).map((q) => (
            <button
              key={q.text}
              className={`st-chip${/[\u0600-\u06FF]/.test(q.text) ? " ur" : ""}`}
              onClick={() => navigate("/chat", { state: { question: q.text } })}
            >
              {q.text}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
