import { Link } from "react-router-dom";
import { useApp } from "@/context/AppContext";

/**
 * Footer carries real campus numbers rather than placeholder links, because a
 * student who has given up on the chat needs a phone number, not a sitemap.
 */
export default function StudentFooter() {
  const { store } = useApp();
  const campuses = store.departments.filter((d) => d.en.startsWith("Regional Campus")).slice(0, 4);

  return (
    <footer className="st-foot">
      <div className="st-wrap st-foot-grid">
        <div>
          <div className="st-logo" style={{ marginBottom: 12 }}>
            <span className="ua-mark">اُ</span>
            <span>
              <b>UAEA</b>
              <span>Urdu AI Educational Assistant</span>
            </span>
          </div>
          <p style={{ maxWidth: "38ch", lineHeight: 1.7 }}>
            Answers come from the University&apos;s own records and always show the source and the
            date they were last checked. If something is not recorded, you get a person instead of
            a guess.
          </p>
        </div>

        <div>
          <h5>Find things</h5>
          <Link to="/chat">Ask a question</Link>
          <Link to="/services">All services</Link>
          <Link to="/directory">Departments and campuses</Link>
          <Link to="/admin">Staff console</Link>
        </div>

        <div>
          <h5>Regional campuses</h5>
          {campuses.map((c) => (
            <a key={c.id} href={`tel:${c.phone}`} className="ua-num">
              {c.en.replace("Regional Campus ", "")} — {c.phone}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}
