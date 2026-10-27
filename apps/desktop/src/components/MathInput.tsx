import { useEffect, useRef, useState } from "react";
import { getBackend } from "../lib/backend";
import { MathBlock } from "./Tex";

const PALETTE: { label: string; insert: string; caret?: number; title: string }[] = [
  { label: "a/b", insert: "()/()", caret: 1, title: "เศษส่วน" },
  { label: "xⁿ", insert: "^()", caret: 2, title: "ยกกำลัง" },
  { label: "√", insert: "sqrt()", caret: 5, title: "รากที่สอง" },
  { label: "eˣ", insert: "e^()", caret: 3, title: "เอกซ์โพเนนเชียล" },
  { label: "ln", insert: "ln()", caret: 3, title: "ลอการิทึมธรรมชาติ" },
  { label: "|x|", insert: "||", caret: 1, title: "ค่าสัมบูรณ์" },
  { label: "sin", insert: "sin()", caret: 4, title: "sin" },
  { label: "cos", insert: "cos()", caret: 4, title: "cos" },
  { label: "tan", insert: "tan()", caret: 4, title: "tan" },
  { label: "sec", insert: "sec()", caret: 4, title: "sec" },
  { label: "tan⁻¹", insert: "arctan()", caret: 7, title: "arctan" },
  { label: "sin⁻¹", insert: "arcsin()", caret: 7, title: "arcsin" },
  { label: "π", insert: "pi", title: "พาย" },
  { label: "∞", insert: "oo", title: "อนันต์" },
  { label: "+C", insert: " + C", title: "ค่าคงที่ของการอินทิเกรต" },
];

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSubmit?: () => void;
  disabled?: boolean;
  allowDiverges?: boolean;
  id?: string;
}

export function MathInput({ value, onChange, onSubmit, disabled, allowDiverges, id = "answer" }: Props) {
  const ref = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<{ ok: boolean; latex?: string; error?: string } | null>(null);

  useEffect(() => {
    if (!value.trim() || ["diverges", "ลู่ออก"].includes(value.trim().toLowerCase())) { setPreview(null); return; }
    const t = setTimeout(async () => {
      try { const be = await getBackend(); setPreview(await be.math("preview", { text: value })); }
      catch { setPreview(null); }
    }, 250);
    return () => clearTimeout(t);
  }, [value]);

  const insert = (s: string, caret?: number) => {
    const el = ref.current;
    const start = el?.selectionStart ?? value.length, end = el?.selectionEnd ?? value.length;
    const next = value.slice(0, start) + s + value.slice(end);
    onChange(next);
    requestAnimationFrame(() => { el?.focus(); const pos = start + (caret ?? s.length); el?.setSelectionRange(pos, pos); });
  };

  return (
    <div className="space-y-2">
      <label htmlFor={id} className="text-sm text-muted">คำตอบของคุณ (พิมพ์เช่น <code>x^2/2 + C</code>, <code>sqrt(x+1)</code>, <code>e^(2x)</code>, <code>ln|x|</code>)</label>
      <input id={id} ref={ref} value={value} disabled={disabled} spellCheck={false} autoComplete="off" aria-describedby={`${id}-preview`}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter" && onSubmit) { e.preventDefault(); onSubmit(); } }}
        className="w-full rounded-md border border-line bg-bg px-3 py-2 font-mono text-base focus:border-accent focus:outline-none" />
      <div className="flex flex-wrap gap-1" role="toolbar" aria-label="แป้นสัญลักษณ์คณิตศาสตร์">
        {PALETTE.map((p) => (
          <button key={p.label} type="button" title={p.title} disabled={disabled} onClick={() => insert(p.insert, p.caret)}
            className="rounded border border-line bg-surface px-2 py-0.5 text-sm hover:bg-bg">{p.label}</button>
        ))}
        {allowDiverges && <button type="button" disabled={disabled} onClick={() => onChange("diverges")} className="rounded border border-line bg-surface px-2 py-0.5 text-sm hover:bg-bg">ลู่ออก</button>}
      </div>
      <div id={`${id}-preview`} aria-live="polite" className="min-h-[2.5rem] rounded-md bg-bg px-3 py-1 text-sm">
        {preview?.ok && preview.latex ? <div className="flex items-center gap-2"><span className="text-muted">ระบบอ่านได้ว่า:</span><MathBlock tex={preview.latex} /></div>
          : preview && !preview.ok ? <span className="text-bad">{preview.error}</span> : <span className="text-muted">ตัวอย่างการแสดงผลจะปรากฏที่นี่</span>}
      </div>
    </div>
  );
}
