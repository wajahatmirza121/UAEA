import { Search } from "lucide-react";

/**
 * Search + filter strip above a table.
 * Filters are passed as a list of select descriptors so each page decides
 * what it filters on without a bespoke toolbar per table.
 */
export default function TableToolbar({
  tabs,
  activeTab,
  onTab,
  query,
  onQuery,
  searchPlaceholder = "Search this table",
  filters = [],
  children,
}) {
  return (
    <div className="ua-toolbar">
      {tabs && (
        <div className="ua-tabs">
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`ua-tab${activeTab === t.id ? " on" : ""}`}
              onClick={() => onTab(t.id)}
            >
              {t.icon && <t.icon size={13} />}
              {t.label}
              {t.count !== undefined && <span className="n">{t.count}</span>}
            </button>
          ))}
        </div>
      )}

      <div style={{ flex: 1 }} />

      {onQuery && (
        <div className="ua-searchwrap" style={{ maxWidth: 250 }}>
          <Search size={14} />
          <input
            className="ua-input"
            placeholder={searchPlaceholder}
            value={query}
            onChange={(e) => onQuery(e.target.value)}
          />
        </div>
      )}

      {filters.map((f) => (
        <select
          key={f.key}
          className="ua-select"
          style={{ width: "auto", minWidth: f.width || 136 }}
          value={f.value}
          onChange={(e) => f.onChange(e.target.value)}
          aria-label={f.label}
        >
          {f.options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      ))}

      {children}
    </div>
  );
}
