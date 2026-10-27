/**
 * Safe expression compiler for plotting only (never grading).
 * Same restricted grammar as the Python engine: allowlisted names, no eval / Function().
 * Produces a closure (x) => number.
 */
export type Fn1 = (x: number) => number;

const FUNCS: Record<string, (a: number, b?: number) => number> = {
  sin: Math.sin, cos: Math.cos, tan: Math.tan,
  sec: (a) => 1 / Math.cos(a), csc: (a) => 1 / Math.sin(a), cot: (a) => 1 / Math.tan(a),
  asin: Math.asin, arcsin: Math.asin, acos: Math.acos, arccos: Math.acos, atan: Math.atan, arctan: Math.atan,
  asec: (a) => Math.acos(1 / a), sinh: Math.sinh, cosh: Math.cosh, tanh: Math.tanh,
  ln: Math.log, log: (a, b) => (b === undefined ? Math.log(a) : Math.log(b) / Math.log(a)),
  exp: Math.exp, sqrt: Math.sqrt, abs: Math.abs, Abs: Math.abs,
  // real cube root used by sympy's root(x, 3)
  cbrt: Math.cbrt,
};
const CONSTS: Record<string, number> = { pi: Math.PI, e: Math.E, E: Math.E };
const NAMES = [...Object.keys(FUNCS), ...Object.keys(CONSTS), "x"].sort((a, b) => b.length - a.length);

type Tok = { k: "num" | "name" | "func" | "op"; t: string };
type Node = (x: number) => number;

export class ExprError extends Error {}

function tokenize(src: string): Tok[] {
  if (src.length > 400) throw new ExprError("expression too long");
  src = src.replace(/\*\*/g, "^").replace(/π/g, "pi").replace(/−/g, "-");
  const out: Tok[] = [];
  let i = 0;
  while (i < src.length) {
    const c = src[i];
    if (c === " ") { i++; continue; }
    const num = /^(\d+(\.\d+)?|\.\d+)/.exec(src.slice(i));
    if (num) { out.push({ k: "num", t: num[0] }); i += num[0].length; continue; }
    const word = /^[A-Za-z]+/.exec(src.slice(i));
    if (word) {
      let w = word[0], j = 0;
      while (j < w.length) {
        const name = NAMES.find((n) => w.startsWith(n, j));
        if (!name) throw new ExprError(`unknown name ${w}`);
        out.push({ k: name in FUNCS ? "func" : "name", t: name });
        j += name.length;
      }
      i += w.length; continue;
    }
    if ("+-*/^(),|".includes(c)) { out.push({ k: "op", t: c }); i++; continue; }
    throw new ExprError(`unexpected ${c}`);
  }
  if (out.length > 250) throw new ExprError("too complex");
  return out;
}

export function compile(src: string): Fn1 {
  const toks = tokenize(src);
  let p = 0, depth = 0, absDepth = 0;
  const peek = () => toks[p];
  const take = (t?: string) => {
    const tok = toks[p];
    if (!tok || (t !== undefined && tok.t !== t)) throw new ExprError(`expected ${t ?? "token"}`);
    p++; return tok;
  };
  const enter = () => { if (++depth > 40) throw new ExprError("too deep"); };
  const startsAtom = (t?: Tok) => !!t && (t.k !== "op" || t.t === "(" || (t.t === "|" && absDepth === 0));

  function expr(): Node {
    enter();
    let v = term();
    while (peek() && peek().k === "op" && (peek().t === "+" || peek().t === "-")) {
      const op = take().t, l = v, r = term();
      v = op === "+" ? (x) => l(x) + r(x) : (x) => l(x) - r(x);
    }
    depth--; return v;
  }
  function term(): Node {
    let v = unary();
    for (;;) {
      const t = peek();
      if (t && t.k === "op" && (t.t === "*" || t.t === "/")) {
        p++; const l = v, r = unary();
        v = t.t === "*" ? (x) => l(x) * r(x) : (x) => l(x) / r(x);
      } else if (startsAtom(t)) {
        const l = v, r = power(); v = (x) => l(x) * r(x);
      } else return v;
    }
  }
  function unary(): Node {
    const t = peek();
    if (t && t.k === "op" && (t.t === "-" || t.t === "+")) {
      p++; enter(); const v = unary(); depth--;
      return t.t === "-" ? (x) => -v(x) : v;
    }
    return power();
  }
  function power(): Node {
    const b = atom();
    if (peek() && peek().t === "^") { p++; enter(); const e = unary(); depth--; return (x) => Math.pow(b(x), e(x)); }
    return b;
  }
  function atom(): Node {
    const t = take();
    if (t.k === "num") { const v = parseFloat(t.t); return () => v; }
    if (t.k === "name") { if (t.t === "x") return (x) => x; const v = CONSTS[t.t]; return () => v; }
    if (t.k === "func") {
      const f = FUNCS[t.t];
      let ex: Node | null = null;
      if (peek() && peek().t === "^") { p++; ex = atom(); }
      enter();
      const args: Node[] = [];
      if (peek() && peek().t === "(") {
        p++; args.push(expr());
        while (peek() && peek().t === ",") { p++; args.push(expr()); }
        take(")");
      } else args.push(power());
      depth--;
      const call: Node = args.length === 1 ? (x) => f(args[0](x)) : (x) => f(args[0](x), args[1](x));
      return ex ? (x) => Math.pow(call(x), ex!(x)) : call;
    }
    if (t.t === "(") { const v = expr(); take(")"); return v; }
    if (t.t === "|") { absDepth++; const v = expr(); take("|"); absDepth--; return (x) => Math.abs(v(x)); }
    throw new ExprError(`unexpected ${t.t}`);
  }
  const root = expr();
  if (p !== toks.length) throw new ExprError("trailing input");
  // fractional powers of negative numbers: use real odd roots where sympy means a real root
  return (x) => { const v = root(x); return Number.isFinite(v) ? v : NaN; };
}

/** Sample f on [a,b]; NaN where undefined (renderer breaks the path there). */
export function sample(f: Fn1, a: number, b: number, n = 400): [number, number][] {
  const pts: [number, number][] = [];
  for (let i = 0; i <= n; i++) {
    const x = a + ((b - a) * i) / n;
    pts.push([x, f(x)]);
  }
  return pts;
}
