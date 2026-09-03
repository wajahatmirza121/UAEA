/**
 * CSV export.
 *
 * Returns false rather than throwing when the host blocks the download —
 * sandboxed iframes and some corporate browsers do. Callers surface that
 * honestly instead of showing a success toast that lies.
 */
export function exportCSV(filename, columns, rows) {
  const esc = (s) => `"${String(s ?? "").replace(/"/g, '""')}"`;
  const body = [
    columns.map((c) => esc(c.label)).join(","),
    ...rows.map((r) => columns.map((c) => esc(c.value(r))).join(",")),
  ].join("\n");

  try {
    // BOM keeps Excel from mangling Urdu text in the export.
    const blob = new Blob(["\uFEFF" + body], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    return true;
  } catch {
    return false;
  }
}
