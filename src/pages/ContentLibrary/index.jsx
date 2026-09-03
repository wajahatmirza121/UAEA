import { useState, useMemo } from "react";
import { Plus, Download, ShieldCheck } from "lucide-react";
import { CONTENT_TABS } from "./tabs";
import RowActions from "./RowActions";
import DataTable from "@/components/data/DataTable";
import TableToolbar from "@/components/data/TableToolbar";
import Button from "@/components/ui/Button";
import ReadOnlyNotice from "@/components/ui/ReadOnlyNotice";
import RecordModal from "@/components/content/RecordModal";
import RecordHistory from "@/components/content/RecordHistory";
import DeleteRecordModal from "@/components/content/DeleteRecordModal";
import { COLUMNS, nameOf } from "@/components/content/columns";
import { useDebounced } from "@/hooks/useDebounced";
import { freshness } from "@/lib/freshness";
import { can } from "@/lib/rbac";
import { exportCSV } from "@/lib/csv";
import { ISO_TODAY } from "@/lib/constants";
import { useApp } from "@/context/AppContext";
import { useToast } from "@/context/ToastContext";

/**
 * The catalogue. These four tables are the assistant's only source for fees,
 * dates, checklists and contacts — nothing here comes from model memory.
 */
export default function ContentLibrary() {
  const { store, mutate, verifyRecord, audit, role, urdu } = useApp();
  const toast = useToast();

  const [tab, setTab] = useState("services");
  const [rawQuery, setRawQuery] = useState("");
  const query = useDebounced(rawQuery);
  const [category, setCategory] = useState("all");
  const [fresh, setFresh] = useState("all");
  const [sort, setSort] = useState({ key: "verified", dir: "asc" });
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(false);

  const [editing, setEditing] = useState(null); // record | "new" | null
  const [deleting, setDeleting] = useState(null);
  const [historyOf, setHistoryOf] = useState(null);

  const mayWrite = can(role, "content.write");
  const rows = store[tab];

  const switchTab = (next) => {
    setTab(next);
    setSelected([]);
    setRawQuery("");
    setCategory("all");
    setFresh("all");
    setLoading(true);
    // ↯ API SEAM — GET /v1/lookup/{tab}
    setTimeout(() => setLoading(false), 280);
  };

  const categories = useMemo(
    () => [...new Set(rows.map((r) => r.cat).filter(Boolean))],
    [rows]
  );

  const filtered = useMemo(() => {
    const matched = rows.filter((r) => {
      if (query && !Object.values(r).join(" ").toLowerCase().includes(query.toLowerCase()))
        return false;
      if (category !== "all" && r.cat !== category) return false;
      if (fresh !== "all" && freshness(r.verified).tone !== fresh) return false;
      return true;
    });

    return [...matched].sort((a, b) => {
      const av = a[sort.key];
      const bv = b[sort.key];
      if (av === bv) return 0;
      if (av === null || av === undefined) return 1;
      if (bv === null || bv === undefined) return -1;
      const cmp = typeof av === "number" ? av - bv : String(av).localeCompare(String(bv));
      return sort.dir === "asc" ? cmp : -cmp;
    });
  }, [rows, query, category, fresh, sort]);

  // ↯ API SEAM — POST /v1/admin/content/{tab}/{id}/verify
  const onVerify = (record) => {
    verifyRecord(tab, record, nameOf);
    toast("Marked as verified", `${nameOf(record)} now shows today's date to students.`);
  };

  const onVerifySelected = () => {
    selected.forEach((id) => {
      const record = rows.find((r) => r.id === id);
      if (record) verifyRecord(tab, record, nameOf);
    });
    toast("Marked as verified", `${selected.length} records updated and re-published.`);
    setSelected([]);
  };

  const onSave = (values, changes) => {
    if (editing === "new") {
      mutate(tab, null, values, { action: "create", record: nameOf(values), changes });
    } else {
      mutate(tab, editing.id, values, { action: "update", record: nameOf(values), changes });
    }
    toast(
      editing === "new" ? "Record added" : "Changes saved",
      "The assistant will use this from the next message onward."
    );
    setEditing(null);
  };

  const onDelete = () => {
    mutate(tab, deleting.id, null, { action: "delete", record: nameOf(deleting), changes: [] });
    toast("Record deleted", `${nameOf(deleting)} removed from the catalogue.`);
    setDeleting(null);
  };

  const onExport = () => {
    const cols = [
      ...COLUMNS[tab]
        .filter((c) => c.key !== "verified" && c.key !== "checklist")
        .map((c) => ({ label: c.label, value: (r) => r[c.key] })),
      { label: "Last verified", value: (r) => r.verified },
      { label: "Verified by", value: (r) => r.by },
    ];
    const ok = exportCSV(`uaea-${tab}-${ISO_TODAY}.csv`, cols, filtered);
    toast(
      ok ? "Export downloaded" : "Export blocked",
      ok
        ? `${filtered.length} rows saved, including verification dates.`
        : "Your browser blocked the download. Try again outside a sandboxed frame.",
      ok ? "jade" : "rose"
    );
  };

  return (
    <div className="ua-page">
      <div className="ua-head">
        <div>
          <h1 className={`ua-h1${urdu ? " ur" : ""}`}>{urdu ? "مواد" : "Content library"}</h1>
          <p className="ua-sub">
            These tables are the assistant&apos;s only source for fees, dates, checklists and
            contacts. Nothing here comes from the model&apos;s memory.
          </p>
        </div>
        <div style={{ display: "flex", gap: 9 }}>
          <Button icon={Download} onClick={onExport}>
            Export CSV
          </Button>
          {mayWrite && (
            <Button variant="primary" icon={Plus} onClick={() => setEditing("new")}>
              Add record
            </Button>
          )}
        </div>
      </div>

      <div className="ua-card">
        {!mayWrite && <ReadOnlyNotice role={role} />}

        <TableToolbar
          tabs={CONTENT_TABS.map((t) => ({ ...t, count: store[t.id].length }))}
          activeTab={tab}
          onTab={switchTab}
          query={rawQuery}
          onQuery={setRawQuery}
          filters={[
            ...(categories.length
              ? [
                  {
                    key: "cat",
                    label: "Category",
                    value: category,
                    onChange: setCategory,
                    options: [
                      { value: "all", label: "All categories" },
                      ...categories.map((c) => ({ value: c, label: c })),
                    ],
                  },
                ]
              : []),
            {
              key: "fresh",
              label: "Freshness",
              width: 138,
              value: fresh,
              onChange: setFresh,
              options: [
                { value: "all", label: "Any freshness" },
                { value: "jade", label: "Verified" },
                { value: "amber", label: "Ageing" },
                { value: "rose", label: "Stale" },
              ],
            },
          ]}
        />

        <DataTable
          columns={COLUMNS[tab]}
          rows={filtered}
          loading={loading}
          sort={sort}
          setSort={setSort}
          selectable={mayWrite}
          selected={selected}
          setSelected={setSelected}
          bulkBar={
            <Button size="sm" icon={ShieldCheck} onClick={onVerifySelected}>
              Mark verified
            </Button>
          }
          rowActions={(record) => (
            <RowActions
              role={role}
              record={record}
              onHistory={setHistoryOf}
              onVerify={onVerify}
              onEdit={setEditing}
              onDelete={setDeleting}
            />
          )}
          emptyTitle="Nothing matches those filters"
          emptyBody="Clear the search or widen the freshness filter to see records again."
          emptyAction={
            <Button
              onClick={() => {
                setRawQuery("");
                setCategory("all");
                setFresh("all");
              }}
            >
              Reset filters
            </Button>
          }
        />
      </div>

      <RecordModal
        open={editing !== null}
        record={editing === "new" ? null : editing}
        tab={tab}
        onClose={() => setEditing(null)}
        onSave={onSave}
      />

      <DeleteRecordModal
        record={deleting}
        tab={tab}
        onClose={() => setDeleting(null)}
        onConfirm={onDelete}
      />

      <RecordHistory record={historyOf} audit={audit} onClose={() => setHistoryOf(null)} />
    </div>
  );
}
