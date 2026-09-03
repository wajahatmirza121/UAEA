import { Link } from "react-router-dom";
import {
  GraduationCap, Banknote, ClipboardList, BookOpen, Award, FolderArchive,
} from "lucide-react";
import { CATEGORIES, CATEGORY_DEPARTMENT } from "@/mocks/routing";
import { useApp } from "@/context/AppContext";

const ICONS = {
  Admissions: GraduationCap,
  Finance: Banknote,
  Examinations: ClipboardList,
  Academics: BookOpen,
  Certification: Award,
  Records: FolderArchive,
};

/**
 * Services grouped by the department that owns them, so a student who does
 * not know what their question is called can still find it.
 */
export default function CategoryGrid() {
  const { store, urdu } = useApp();

  return (
    <section className="st-section" style={{ borderTop: "1px solid var(--line)" }}>
      <div className="st-wrap">
        <p className="st-eyebrow">Browse by department</p>
        <h2 className="st-h2">{urdu ? "شعبے کے اعتبار سے" : "Not sure what to ask?"}</h2>
        <p className="st-lede" style={{ marginBottom: 26 }}>
          Every service belongs to a department. Pick the area your question falls under and see
          exactly what is needed, what it costs and who handles it.
        </p>

        <div className="st-grid three">
          {CATEGORIES.map((c) => {
            const Icon = ICONS[c.id];
            const count = store.services.filter((s) => s.cat === c.id).length;
            const dept = store.departments.find((d) => d.id === CATEGORY_DEPARTMENT[c.id]);

            return (
              <Link key={c.id} to={`/services?category=${encodeURIComponent(c.id)}`} className="st-card">
                <span className="st-card-icon">
                  <Icon size={18} color="var(--brass)" />
                </span>
                <h3>{urdu ? c.ur : c.en}</h3>
                <p className={urdu ? "ur" : ""}>{urdu ? c.blurb_ur : c.blurb}</p>
                <div className="st-meta">
                  <span>{count} services</span>
                  <span>·</span>
                  <span>{dept?.en}</span>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </section>
  );
}
