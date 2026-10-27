/**
 * Small, safe Markdown renderer for AI tutor answers. Builds React elements directly (no raw HTML,
 * no innerHTML except KaTeX output), so model text can never inject markup or scripts.
 * Supports: headings, paragraphs, bold/italic, inline code, fenced code, bullet/numbered lists,
 * blockquotes, tables, horizontal rules, and $inline$ / $$display$$ math.
 */
import { Fragment, memo, type ReactNode } from "react";
import { MathBlock, Tex } from "./Tex";

type Block =
  | { t: "h"; level: number; text: string }
  | { t: "p"; text: string }
  | { t: "code"; text: string }
  | { t: "math"; text: string }
  | { t: "ul" | "ol"; items: string[] }
  | { t: "quote"; text: string }
  | { t: "table"; head: string[]; rows: string[][] }
  | { t: "hr" };

const cells = (line: string) => line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());

export function parseBlocks(src: string): Block[] {
  const lines = src.replace(/\r\n?/g, "\n").split("\n");
  const out: Block[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();
    if (!trimmed) { i++; continue; }
    if (trimmed.startsWith("```")) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) buf.push(lines[i++]);
      i++;
      out.push({ t: "code", text: buf.join("\n") });
      continue;
    }
    if (trimmed.startsWith("$$")) {
      let body = trimmed.slice(2);
      if (body.endsWith("$$") && body.length > 2) { out.push({ t: "math", text: body.slice(0, -2) }); i++; continue; }
      const buf = [body];
      i++;
      while (i < lines.length && !lines[i].includes("$$")) buf.push(lines[i++]);
      if (i < lines.length) buf.push(lines[i].slice(0, lines[i].indexOf("$$")));
      i++;
      out.push({ t: "math", text: buf.join("\n").trim() });
      continue;
    }
    const h = /^(#{1,4})\s+(.*)$/.exec(trimmed);
    if (h) { out.push({ t: "h", level: h[1].length, text: h[2] }); i++; continue; }
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) { out.push({ t: "hr" }); i++; continue; }
    if (trimmed.startsWith("|") && i + 1 < lines.length && /^\s*\|?\s*:?-{2,}/.test(lines[i + 1])) {
      const head = cells(trimmed);
      const rows: string[][] = [];
      i += 2;
      while (i < lines.length && lines[i].trim().startsWith("|")) rows.push(cells(lines[i++]));
      out.push({ t: "table", head, rows });
      continue;
    }
    if (/^[-*+]\s+/.test(trimmed) || /^\d+[.)]\s+/.test(trimmed)) {
      const ordered = /^\d+[.)]\s+/.test(trimmed);
      const items: string[] = [];
      const re = ordered ? /^\d+[.)]\s+/ : /^[-*+]\s+/;
      while (i < lines.length && re.test(lines[i].trim())) {
        let item = lines[i].trim().replace(re, "");
        i++;
        // continuation lines (indented, not a new item)
        while (i < lines.length && /^\s{2,}\S/.test(lines[i]) && !re.test(lines[i].trim())) item += " " + lines[i++].trim();
        items.push(item);
      }
      out.push({ t: ordered ? "ol" : "ul", items });
      continue;
    }
    if (trimmed.startsWith(">")) {
      const buf: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) buf.push(lines[i++].trim().replace(/^>\s?/, ""));
      out.push({ t: "quote", text: buf.join(" ") });
      continue;
    }
    const buf = [trimmed];
    i++;
    while (i < lines.length && lines[i].trim() && !/^(#{1,4}\s|```|\$\$|>|[-*+]\s|\d+[.)]\s|\|)/.test(lines[i].trim())) buf.push(lines[i++].trim());
    out.push({ t: "p", text: buf.join(" ") });
  }
  return out;
}

/** Inline: `code`, **bold**, *italic*, and $math$ (math handled by Tex). */
function Inline({ text }: { text: string }) {
  const parts: ReactNode[] = [];
  // math spans are matched first so `*` inside $...$ is never treated as emphasis
  const re = /(\$\$[^$]+\$\$|\$[^$]+\$)|(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*\s][^*]*\*)/g;
  let last = 0, m: RegExpExecArray | null, k = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) parts.push(<Tex key={k++} text={text.slice(last, m.index)} />);
    const s = m[0];
    if (m[1]) parts.push(<Tex key={k++} text={s} />);
    else if (m[2]) parts.push(<code key={k++} className="rounded bg-bg px-1 py-0.5 font-mono text-[0.9em]">{s.slice(1, -1)}</code>);
    else if (m[3]) parts.push(<strong key={k++}><Tex text={s.slice(2, -2)} /></strong>);
    else parts.push(<em key={k++}><Tex text={s.slice(1, -1)} /></em>);
    last = re.lastIndex;
  }
  if (last < text.length) parts.push(<Tex key={k++} text={text.slice(last)} />);
  return <>{parts}</>;
}

const H = ["text-xl", "text-lg", "text-base", "text-base"];

export const Markdown = memo(function Markdown({ text }: { text: string }) {
  const blocks = parseBlocks(text);
  return (
    <div className="space-y-3 text-[0.95rem] leading-7">
      {blocks.map((b, i) => {
        switch (b.t) {
          case "h": return <div key={i} role="heading" aria-level={b.level + 1} className={`${H[b.level - 1]} mt-2 font-semibold`}><Inline text={b.text} /></div>;
          case "p": return <p key={i}><Inline text={b.text} /></p>;
          case "code": return <pre key={i} className="overflow-x-auto rounded-md bg-bg p-3 font-mono text-sm">{b.text}</pre>;
          case "math": return <MathBlock key={i} tex={b.text} />;
          case "ul": return <ul key={i} className="list-disc space-y-1 pl-6">{b.items.map((it, j) => <li key={j}><Inline text={it} /></li>)}</ul>;
          case "ol": return <ol key={i} className="list-decimal space-y-1 pl-6">{b.items.map((it, j) => <li key={j}><Inline text={it} /></li>)}</ol>;
          case "quote": return <blockquote key={i} className="border-l-4 border-accent/50 pl-3 text-muted"><Inline text={b.text} /></blockquote>;
          case "hr": return <hr key={i} className="border-line" />;
          case "table": return (
            <div key={i} className="overflow-x-auto">
              <table className="min-w-full border-collapse text-sm">
                <thead><tr>{b.head.map((c, j) => <th key={j} className="border border-line bg-bg px-2 py-1 text-left font-semibold"><Inline text={c} /></th>)}</tr></thead>
                <tbody>{b.rows.map((r, j) => <tr key={j}>{r.map((c, l) => <td key={l} className="border border-line px-2 py-1"><Inline text={c} /></td>)}</tr>)}</tbody>
              </table>
            </div>
          );
          default: return <Fragment key={i} />;
        }
      })}
    </div>
  );
});
