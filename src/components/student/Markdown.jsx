import { Fragment } from "react";

/**
 * Minimal, dependency-free Markdown for assistant replies.
 *
 * Supports paragraphs, line breaks, "- " / "1. " lists, pipe tables, "---"
 * rules, **bold**, *italic* / _italic_ and `code`. Everything is rendered as
 * React elements — no HTML from the server is ever injected.
 */

const INLINE = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*|_[^_\s][^_]*_)/g;

function inline(text, keyBase = "i") {
  const parts = String(text).split(INLINE);
  return parts.map((p, i) => {
    const k = `${keyBase}-${i}`;
    if (p.startsWith("**") && p.endsWith("**") && p.length > 4) return <b key={k}>{p.slice(2, -2)}</b>;
    if (p.startsWith("`") && p.endsWith("`") && p.length > 2) return <code key={k}>{p.slice(1, -1)}</code>;
    if ((p.startsWith("*") && p.endsWith("*")) || (p.startsWith("_") && p.endsWith("_"))) {
      if (p.length > 2) return <i key={k}>{p.slice(1, -1)}</i>;
    }
    return <Fragment key={k}>{p}</Fragment>;
  });
}

function withBreaks(lines, key) {
  return lines.map((l, i) => (
    <Fragment key={`${key}-${i}`}>
      {i > 0 && <br />}
      {inline(l, `${key}-${i}`)}
    </Fragment>
  ));
}

const isRow = (l) => /^\s*\|.*\|\s*$/.test(l);
const isSep = (l) => /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(l);
const cells = (l) => l.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());

export default function Markdown({ text }) {
  const lines = String(text || "").replace(/\r/g, "").split("\n");
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i++;
      continue;
    }
    if (/^\s*-{3,}\s*$/.test(line)) {
      blocks.push({ t: "hr" });
      i++;
      continue;
    }
    if (isRow(line) && i + 1 < lines.length && isSep(lines[i + 1])) {
      const head = cells(line);
      const rows = [];
      i += 2;
      while (i < lines.length && isRow(lines[i])) rows.push(cells(lines[i++]));
      blocks.push({ t: "table", head, rows });
      continue;
    }
    const bullet = /^\s*[-•]\s+(.*)$/;
    const num = /^\s*\d+[.)]\s+(.*)$/;
    if (bullet.test(line) || num.test(line)) {
      const ordered = num.test(line) && !bullet.test(line);
      const re = ordered ? num : bullet;
      const items = [];
      while (i < lines.length && re.test(lines[i])) {
        const item = [lines[i].match(re)[1]];
        i++;
        // continuation lines indented under the item ("  more text")
        while (i < lines.length && /^\s{2,}\S/.test(lines[i]) && !re.test(lines[i])) item.push(lines[i++].trim());
        items.push(item);
      }
      blocks.push({ t: ordered ? "ol" : "ul", items });
      continue;
    }
    const para = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !isRow(lines[i]) &&
      !/^\s*([-•]|\d+[.)])\s+/.test(lines[i]) &&
      !/^\s*-{3,}\s*$/.test(lines[i])
    ) {
      para.push(lines[i].replace(/\s+$/, ""));
      i++;
    }
    blocks.push({ t: "p", lines: para });
  }

  return (
    <div className="st-md">
      {blocks.map((b, k) => {
        if (b.t === "hr") return <hr key={k} />;
        if (b.t === "p") return <p key={k}>{withBreaks(b.lines, `p${k}`)}</p>;
        if (b.t === "ul" || b.t === "ol") {
          const Tag = b.t;
          return (
            <Tag key={k}>
              {b.items.map((it, j) => (
                <li key={j}>{withBreaks(it, `l${k}-${j}`)}</li>
              ))}
            </Tag>
          );
        }
        return (
          <div key={k} className="st-md-table">
            <table>
              <thead>
                <tr>
                  {b.head.map((h, j) => (
                    <th key={j}>{inline(h, `h${k}-${j}`)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {b.rows.map((r, j) => (
                  <tr key={j}>
                    {r.map((c, m) => (
                      <td key={m}>{inline(c, `c${k}-${j}-${m}`)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
}
