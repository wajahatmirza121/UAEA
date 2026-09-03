import { ChevronLeft, ChevronRight } from "lucide-react";

/**
 * Page control that collapses long ranges: first, last, and a window around
 * the current page, with an ellipsis where numbers are skipped.
 */
export default function Pagination({ page, pages, onChange }) {
  const visible = Array.from({ length: pages }, (_, i) => i + 1).filter(
    (p) => p === 1 || p === pages || Math.abs(p - page) <= 1
  );

  return (
    <div className="ua-pager">
      <button
        className="ua-pg"
        disabled={page === 1}
        onClick={() => onChange(page - 1)}
        aria-label="Previous page"
      >
        <ChevronLeft size={14} />
      </button>

      {visible.map((p, i) => (
        <span key={p} style={{ display: "contents" }}>
          {i > 0 && visible[i - 1] !== p - 1 && (
            <span style={{ color: "var(--t3)", padding: "0 3px" }}>…</span>
          )}
          <button
            className={`ua-pg${p === page ? " on" : ""}`}
            onClick={() => onChange(p)}
            aria-current={p === page ? "page" : undefined}
          >
            {p}
          </button>
        </span>
      ))}

      <button
        className="ua-pg"
        disabled={page === pages}
        onClick={() => onChange(page + 1)}
        aria-label="Next page"
      >
        <ChevronRight size={14} />
      </button>
    </div>
  );
}
