import { useState, useEffect } from "react";
import { Check, ArrowUpDown, ShieldCheck } from "lucide-react";
import Pagination from "./Pagination";
import Skeleton from "@/components/ui/Skeleton";
import EmptyState from "@/components/ui/EmptyState";
import Button from "@/components/ui/Button";

/**
 * Generic table driven by a column descriptor list.
 *
 * columns: [{ key, label, sortable, width, render(row) }]
 *
 * One component backs every table in the console, which is why adding a tab
 * to the content library costs a column array rather than a new screen.
 * Selection is optional so read-only roles get a table with no checkboxes
 * rather than checkboxes that do nothing.
 */
export default function DataTable({
  columns,
  rows,
  rowKey = "id",
  rowActions,
  selectable = true,
  selected = [],
  setSelected = () => {},
  sort,
  setSort,
  loading,
  perPage = 8,
  bulkBar,
  emptyTitle = "Nothing to show",
  emptyBody,
  emptyAction,
}) {
  const [page, setPage] = useState(1);

  // Any change to the result set or ordering sends you back to page one,
  // otherwise you can end up stranded on an empty page 4.
  useEffect(() => {
    setPage(1);
  }, [rows.length, sort?.key, sort?.dir]);

  if (loading) {
    return (
      <div style={{ padding: 14 }}>
        <Skeleton height={40} rows={6} />
      </div>
    );
  }

  if (rows.length === 0) {
    return <EmptyState title={emptyTitle} body={emptyBody} action={emptyAction} />;
  }

  const pages = Math.max(1, Math.ceil(rows.length / perPage));
  const view = rows.slice((page - 1) * perPage, page * perPage);
  const allOn = view.length > 0 && view.every((r) => selected.includes(r[rowKey]));

  const toggleAll = () =>
    setSelected(
      allOn
        ? selected.filter((id) => !view.some((r) => r[rowKey] === id))
        : [...new Set([...selected, ...view.map((r) => r[rowKey])])]
    );

  const toggleOne = (id, on) =>
    setSelected(on ? selected.filter((x) => x !== id) : [...selected, id]);

  const onSort = (key) =>
    setSort({ key, dir: sort.key === key && sort.dir === "asc" ? "desc" : "asc" });

  return (
    <>
      <div className="ua-tablewrap">
        <table className="ua-table">
          <thead>
            <tr>
              {selectable && (
                <th style={{ width: 38 }}>
                  <button
                    className={`ua-check${allOn ? " on" : ""}`}
                    onClick={toggleAll}
                    aria-label="Select all rows on this page"
                  >
                    {allOn && <Check size={11} strokeWidth={3} />}
                  </button>
                </th>
              )}

              {columns.map((c) => (
                <th
                  key={c.key}
                  className={`${c.sortable ? "sortable " : ""}${sort?.key === c.key ? "act" : ""}`}
                  style={c.width ? { width: c.width } : undefined}
                  onClick={c.sortable ? () => onSort(c.key) : undefined}
                >
                  {c.label}
                  {c.sortable && (
                    <span className="sarrow">
                      <ArrowUpDown size={11} />
                    </span>
                  )}
                </th>
              ))}

              {rowActions && <th style={{ width: 116 }} />}
            </tr>
          </thead>

          <tbody>
            {view.map((row) => {
              const on = selected.includes(row[rowKey]);
              return (
                <tr key={row[rowKey]} className={on ? "sel" : ""}>
                  {selectable && (
                    <td>
                      <button
                        className={`ua-check${on ? " on" : ""}`}
                        onClick={() => toggleOne(row[rowKey], on)}
                        aria-label={`Select ${row[rowKey]}`}
                      >
                        {on && <Check size={11} strokeWidth={3} />}
                      </button>
                    </td>
                  )}

                  {columns.map((c) => (
                    <td key={c.key}>{c.render(row)}</td>
                  ))}

                  {rowActions && <td>{rowActions(row)}</td>}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {selectable && selected.length > 0 && (
        <div className="ua-bulk">
          <ShieldCheck size={15} color="var(--brass)" />
          <span style={{ flex: 1 }}>
            <b className="ua-num">{selected.length}</b> record{selected.length > 1 ? "s" : ""} selected
          </span>
          {bulkBar}
          <Button size="sm" variant="ghost" onClick={() => setSelected([])}>
            Clear
          </Button>
        </div>
      )}

      <div className="ua-tfoot">
        <span className="ua-num">
          Showing {(page - 1) * perPage + 1}–{Math.min(page * perPage, rows.length)} of {rows.length}
        </span>
        <Pagination page={page} pages={pages} onChange={setPage} />
      </div>
    </>
  );
}
