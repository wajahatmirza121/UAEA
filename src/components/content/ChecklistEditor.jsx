import { Plus, Trash2, ChevronUp, ChevronDown } from "lucide-react";

/**
 * Editor for a service's document checklist.
 *
 * These items are read out to students verbatim by get_document_checklist(),
 * so both scripts matter and so does the original-versus-copy flag — "do I
 * bring the original?" is the most common follow-up at the counter, and a
 * vague checklist sends people back home for a second trip.
 */
export default function ChecklistEditor({ items = [], onChange }) {
  const update = (id, patch) =>
    onChange(items.map((it) => (it.id === id ? { ...it, ...patch } : it)));

  const remove = (id) => onChange(items.filter((it) => it.id !== id));

  const add = () =>
    onChange([...items, { id: `c${Date.now()}`, en: "", ur: "", copy: false }]);

  const move = (index, delta) => {
    const next = [...items];
    const target = index + delta;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    onChange(next);
  };

  return (
    <div style={{ display: "grid", gap: 9 }}>
      {items.length === 0 && (
        <p style={{ fontSize: 12, color: "var(--t3)", margin: 0, lineHeight: 1.6 }}>
          No items yet. Without a checklist the assistant will tell students it does not know what
          to bring, and offer a human instead.
        </p>
      )}

      {items.map((item, i) => (
        <div
          key={item.id}
          style={{
            border: "1px solid var(--line)",
            borderRadius: 10,
            padding: 10,
            display: "grid",
            gap: 8,
            background: "var(--panel-2)",
          }}
        >
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span className="ua-stepnum">{i + 1}</span>
            <input
              className="ua-input"
              placeholder="Document name in English"
              value={item.en}
              onChange={(e) => update(item.id, { en: e.target.value })}
            />
            <div style={{ display: "flex", gap: 2 }}>
              <button
                className="ua-mini"
                onClick={() => move(i, -1)}
                disabled={i === 0}
                aria-label="Move up"
                style={{ opacity: i === 0 ? 0.35 : 1 }}
              >
                <ChevronUp size={14} />
              </button>
              <button
                className="ua-mini"
                onClick={() => move(i, 1)}
                disabled={i === items.length - 1}
                aria-label="Move down"
                style={{ opacity: i === items.length - 1 ? 0.35 : 1 }}
              >
                <ChevronDown size={14} />
              </button>
              <button
                className="ua-mini danger"
                onClick={() => remove(item.id)}
                aria-label="Remove item"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              className="ua-input ur"
              placeholder="اردو میں نام"
              value={item.ur}
              onChange={(e) => update(item.id, { ur: e.target.value })}
            />
            <select
              className="ua-select"
              style={{ width: "auto", minWidth: 132, flex: "0 0 auto" }}
              value={item.copy ? "copy" : "original"}
              onChange={(e) => update(item.id, { copy: e.target.value === "copy" })}
              aria-label="Original or copy"
            >
              <option value="original">Original</option>
              <option value="copy">Attested copy</option>
            </select>
          </div>
        </div>
      ))}

      <button className="ua-btn sm" onClick={add} style={{ justifySelf: "start" }}>
        <Plus size={14} />
        Add document
      </button>
    </div>
  );
}
