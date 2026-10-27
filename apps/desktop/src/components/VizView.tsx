import { lazy, Suspense, useMemo, useState } from "react";
import { compile, type Fn1 } from "@viz/expr";
import { polygonLength, riemannRects, simpson, validateSpec, type VizSpec } from "@viz/spec";
import { Plot2D, type Scene } from "./Plot2D";
import { Spinner } from "./ui";

const Viz3D = lazy(() => import("./Viz3D"));
const COLORS = ["#2563eb", "#dc2626", "#059669", "#7c3aed", "#d97706", "#0891b2"];
const fmt = (v: number) => (Number.isFinite(v) ? (Math.abs(v) < 1e-10 ? "0" : v.toPrecision(7).replace(/\.?0+$/, "")) : "ไม่นิยาม");

function Slider({ label, value, min, max, step = 1, onChange }: { label: string; value: number; min: number; max: number; step?: number; onChange: (v: number) => void }) {
  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="w-40 text-muted">{label}</span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} className="flex-1 accent-[rgb(var(--accent))]" />
      <span className="w-14 text-right tabular-nums">{Number.isInteger(step) ? value : value.toFixed(2)}</span>
    </label>
  );
}

export function VizView({ spec: raw, editable = false }: { spec: unknown; editable?: boolean }) {
  const valid = useMemo(() => validateSpec(raw), [raw]);
  if (!valid.ok) return <div className="rounded border border-bad/40 p-2 text-sm text-bad">ไม่สามารถแสดงภาพได้: {valid.error}</div>;
  return <VizInner key={JSON.stringify(valid.spec)} spec={valid.spec} editable={editable} />;
}

function VizInner({ spec, editable }: { spec: VizSpec; editable: boolean }) {
  const s = spec as any;
  const [n, setN] = useState<number>(s.n ?? 6);
  const [method, setMethod] = useState<string>(s.method ?? "left");
  const [b, setB] = useState<number>(s.b ?? 1);
  const [a, setA] = useState<number>(s.a ?? 0);
  const [x0, setX0] = useState<number>(s.x0 ?? ((s.a ?? 0) + (s.b ?? 1)) / 2);
  const [sweep, setSweep] = useState(360);
  const [expr, setExpr] = useState<string>(s.f ?? s.expressions?.[0] ?? "x");
  const [showFill, setShowFill] = useState(true);

  const { f, exprErr } = useMemo((): { f: Fn1; exprErr: string | null } => {
    try { return { f: compile(expr), exprErr: null }; } catch (e) { return { f: compile(s.f ?? s.expressions?.[0] ?? "x"), exprErr: (e as Error).message }; }
  }, [expr]);
  const g: Fn1 | undefined = useMemo(() => (s.g ? compile(s.g) : undefined), [s.g]);

  const span = (s.b - s.a) || 1;
  let scene: Scene | null = null;
  const readouts: [string, string][] = [];
  let controls: JSX.Element[] = [];
  const is3D = s.type === "revolution" || s.type === "cross_section";

  switch (s.type) {
    case "function_plot": {
      const fns = (s.expressions as string[]).map((e, i) => ({ fn: i === 0 ? f : compile(e), color: COLORS[i % 6], label: i === 0 ? expr : e }));
      scene = { x: s.domain, curves: fns };
      break;
    }
    case "riemann": {
      const R = riemannRects(f, s.a, s.b, n, method as "left");
      const exact = simpson(f, s.a, s.b);
      scene = { x: [s.a - span * 0.1, s.b + span * 0.1], curves: [{ fn: f, color: COLORS[0], label: `f(x) = ${expr}` }], rects: R.rects };
      readouts.push(["Δx", fmt(R.dx)], [`ผลรวม (${method})`, fmt(R.sum)], ["ค่าอินทิกรัล (เชิงตัวเลข)", fmt(exact)], ["ความคลาดเคลื่อน", fmt(R.sum - exact)]);
      controls = [<Slider key="n" label="จำนวนสี่เหลี่ยม n" value={n} min={1} max={100} onChange={setN} />,
        <div key="m" className="flex gap-2 text-sm">{["left", "right", "mid"].map((m) => <button key={m} onClick={() => setMethod(m)} className={`rounded border px-2 py-0.5 ${m === method ? "border-accent bg-accent/10" : "border-line"}`}>{{ left: "จุดปลายซ้าย", right: "จุดปลายขวา", mid: "จุดกึ่งกลาง" }[m]}</button>)}</div>];
      break;
    }
    case "area": case "improper": case "accumulation": {
      const lo = s.type === "accumulation" ? s.a : s.a, hi = s.type === "area" ? s.b : b;
      const I = simpson(f, lo + (s.type === "improper" && s.a === 0 ? 1e-6 : 0), hi);
      scene = { x: [Math.min(s.a, 0) - span * 0.1, s.b + span * 0.1], curves: [{ fn: f, color: COLORS[0], label: expr }],
        fills: showFill ? [{ top: f, a: lo, b: hi, signed: true }] : [], vlines: [{ x: hi, dashed: true }] };
      if (s.type === "accumulation") {
        const F = (t: number) => simpson(f, s.a, t, 200);
        scene.curves.push({ fn: F, color: COLORS[1], label: `F(x) = ∫ f` });
        readouts.push([`F(${fmt(hi)}) = ∫ f`, fmt(I)], ["F′(x) = f(x)", fmt(f(hi))]);
      } else readouts.push([`∫ จาก ${fmt(lo)} ถึง ${fmt(hi)}`, fmt(I)]);
      if (s.type !== "area") controls = [<Slider key="b" label={s.type === "improper" ? "ขอบเขตบน b → ∞" : "x"} value={b} min={s.a + span * 0.02} max={s.type === "improper" ? s.b * 5 : s.b} step={span / 200} onChange={setB} />];
      if (s.type === "improper" && s.a <= 0 && s.b > 0 && s.singularity === 0) {
        const eps = Math.max(1e-4, a > 0 ? a : 0.1);
        readouts.length = 0;
        readouts.push([`∫ จาก ${fmt(eps)} ถึง ${fmt(s.b)}`, fmt(simpson(f, eps, s.b))], [`∫ จาก ${fmt(s.a)} ถึง ${fmt(-eps)}`, fmt(simpson(f, s.a, -eps))]);
        controls = [<Slider key="e" label="ε (ระยะจากจุดเอกฐาน)" value={a > 0 ? a : 0.1} min={0.001} max={0.5} step={0.001} onChange={setA} />];
        scene.fills = [{ top: f, a: eps, b: s.b }, { top: f, a: s.a, b: -eps }];
        scene.vlines = [{ x: 0, dashed: true }];
      }
      break;
    }
    case "area_between": {
      const swap = s.axis === "y";
      const I = simpson((t) => f(t) - g!(t), s.a, s.b);
      scene = { x: swap ? [-1, Math.max(...[s.a, s.b].map((t) => Math.max(f(t), g!(t)))) + 1] : [s.a - span * 0.2, s.b + span * 0.2],
        y: swap ? [s.a - span * 0.2, s.b + span * 0.2] : undefined,
        curves: [{ fn: f, color: COLORS[0], label: swap ? `x = ${s.f.replace(/x/g, "y")}` : s.f, swapXY: swap, from: swap ? s.a - span * 0.2 : undefined, to: swap ? s.b + span * 0.2 : undefined },
          { fn: g!, color: COLORS[1], label: swap ? `x = ${s.g.replace(/x/g, "y")}` : s.g, swapXY: swap, from: swap ? s.a - span * 0.2 : undefined, to: swap ? s.b + span * 0.2 : undefined }],
        fills: showFill ? [{ top: f, bottom: g, a, b, swapXY: swap }] : [] };
      readouts.push([`พื้นที่บน [${fmt(a)}, ${fmt(b)}] = ∫ (บน − ล่าง)`, fmt(simpson((t) => f(t) - g!(t), a, b))], ["พื้นที่ทั้งหมดระหว่างจุดตัด", fmt(I)]);
      controls = [<Slider key="a" label="ขอบเขตล่าง" value={a} min={s.a} max={b} step={span / 100} onChange={setA} />,
        <Slider key="b" label="ขอบเขตบน" value={b} min={a} max={s.b} step={span / 100} onChange={setB} />];
      break;
    }
    case "arc": {
      const P = polygonLength(f, s.a, s.b, n);
      const exact = simpson((t) => { const h = 1e-5 * span; const d = (f(t + h) - f(t - h)) / (2 * h); return Math.sqrt(1 + d * d); }, s.a, s.b);
      scene = { x: [s.a - span * 0.1, s.b + span * 0.1], curves: [{ fn: f, color: COLORS[0], label: expr }], polyline: P.pts };
      readouts.push([`ความยาวเส้นหัก (n = ${n})`, fmt(P.L)], ["ความยาวส่วนโค้ง (เชิงตัวเลข)", fmt(exact)], ["ผลต่าง", fmt(exact - P.L)]);
      controls = [<Slider key="n" label="จำนวนส่วนของเส้นตรง n" value={n} min={1} max={60} onChange={setN} />];
      break;
    }
    case "inverse": {
      scene = { x: [s.a, s.b], y: [s.a, s.b], curves: [{ fn: f, color: COLORS[0], label: `y = ${expr}` }, { fn: f, color: COLORS[1], label: "f⁻¹ (สะท้อน)", swapXY: true, from: s.a, to: s.b },
        { fn: (t) => t, color: "#9ca3af", dashed: true, label: "y = x" }],
        points: [{ x: x0, y: f(x0), label: "(a, f(a))" }, { x: f(x0), y: x0, label: "(f(a), a)" }] };
      const h = 1e-5, d = (f(x0 + h) - f(x0 - h)) / (2 * h);
      readouts.push(["a", fmt(x0)], ["f′(a)", fmt(d)], ["(f⁻¹)′(f(a)) = 1/f′(a)", fmt(1 / d)]);
      controls = [<Slider key="x0" label="จุด a" value={x0} min={s.a} max={s.b} step={(s.b - s.a) / 200} onChange={setX0} />];
      break;
    }
    case "tangent": {
      const h = 1e-5, m = (f(x0 + h) - f(x0 - h)) / (2 * h);
      scene = { x: [s.a, s.b], curves: [{ fn: f, color: COLORS[0], label: expr }, { fn: (t) => f(x0) + m * (t - x0), color: COLORS[1], dashed: true, label: "เส้นสัมผัส" }], points: [{ x: x0, y: f(x0) }] };
      readouts.push(["ความชัน", fmt(m)]);
      controls = [<Slider key="x0" label="x₀" value={x0} min={s.a} max={s.b} step={(s.b - s.a) / 200} onChange={setX0} />];
      break;
    }
  }

  if (is3D) {
    const solid = { f, g, a: s.a, b: s.b, axis: s.axis ?? "x", axisValue: s.axisValue, method: s.type === "cross_section" ? "cross_section" : s.method, shape: s.shape, sweep: (sweep / 180) * Math.PI, slices: n } as const;
    const vol = (() => {
      const c = s.axisValue ?? 0;
      if (s.type === "cross_section") { const k = { square: 1, semicircle: Math.PI / 8, equilateral: Math.sqrt(3) / 4 }[s.shape as "square"]; return simpson((t) => k * f(t) ** 2, s.a, s.b); }
      if (s.method === "shell") return simpson((t) => 2 * Math.PI * Math.abs(t - c) * Math.abs(f(t) - (g ? g(t) : 0)), s.a, s.b);
      if (s.method === "surface") return simpson((t) => { const h = 1e-5; const d = (f(t + h) - f(t - h)) / (2 * h); return 2 * Math.PI * Math.abs(f(t) - c) * Math.sqrt(1 + d * d); }, s.a, s.b);
      return simpson((t) => Math.PI * ((f(t) - c) ** 2 - (g ? (g(t) - c) ** 2 : 0)), s.a, s.b);
    })();
    readouts.push([s.method === "surface" ? "พื้นที่ผิว (เชิงตัวเลข)" : "ปริมาตร (เชิงตัวเลข)", fmt(Math.abs(vol))]);
    return (
      <div className="space-y-2">
        <Suspense fallback={<Spinner label="กำลังโหลดภาพสามมิติ…" />}><Viz3D solid={solid} /></Suspense>
        <Slider label="มุมการหมุน (องศา)" value={sweep} min={10} max={360} onChange={setSweep} />
        <Slider label={s.method === "shell" ? "จำนวนเปลือก" : "จำนวนชิ้นหน้าตัด"} value={n} min={1} max={40} onChange={setN} />
        <Readouts rows={readouts} />
        <p className="text-xs text-muted">ภาพ 2 มิติของบริเวณที่หมุน:</p>
        <Plot2D scene={{ x: [Math.min(s.a, 0) - span * 0.1, s.b + span * 0.1], curves: [{ fn: f, color: COLORS[0], label: s.f }, ...(g ? [{ fn: g, color: COLORS[1], label: s.g }] : [])],
          fills: [{ top: f, bottom: g, a: s.a, b: s.b }], vlines: s.axis === "y" ? [{ x: s.axisValue ?? 0, dashed: true }] : [] }} />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {editable && (
        <label className="flex items-center gap-2 text-sm"><span className="w-40 text-muted">ฟังก์ชัน f(x)</span>
          <input value={expr} onChange={(e) => setExpr(e.target.value)} className="flex-1 rounded border border-line bg-bg px-2 py-1 font-mono" />
          {exprErr && <span className="text-xs text-bad">{exprErr}</span>}</label>
      )}
      {scene && <Plot2D scene={scene} />}
      {controls}
      {(s.type === "area" || s.type === "area_between" || s.type === "improper") && (
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={showFill} onChange={(e) => setShowFill(e.target.checked)} />แสดงบริเวณแรเงา</label>
      )}
      <Readouts rows={readouts} />
    </div>
  );
}

function Readouts({ rows }: { rows: [string, string][] }) {
  if (!rows.length) return null;
  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-1 rounded-md bg-bg p-2 text-sm sm:grid-cols-4">
      {rows.map(([k, v]) => <div key={k}><dt className="text-xs text-muted">{k}</dt><dd className="font-mono tabular-nums">{v}</dd></div>)}
    </dl>
  );
}
