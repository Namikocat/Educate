import { useMemo, useRef, useState } from "react";
import type { Fn1 } from "@viz/expr";
import { getBackend } from "../lib/backend";

export interface Scene {
  x: [number, number];
  y?: [number, number];
  curves: { fn: Fn1; color: string; label?: string; dashed?: boolean; from?: number; to?: number; swapXY?: boolean }[];
  fills?: { top: Fn1; bottom?: Fn1; a: number; b: number; signed?: boolean; color?: string; swapXY?: boolean }[];
  rects?: { x0: number; x1: number; h: number }[];
  polyline?: [number, number][];
  points?: { x: number; y: number; label?: string }[];
  vlines?: { x: number; label?: string; dashed?: boolean }[];
}

const W = 640, H = 400, PAD = 34;
const C = { fillPos: "rgba(59,130,246,0.25)", fillNeg: "rgba(239,68,68,0.25)" };

function niceTicks(lo: number, hi: number, n = 6) {
  const span = hi - lo || 1;
  const step = Math.pow(10, Math.floor(Math.log10(span / n)));
  const m = [1, 2, 5, 10].find((k) => span / (k * step) <= n) ?? 10;
  const s = m * step, out: number[] = [];
  for (let v = Math.ceil(lo / s) * s; v <= hi + 1e-9; v += s) out.push(Number(v.toPrecision(12)));
  return out;
}

export function Plot2D({ scene, title }: { scene: Scene; title?: string }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const autoY = useMemo<[number, number]>(() => {
    if (scene.y) return scene.y;
    let lo = Infinity, hi = -Infinity;
    const [a, b] = scene.x;
    for (const c of scene.curves) for (let i = 0; i <= 200; i++) {
      const x = a + ((b - a) * i) / 200, v = c.fn(x);
      if (Number.isFinite(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
    }
    for (const r of scene.rects ?? []) { lo = Math.min(lo, r.h, 0); hi = Math.max(hi, r.h, 0); }
    if (!Number.isFinite(lo)) [lo, hi] = [-1, 1];
    lo = Math.min(lo, 0); hi = Math.max(hi, 0);
    const pad = (hi - lo || 1) * 0.12;
    return [Math.max(lo - pad, -1e4), Math.min(hi + pad, 1e4)];
  }, [scene]);
  const [view, setView] = useState<{ x: [number, number]; y: [number, number] } | null>(null);
  const v = view ?? { x: scene.x, y: autoY };
  const sx = (x: number) => PAD + ((x - v.x[0]) / (v.x[1] - v.x[0])) * (W - 2 * PAD);
  const sy = (y: number) => H - PAD - ((y - v.y[0]) / (v.y[1] - v.y[0])) * (H - 2 * PAD);
  const ix = (px: number) => v.x[0] + ((px - PAD) / (W - 2 * PAD)) * (v.x[1] - v.x[0]);
  const iy = (py: number) => v.y[0] + ((H - PAD - py) / (H - 2 * PAD)) * (v.y[1] - v.y[0]);
  const [hover, setHover] = useState<{ x: number; y: number } | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const drag = useRef<{ px: number; py: number; v: typeof v } | null>(null);

  const path = (fn: Fn1, from = v.x[0], to = v.x[1], swap = false) => {
    let d = "", pen = false;
    const N = 500;
    for (let i = 0; i <= N; i++) {
      const t = from + ((to - from) * i) / N, val = fn(t);
      const [X, Y] = swap ? [val, t] : [t, val];
      if (!Number.isFinite(val) || Math.abs(Y - v.y[0]) > 50 * (v.y[1] - v.y[0])) { pen = false; continue; }
      d += `${pen ? "L" : "M"}${sx(X).toFixed(1)},${sy(Y).toFixed(1)}`; pen = true;
    }
    return d;
  };
  const fillPath = (f: NonNullable<Scene["fills"]>[number]) => {
    const N = 300, top: string[] = [], bot: string[] = [];
    for (let i = 0; i <= N; i++) {
      const t = f.a + ((f.b - f.a) * i) / N;
      const T = f.top(t), B = f.bottom ? f.bottom(t) : 0;
      if (!Number.isFinite(T) || !Number.isFinite(B)) continue;
      const clampT = Math.max(Math.min(T, v.y[1] * 2), v.y[0] * 2);
      top.push(f.swapXY ? `${sx(clampT)},${sy(t)}` : `${sx(t)},${sy(clampT)}`);
      bot.push(f.swapXY ? `${sx(B)},${sy(t)}` : `${sx(t)},${sy(B)}`);
    }
    return `M${top.join("L")}L${bot.reverse().join("L")}Z`;
  };

  const zoom = (factor: number, cx?: number, cy?: number) => {
    const mx = cx ?? (v.x[0] + v.x[1]) / 2, my = cy ?? (v.y[0] + v.y[1]) / 2;
    setView({ x: [mx - (mx - v.x[0]) * factor, mx + (v.x[1] - mx) * factor], y: [my - (my - v.y[0]) * factor, my + (v.y[1] - my) * factor] });
  };
  const toPx = (e: React.MouseEvent | React.WheelEvent) => {
    const r = svgRef.current!.getBoundingClientRect();
    return { px: ((e.clientX - r.left) / r.width) * W, py: ((e.clientY - r.top) / r.height) * H };
  };
  const exportPng = () => {
    const svg = svgRef.current; if (!svg) return;
    const xml = new XMLSerializer().serializeToString(svg);
    const img = new Image();
    img.onload = () => {
      const c = document.createElement("canvas"); c.width = W * 2; c.height = H * 2;
      const g = c.getContext("2d")!; g.fillStyle = "#fff"; g.fillRect(0, 0, c.width, c.height); g.drawImage(img, 0, 0, c.width, c.height);
      const name = `${(title ?? "graph").replace(/[^A-Za-z0-9_-]+/g, "_") || "graph"}-${Date.now()}.png`;
      getBackend().then((be) => be.saveFile(name, c.toDataURL("image/png"), true)).then((where) => setSaved(where), (e) => setSaved(String(e)));
    };
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(xml);
  };

  const xt = niceTicks(v.x[0], v.x[1]), yt = niceTicks(v.y[0], v.y[1]);
  return (
    <div className="space-y-1">
      <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="w-full select-none rounded-lg border border-line bg-white text-[11px]" role="img" aria-label={title ?? "กราฟ"}
        xmlns="http://www.w3.org/2000/svg"
        onWheel={(e) => { const { px, py } = toPx(e); zoom(e.deltaY > 0 ? 1.15 : 1 / 1.15, ix(px), iy(py)); }}
        onMouseDown={(e) => { const p = toPx(e); drag.current = { ...p, v }; }}
        onMouseUp={() => (drag.current = null)} onMouseLeave={() => { drag.current = null; setHover(null); }}
        onMouseMove={(e) => {
          const { px, py } = toPx(e);
          setHover({ x: ix(px), y: iy(py) });
          if (drag.current) {
            const d = drag.current, dx = ((px - d.px) / (W - 2 * PAD)) * (d.v.x[1] - d.v.x[0]), dy = ((py - d.py) / (H - 2 * PAD)) * (d.v.y[1] - d.v.y[0]);
            setView({ x: [d.v.x[0] - dx, d.v.x[1] - dx], y: [d.v.y[0] + dy, d.v.y[1] + dy] });
          }
        }}>
        <rect x={0} y={0} width={W} height={H} fill="#fff" />
        {xt.map((t) => <line key={"gx" + t} x1={sx(t)} x2={sx(t)} y1={PAD} y2={H - PAD} stroke="#eef0f3" />)}
        {yt.map((t) => <line key={"gy" + t} y1={sy(t)} y2={sy(t)} x1={PAD} x2={W - PAD} stroke="#eef0f3" />)}
        <line x1={PAD} x2={W - PAD} y1={sy(0)} y2={sy(0)} stroke="#9aa3af" />
        <line y1={PAD} y2={H - PAD} x1={sx(0)} x2={sx(0)} stroke="#9aa3af" />
        {xt.map((t) => <text key={"tx" + t} x={sx(t)} y={H - PAD + 14} textAnchor="middle" fill="#6b7280">{t}</text>)}
        {yt.map((t) => <text key={"ty" + t} x={PAD - 4} y={sy(t) + 3} textAnchor="end" fill="#6b7280">{t}</text>)}
        <clipPath id="plotclip"><rect x={PAD} y={PAD} width={W - 2 * PAD} height={H - 2 * PAD} /></clipPath>
        <g clipPath="url(#plotclip)">
          {scene.fills?.map((f, i) => {
            if (!f.signed) return <path key={"f" + i} d={fillPath(f)} fill={f.color ?? C.fillPos} />;
            // signed: split into positive / negative parts
            const pos = { ...f, top: (x: number) => Math.max(f.top(x), 0) }, neg = { ...f, top: (x: number) => Math.min(f.top(x), 0) };
            return <g key={"f" + i}><path d={fillPath(pos)} fill={C.fillPos} /><path d={fillPath(neg)} fill={C.fillNeg} /></g>;
          })}
          {scene.rects?.map((r, i) => <rect key={"r" + i} x={sx(r.x0)} width={Math.max(0.5, sx(r.x1) - sx(r.x0))} y={Math.min(sy(r.h), sy(0))} height={Math.abs(sy(r.h) - sy(0))}
            fill={r.h >= 0 ? "rgba(59,130,246,0.22)" : "rgba(239,68,68,0.22)"} stroke={r.h >= 0 ? "#2563eb" : "#dc2626"} strokeWidth={1} />)}
          {scene.vlines?.map((l, i) => <line key={"v" + i} x1={sx(l.x)} x2={sx(l.x)} y1={PAD} y2={H - PAD} stroke="#6b7280" strokeDasharray={l.dashed ? "4 4" : undefined} />)}
          {scene.curves.map((c, i) => <path key={"c" + i} d={path(c.fn, c.from, c.to, c.swapXY)} fill="none" stroke={c.color} strokeWidth={2.2} strokeDasharray={c.dashed ? "6 5" : undefined} />)}
          {scene.polyline && <polyline points={scene.polyline.map(([x, y]) => `${sx(x)},${sy(y)}`).join(" ")} fill="none" stroke="#f59e0b" strokeWidth={2} />}
          {scene.polyline?.map(([x, y], i) => <circle key={"pp" + i} cx={sx(x)} cy={sy(y)} r={3} fill="#f59e0b" />)}
          {scene.points?.map((p, i) => <g key={"p" + i}><circle cx={sx(p.x)} cy={sy(p.y)} r={4} fill="#111827" />{p.label && <text x={sx(p.x) + 6} y={sy(p.y) - 6} fill="#111827">{p.label}</text>}</g>)}
        </g>
        {scene.curves.filter((c) => c.label).map((c, i) => <g key={"lg" + i}><rect x={W - PAD - 150} y={PAD + 4 + i * 16} width={10} height={3} fill={c.color} /><text x={W - PAD - 134} y={PAD + 9 + i * 16} fill="#374151">{c.label}</text></g>)}
        {hover && <text x={PAD + 4} y={PAD - 8} fill="#374151">({hover.x.toFixed(3)}, {hover.y.toFixed(3)})</text>}
      </svg>
      <div className="flex flex-wrap gap-1 text-xs">
        <button className="rounded border border-line px-2 py-0.5" onClick={() => zoom(1 / 1.3)}>ซูมเข้า</button>
        <button className="rounded border border-line px-2 py-0.5" onClick={() => zoom(1.3)}>ซูมออก</button>
        <button className="rounded border border-line px-2 py-0.5" onClick={() => setView(null)}>รีเซ็ต</button>
        <button className="rounded border border-line px-2 py-0.5" onClick={exportPng}>บันทึกภาพ PNG</button>
        <span className="text-muted">ลากเพื่อเลื่อน · หมุนล้อเมาส์เพื่อซูม</span>
        {saved && <span className="text-good">บันทึกแล้ว: {saved}</span>}
      </div>
    </div>
  );
}
