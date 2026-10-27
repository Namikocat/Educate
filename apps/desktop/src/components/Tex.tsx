import katex from "katex";
import { memo, useMemo } from "react";

/** Render KaTeX safely (trust:false blocks \href, \url, \html* commands). */
export function texToHtml(tex: string, display = false): string {
  return katex.renderToString(tex, { displayMode: display, throwOnError: false, trust: false, strict: "ignore", output: "html" });
}

export const MathBlock = memo(function MathBlock({ tex, className = "" }: { tex: string; className?: string }) {
  const html = useMemo(() => texToHtml(tex, true), [tex]);
  return <div className={`overflow-x-auto ${className}`} dangerouslySetInnerHTML={{ __html: html }} />;
});

/** Text with inline $...$ and display $$...$$ math. Non-math text is rendered as plain text nodes. */
export const Tex = memo(function Tex({ text, className = "" }: { text: string; className?: string }) {
  const parts = useMemo(() => {
    const out: { math: boolean; display: boolean; s: string }[] = [];
    const re = /\$\$([\s\S]+?)\$\$|\$([^$]+?)\$/g;
    let last = 0, m: RegExpExecArray | null;
    while ((m = re.exec(text))) {
      if (m.index > last) out.push({ math: false, display: false, s: text.slice(last, m.index) });
      out.push({ math: true, display: !!m[1], s: m[1] ?? m[2] });
      last = re.lastIndex;
    }
    if (last < text.length) out.push({ math: false, display: false, s: text.slice(last) });
    return out;
  }, [text]);
  return (
    <span className={className}>
      {parts.map((p, i) => p.math ? <span key={i} dangerouslySetInnerHTML={{ __html: texToHtml(p.s, p.display) }} /> : <span key={i}>{p.s}</span>)}
    </span>
  );
});
