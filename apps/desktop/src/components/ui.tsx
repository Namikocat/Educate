import type { ButtonHTMLAttributes, ReactNode } from "react";

export function Button({ variant = "default", className = "", ...p }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "default" | "primary" | "ghost" | "danger" }) {
  const v = {
    default: "border border-line bg-surface hover:bg-bg",
    primary: "bg-accent text-white hover:opacity-90 border border-accent",
    ghost: "hover:bg-bg",
    danger: "border border-bad text-bad hover:bg-bad/10",
  }[variant];
  return <button {...p} className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition disabled:opacity-40 disabled:cursor-not-allowed focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent ${v} ${className}`} />;
}

export function Card({ children, className = "", title, actions }: { children: ReactNode; className?: string; title?: ReactNode; actions?: ReactNode }) {
  return (
    <section className={`rounded-xl border border-line bg-surface p-4 ${className}`}>
      {(title || actions) && <div className="mb-3 flex items-center justify-between gap-2"><h3 className="font-semibold">{title}</h3>{actions}</div>}
      {children}
    </section>
  );
}

export function Badge({ children, tone = "muted" }: { children: ReactNode; tone?: "muted" | "good" | "bad" | "accent" }) {
  const t = { muted: "bg-bg text-muted border-line", good: "bg-good/10 text-good border-good/30", bad: "bg-bad/10 text-bad border-bad/30", accent: "bg-accent/10 text-accent border-accent/30" }[tone];
  return <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs ${t}`}>{children}</span>;
}

export function Spinner({ label = "กำลังโหลด…" }: { label?: string }) {
  return <div role="status" className="flex items-center gap-2 text-sm text-muted"><span className="h-4 w-4 animate-spin rounded-full border-2 border-accent border-t-transparent" />{label}</div>;
}

export function ErrorBox({ error }: { error: unknown }) {
  if (!error) return null;
  return <div role="alert" className="rounded-md border border-bad/40 bg-bad/10 p-3 text-sm text-bad">{error instanceof Error ? error.message : String(error)}</div>;
}

export function Bar({ value, label }: { value: number; label?: string }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div className="flex items-center gap-2" aria-label={label} title={`${pct}%`}>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-bg"><div className="h-full rounded-full bg-accent" style={{ width: `${pct}%` }} /></div>
      <span className="w-10 text-right text-xs tabular-nums text-muted">{pct}%</span>
    </div>
  );
}

export function Select<T extends string | number>({ value, onChange, options, label }: { value: T; onChange: (v: T) => void; options: { value: T; label: string }[]; label: string }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-muted">{label}</span>
      <select className="rounded-md border border-line bg-surface px-2 py-1.5" value={String(value)}
        onChange={(e) => onChange((typeof value === "number" ? Number(e.target.value) : e.target.value) as T)}>
        {options.map((o) => <option key={String(o.value)} value={String(o.value)}>{o.label}</option>)}
      </select>
    </label>
  );
}
