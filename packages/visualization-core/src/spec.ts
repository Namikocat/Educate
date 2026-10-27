/**
 * Declarative visualization specifications. Every spec (from the math engine, a lesson file,
 * or the optional AI tutor) is validated here before rendering; nothing executes code.
 */
import { compile, ExprError } from "./expr";

export type VizSpec =
  | { type: "function_plot"; expressions: string[]; domain: [number, number]; showIntersections?: boolean }
  | { type: "riemann"; f: string; a: number; b: number; n: number; method: "left" | "right" | "mid" }
  | { type: "area"; f: string; a: number; b: number; signed?: boolean }
  | { type: "area_between"; f: string; g: string; a: number; b: number; axis?: "x" | "y" }
  | { type: "arc"; f: string; a: number; b: number; n: number }
  | { type: "inverse"; f: string; g: string; a: number; b: number }
  | { type: "improper"; f: string; a: number; b: number; singularity?: number }
  | { type: "accumulation"; f: string; a: number; b: number }
  | { type: "tangent"; f: string; a: number; b: number; x0: number }
  | { type: "cross_section"; f: string; a: number; b: number; shape: "square" | "semicircle" | "equilateral" }
  | { type: "revolution"; f: string; g?: string; a: number; b: number; axis: "x" | "y"; axisValue?: number;
      method: "disk" | "washer" | "shell" | "surface" };

const TYPES = ["function_plot", "riemann", "area", "area_between", "arc", "inverse", "improper", "accumulation", "tangent", "cross_section", "revolution"];
const finite = (v: unknown) => typeof v === "number" && Number.isFinite(v) && Math.abs(v) < 1e6;

export function validateSpec(raw: unknown): { ok: true; spec: VizSpec } | { ok: false; error: string } {
  if (!raw || typeof raw !== "object") return { ok: false, error: "spec must be an object" };
  const s = raw as Record<string, unknown>;
  if (!TYPES.includes(s.type as string)) return { ok: false, error: `unsupported type ${String(s.type)}` };
  const exprs: unknown[] = s.type === "function_plot" ? ((s.expressions as unknown[]) ?? []) : [s.f, s.g].filter((e) => e !== undefined);
  if (exprs.length === 0 || exprs.length > 6) return { ok: false, error: "expressions missing" };
  for (const e of exprs) {
    if (typeof e !== "string") return { ok: false, error: "expression must be a string" };
    try { compile(e); } catch (err) { return { ok: false, error: `invalid expression: ${(err as ExprError).message}` }; }
  }
  if (s.type === "function_plot") {
    const d = s.domain as unknown[];
    if (!Array.isArray(d) || d.length !== 2 || !finite(d[0]) || !finite(d[1]) || (d[0] as number) >= (d[1] as number)) return { ok: false, error: "bad domain" };
  } else {
    if (!finite(s.a) || !finite(s.b) || (s.a as number) >= (s.b as number)) return { ok: false, error: "bad interval" };
    if ("n" in s && (!Number.isInteger(s.n) || (s.n as number) < 1 || (s.n as number) > 400)) return { ok: false, error: "bad n" };
  }
  if (s.type === "riemann" && !["left", "right", "mid"].includes(s.method as string)) return { ok: false, error: "bad method" };
  if (s.type === "revolution" && !["disk", "washer", "shell", "surface"].includes(s.method as string)) return { ok: false, error: "bad method" };
  return { ok: true, spec: s as unknown as VizSpec };
}

export function riemannRects(f: (x: number) => number, a: number, b: number, n: number, method: "left" | "right" | "mid") {
  const dx = (b - a) / n;
  const rects: { x0: number; x1: number; h: number }[] = [];
  let sum = 0;
  for (let i = 0; i < n; i++) {
    const x0 = a + i * dx, x1 = x0 + dx;
    const c = method === "left" ? x0 : method === "right" ? x1 : (x0 + x1) / 2;
    const h = f(c);
    rects.push({ x0, x1, h });
    sum += h * dx;
  }
  return { rects, sum, dx };
}

export function simpson(f: (x: number) => number, a: number, b: number, n = 2000): number {
  if (n % 2) n++;
  const h = (b - a) / n;
  let s = f(a) + f(b);
  for (let i = 1; i < n; i++) s += f(a + i * h) * (i % 2 ? 4 : 2);
  return (s * h) / 3;
}

export function polygonLength(f: (x: number) => number, a: number, b: number, n: number) {
  let L = 0;
  const pts: [number, number][] = [];
  for (let i = 0; i <= n; i++) {
    const x = a + ((b - a) * i) / n;
    pts.push([x, f(x)]);
    if (i) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  }
  return { L, pts };
}
