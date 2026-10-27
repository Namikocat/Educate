"""Chapter 5 - Integrals (sections 5.1-5.6)."""
from __future__ import annotations

import sympy as sp

from ..core import Built, Reject, Step, L, integral_tex, template
from ._h import R, eval_between, ftc_steps, poly_str, riemann, sub_steps, t, u, x, y, k, n

METHOD_TH = {"left": "จุดปลายซ้าย (left endpoint)", "right": "จุดปลายขวา (right endpoint)", "mid": "จุดกึ่งกลาง (midpoint)"}


def _riemann_problem(r, d, method):
    p = r.int("p", 1, 3)
    q = r.int("q", 0, 4)
    a = r.int("a", 0, 2)
    w = r.choice("w", [1, 2, 3, 4])
    nn = r.choice("n", {1: [2, 4], 2: [4, 5], 3: [6, 8]}[d])
    f = p * x**2 + q
    val, dx, pts = riemann(f, a, a + w, nn, method)
    k_ = sp.Symbol("k")
    if method == "left":
        term = f.subs(x, a + k_ * dx); lo, hi = 0, nn - 1
    elif method == "right":
        term = f.subs(x, a + k_ * dx); lo, hi = 1, nn
    else:
        term = f.subs(x, a + (k_ - R(1, 2)) * dx); lo, hi = 1, nn
    steps = [
        Step("riemann.dx", f"ความกว้างของแต่ละช่วงย่อย $\\Delta x = \\frac{{b-a}}{{n}} = \\frac{{{w}}}{{{nn}}}$", after=dx, check=("eq", dx, R(w, nn))),
        Step("riemann.points", f"จุดตัวแทนแบบ{METHOD_TH[method]}: " + ", ".join(f"${L(p_)}$" for p_ in pts)),
        Step("riemann.sum", "รวมพื้นที่สี่เหลี่ยม $\\sum f(c_k)\\,\\Delta x$",
             before_tex=rf"\sum_{{k={lo}}}^{{{hi}}} {L(term)}\cdot {L(dx)}", after=val,
             check=("eq", sum(f.subs(x, p_) for p_ in pts) * dx, val)),
    ]
    return Built(
        statement=f"จงประมาณพื้นที่ใต้กราฟ $f(x) = {L(f)}$ บนช่วง $[{a}, {a + w}]$ ด้วยสี่เหลี่ยม $n = {nn}$ รูป โดยใช้{METHOD_TH[method]}",
        display=rf"f(x) = {L(f)},\quad [{a},{a + w}],\ n={nn}",
        answer=val, verify=("sum", term * dx, k_, lo, hi), steps=steps,
        hints=["หา $\\Delta x$ ก่อน", "เขียนรายการจุดตัวแทนในแต่ละช่วงย่อย", "รวม $f(c_k)\\Delta x$ ทุกช่วง"],
        viz={"type": "riemann", "f": poly_str(f), "a": a, "b": a + w, "n": nn, "method": method},
        canonical=f"{f}|{a}|{w}|{nn}|{method}")


for _m, _id in [("left", "left_sum"), ("right", "right_sum"), ("mid", "midpoint_sum")]:
    template(f"calc.5.1.{_id}", "5.1", f"ผลรวมรีมันน์แบบ{METHOD_TH[_m]}", ["5.1.rectangles", f"5.1.{_m}"],
             {"p": (1, 3), "q": (0, 4), "a": (0, 2), "w": ("enum", [1, 2, 3, 4]), "n": ("enum", [2, 4, 5, 6, 8])},
             viz="riemann", errors=["wrong_dx", "wrong_endpoints"])(lambda r, d, _m=_m: _riemann_problem(r, d, _m))


@template("calc.5.1.upper_sum", "5.1", "ผลรวมบน (upper sum) ของฟังก์ชันลด", ["5.1.upper_lower", "5.1.rectangles"],
          {"c": (2, 20), "w": ("enum", [1, 2]), "n": ("enum", [2, 4, 5])}, viz="riemann")
def upper_sum(r, d):
    w = r.choice("w", [1, 2])
    c = r.int("c", w * w + 1, 20)
    nn = r.choice("n", [2, 4] if d == 1 else [4, 5])
    f = c - x**2
    val, dx, pts = riemann(f, 0, w, nn, "left")
    kk = sp.Symbol("k")
    steps = [
        Step("riemann.monotone", f"$f'(x) = -2x \\le 0$ บน $[0,{w}]$ ดังนั้น $f$ เป็นฟังก์ชันลด ค่าสูงสุดในแต่ละช่วงอยู่ที่จุดปลายซ้าย",
             check=("true", True)),
        Step("riemann.dx", f"$\\Delta x = {L(dx)}$", after=dx, check=("eq", dx, R(w, nn))),
        Step("riemann.sum", "ผลรวมบน = ผลรวมแบบจุดปลายซ้ายสำหรับฟังก์ชันลด", after=val,
             check=("eq", sum(f.subs(x, p_) for p_ in pts) * dx, val)),
    ]
    return Built(f"จงหาผลรวมบน (upper sum) ของ $f(x) = {L(f)}$ บน $[0,{w}]$ ด้วย $n={nn}$ ช่วงย่อยเท่ากัน",
                 rf"f(x)={L(f)},\ [0,{w}],\ n={nn}", val, ("sum", f.subs(x, kk * dx) * dx, kk, 0, nn - 1), steps,
                 ["ฟังก์ชันเพิ่มหรือลดบนช่วงนี้?", "ผลรวมบนใช้ค่าสูงสุดของ $f$ ในแต่ละช่วง"],
                 viz={"type": "riemann", "f": poly_str(f), "a": 0, "b": w, "n": nn, "method": "left"})


@template("calc.5.1.signed_midpoint", "5.1", "พื้นที่เชิงเครื่องหมาย (signed area) ด้วยผลรวมจุดกึ่งกลาง", ["5.1.signed_area"],
          {"m": (1, 3), "z": (1, 3), "w": (2, 4), "n": ("enum", [2, 4])}, viz="riemann", errors=["ignored_sign"])
def signed_midpoint(r, d):
    m = r.int("m", 1, 3)
    z = r.int("z", 1, 3)
    w = r.int("w", z + 1, 4)
    nn = r.choice("n", [2, 4])
    f = m * (x - z)
    val, dx, pts = riemann(f, 0, w, nn, "mid")
    steps = [
        Step("riemann.dx", f"$\\Delta x = {L(dx)}$", after=dx, check=("eq", dx, R(w, nn))),
        Step("area.signed", f"$f(x) < 0$ เมื่อ $x < {z}$ สี่เหลี่ยมที่อยู่ใต้แกน $x$ ให้ค่าติดลบ", check=("true", True)),
        Step("riemann.sum", "รวม $f(c_k)\\Delta x$ โดยคงเครื่องหมาย", after=val, check=("eq", sum(f.subs(x, p_) for p_ in pts) * dx, val)),
    ]
    return Built(f"จงประมาณพื้นที่เชิงเครื่องหมายของ $f(x) = {L(f)}$ บน $[0,{w}]$ ด้วยผลรวมจุดกึ่งกลาง $n={nn}$",
                 rf"f(x)={L(f)},\ [0,{w}],\ n={nn}", val, ("value", sp.integrate(f, (x, 0, w))), steps,
                 ["พื้นที่ใต้แกน $x$ นับเป็นค่าลบ", "สำหรับฟังก์ชันเชิงเส้น ผลรวมจุดกึ่งกลางเท่ากับค่าจริงพอดี"],
                 viz={"type": "riemann", "f": poly_str(f), "a": 0, "b": w, "n": nn, "method": "mid"})


@template("calc.5.1.estimate_error", "5.1", "ความคลาดเคลื่อนของการประมาณด้วยจุดปลายขวา", ["5.1.error", "5.1.refinement"],
          {"p": (1, 3), "w": ("enum", [1, 2, 3]), "n": ("enum", [2, 3, 4, 6])}, viz="riemann")
def estimate_error(r, d):
    p = r.int("p", 1, 3)
    w = r.choice("w", [1, 2, 3])
    nn = r.choice("n", [2, 3] if d == 1 else [4, 6])
    f = p * x**2
    val, dx, pts = riemann(f, 0, w, nn, "right")
    exact = sp.Rational(p * w**3, 3)
    ans = val - exact
    steps = [
        Step("riemann.sum", f"ผลรวมจุดปลายขวา $R_{{{nn}}} = {L(val)}$", after=val, check=("eq", sum(f.subs(x, p_) for p_ in pts) * dx, val)),
        Step("integral.exact", f"ค่าจริง $\\int_0^{{{w}}} {L(f)}\\,dx = {L(exact)}$", after=exact, check=("eq", sp.integrate(f, (x, 0, w)), exact)),
        Step("riemann.error", "ความคลาดเคลื่อน = ค่าประมาณ − ค่าจริง (เป็นบวกเพราะ $f$ เพิ่มขึ้น จุดปลายขวาประมาณเกิน)", after=ans,
             check=("eq", val - exact, ans)),
    ]
    return Built(f"ให้ $f(x) = {L(f)}$ บน $[0,{w}]$ จงหา $R_{{{nn}}} - A$ เมื่อ $R_{{{nn}}}$ คือผลรวมจุดปลายขวาและ $A$ คือพื้นที่จริง $\\left(A = \\frac{{{p}\\cdot {w}^3}}{{3}}\\right)$",
                 rf"R_{{{nn}}} - A,\quad f(x)={L(f)}", ans, ("value", riemann(f, 0, w, nn, "right")[0] - sp.integrate(f, (x, 0, w))), steps,
                 ["คำนวณ $R_n$ ก่อน", "เมื่อ $n$ เพิ่มขึ้น ความคลาดเคลื่อนจะลดลง"],
                 viz={"type": "riemann", "f": poly_str(f), "a": 0, "b": w, "n": nn, "method": "right"})


# ------------------------------------------------------------------ 5.2

SUM1 = n * (n + 1) / 2
SUM2 = n * (n + 1) * (2 * n + 1) / 6


@template("calc.5.2.evaluate_sum", "5.2", "หาค่าผลรวมจำกัดด้วยสูตรผลรวม", ["5.2.sigma", "5.2.formulas"],
          {"a": (-3, 4), "b": (-5, 5), "c": (-5, 5), "N": (5, 30)})
def evaluate_sum(r, d):
    kk = sp.Symbol("k")
    a = r.int("a", 1, 4) if d > 1 else 0
    if d == 1:
        r.params["a"] = 0
    b = r.int("b", -5, 5, exclude=(0,))
    c = r.int("c", -5, 5)
    N = r.int("N", 5, 12 if d == 1 else 30)
    term = a * kk**2 + b * kk + c
    s1, s2 = SUM1.subs(n, N), SUM2.subs(n, N)
    val = a * s2 + b * s1 + c * N
    steps = [
        Step("sigma.linearity", "ใช้สมบัติเชิงเส้นของซิกมา (sum laws) แยกผลรวมเป็นแต่ละพจน์",
             before_tex=rf"\sum_{{k=1}}^{{{N}}} ({L(term)})", after_tex=rf"{a}\sum k^2 + {b}\sum k + {c}\cdot {N}"),
        Step("sigma.formula_k", f"$\\sum_{{k=1}}^{{{N}}} k = \\frac{{{N}({N}+1)}}{{2}} = {s1}$", after=s1, check=("eq", sp.summation(kk, (kk, 1, N)), s1)),
        Step("sigma.formula_k2", f"$\\sum_{{k=1}}^{{{N}}} k^2 = \\frac{{{N}({N}+1)(2\\cdot{N}+1)}}{{6}} = {s2}$", after=s2, check=("eq", sp.summation(kk**2, (kk, 1, N)), s2)),
        Step("arith", "รวมผล", after=val, check=("eq", a * s2 + b * s1 + c * N, val)),
    ]
    return Built(f"จงหาค่าของ $\\displaystyle\\sum_{{k=1}}^{{{N}}} \\left({L(term)}\\right)$", rf"\sum_{{k=1}}^{{{N}}} \left({L(term)}\right)",
                 val, ("sum", term, kk, 1, N), steps, ["แยกผลรวมตามสมบัติเชิงเส้น", "$\\sum c = cN$ สำหรับค่าคงที่ $c$"])


@template("calc.5.2.closed_form", "5.2", "เขียนผลรวมให้อยู่ในรูปปิดของ n", ["5.2.formulas", "5.2.sigma"],
          {"a": (1, 6), "b": (-6, 6), "c": (0, 3)})
def closed_form(r, d):
    kk = sp.Symbol("k")
    a = r.int("a", 1, 6)
    b = r.int("b", -6, 6)
    c = r.int("c", 1, 3) if d == 3 else 0
    if d != 3:
        r.params["c"] = 0
    term = c * kk**2 + a * kk + b
    ans = sp.expand(c * SUM2 + a * SUM1 + b * n)
    steps = [
        Step("sigma.linearity", "แยกผลรวมด้วยสมบัติเชิงเส้น", before_tex=rf"\sum_{{k=1}}^{{n}}({L(term)})"),
        Step("sigma.formula", "แทนสูตร $\\sum k = \\frac{n(n+1)}{2}$, $\\sum k^2 = \\frac{n(n+1)(2n+1)}{6}$, $\\sum 1 = n$",
             after=ans, check=("eq", c * SUM2 + a * SUM1 + b * n, ans)),
    ]
    return Built(f"จงเขียน $\\displaystyle\\sum_{{k=1}}^{{n}} \\left({L(term)}\\right)$ ให้อยู่ในรูปนิพจน์ของ $n$",
                 rf"\sum_{{k=1}}^{{n}} \left({L(term)}\right)", ans, ("sum", term, kk, 1, n), steps,
                 ["ใช้สูตรผลรวมมาตรฐาน"], var=n, domain=(1, 12))


@template("calc.5.2.sum_laws", "5.2", "ใช้กฎของผลรวม (sum laws)", ["5.2.sum_laws"],
          {"A": (-20, 20), "B": (-20, 20), "p": (1, 5), "q": (1, 5), "s": (-4, 4), "N": (5, 25)})
def sum_laws(r, d):
    A, B = r.int("A", -20, 20), r.int("B", -20, 20)
    p, q = r.int("p", 1, 5), r.int("q", 1, 5)
    s = r.int("s", -4, 4, exclude=(0,)) if d > 1 else 0
    if d == 1:
        r.params["s"] = 0
    N = r.int("N", 5, 25)
    ans = p * A - q * B + s * N
    expr_tex = rf"\sum_{{k=1}}^{{{N}}} \left({p}a_k - {q}b_k {'+' if s >= 0 else '-'} {abs(s)}\right)"
    steps = [Step("sigma.linearity", "ผลรวมของผลบวก/ผลต่าง = ผลบวก/ผลต่างของผลรวม และดึงค่าคงที่ออกได้",
                  after_tex=rf"{p}\sum a_k - {q}\sum b_k + ({s})\cdot{N}"),
             Step("arith", f"แทนค่า $\\sum a_k = {A}$, $\\sum b_k = {B}$", after=sp.Integer(ans), check=("eq", sp.Integer(p * A - q * B + s * N), ans))]
    return Built(f"กำหนด $\\sum_{{k=1}}^{{{N}}} a_k = {A}$ และ $\\sum_{{k=1}}^{{{N}}} b_k = {B}$ จงหา ${expr_tex}$", expr_tex, sp.Integer(ans),
                 ("value", sp.Integer(p) * A - q * B + sp.summation(sp.Integer(s), (sp.Symbol("k"), 1, N))), steps,
                 ["$\\sum_{k=1}^{N} c = cN$"])


@template("calc.5.2.riemann_limit", "5.2", "ลิมิตของผลรวมรีมันน์", ["5.2.limit_sums", "5.2.sum_to_integral"],
          {"c": (1, 4), "a": (0, 2), "w": (1, 3), "deg": ("enum", [1, 2])})
def riemann_limit(r, d):
    kk = sp.Symbol("k")
    c = r.int("c", 1, 4)
    a = r.int("a", 0, 2) if d > 1 else 0
    if d == 1:
        r.params["a"] = 0
    w = r.int("w", 1, 3)
    deg = r.choice("deg", [1, 2] if d < 3 else [2])
    f = c * x**deg
    xk = a + w * kk / n
    term = sp.expand(f.subs(x, xk) * w / n)
    S_n = sp.simplify(sp.summation(term, (kk, 1, n)))
    lim = sp.limit(S_n, n, sp.oo)
    steps = [
        Step("riemann.identify", f"มองเป็นผลรวมรีมันน์แบบจุดปลายขวา: $\\Delta x = \\frac{{{w}}}{{n}}$, $x_k = {L(xk)}$, $f(x) = {L(f)}$ บน $[{a},{a + w}]$"),
        Step("sigma.formula", "ใช้สูตรผลรวมได้ $S_n$ เป็นนิพจน์ของ $n$", after=S_n, check=("eq", S_n, sp.summation(term, (kk, 1, n)))),
        Step("limit.infinity", "หาลิมิตเมื่อ $n\\to\\infty$", before=S_n, after=lim),
        Step("riemann.integral", f"ตรงกับ $\\int_{{{a}}}^{{{a + w}}} {L(f)}\\,dx$", after=lim, check=("eq", sp.integrate(f, (x, a, a + w)), lim)),
    ]
    return Built(f"จงหาค่าของ $\\displaystyle\\lim_{{n\\to\\infty}} \\sum_{{k=1}}^{{n}} {L(term)}$", rf"\lim_{{n\to\infty}}\sum_{{k=1}}^{{n}} {L(sp.factor(term))}",
                 lim, ("value", sp.integrate(f, (x, a, a + w))), steps,
                 ["ระบุ $\\Delta x$ และ $x_k$", "ผลรวมนี้คืออินทิกรัลจำกัดเขตของฟังก์ชันใด?"],
                 viz={"type": "riemann", "f": poly_str(f), "a": a, "b": a + w, "n": 8, "method": "right"})


@template("calc.5.2.shifted_index", "5.2", "ผลรวมที่ดัชนีไม่ได้เริ่มที่ 1", ["5.2.sigma", "5.2.formulas"],
          {"m": (2, 10), "N": (7, 30), "pw": ("enum", [1, 2, 3])})
def shifted_index(r, d):
    kk = sp.Symbol("k")
    pw = r.choice("pw", {1: [1], 2: [2], 3: [3]}[d])
    m = r.int("m", 2, 10)
    N = r.int("N", m + 5, 30)
    total = sp.summation(kk**pw, (kk, 1, N))
    head = sp.summation(kk**pw, (kk, 1, m - 1))
    val = total - head
    steps = [
        Step("sigma.split", f"$\\sum_{{k={m}}}^{{{N}}} k^{pw} = \\sum_{{k=1}}^{{{N}}} k^{pw} - \\sum_{{k=1}}^{{{m - 1}}} k^{pw}$"),
        Step("sigma.formula", f"ด้วยสูตรผลรวม: ${total} - {head}$", after=val, check=("eq", total - head, val)),
    ]
    return Built(f"จงหาค่าของ $\\displaystyle\\sum_{{k={m}}}^{{{N}}} k^{{{pw}}}$", rf"\sum_{{k={m}}}^{{{N}}} k^{{{pw}}}", val,
                 ("sum", kk**pw, kk, m, N), steps, ["ลบส่วนต้นที่ไม่ต้องการออก"])


@template("calc.5.2.telescoping", "5.2", "ผลรวมแบบยุบตัว (telescoping)", ["5.2.sigma"], {"c": (1, 12), "N": (4, 50)})
def telescoping(r, d):
    kk = sp.Symbol("k")
    c = r.int("c", 1, 12)
    N = r.int("N", 4, 10 if d == 1 else 50)
    term = c / (kk * (kk + 1))
    val = c * (1 - R(1, N + 1))
    steps = [
        Step("algebra.partial_fraction", f"$\\frac{{1}}{{k(k+1)}} = \\frac{{1}}{{k}} - \\frac{{1}}{{k+1}}$", check=("eq", (1 / (x * (x + 1))), 1 / x - 1 / (x + 1))),
        Step("sigma.telescope", "พจน์กลางหักล้างกันหมด เหลือพจน์แรกและพจน์สุดท้าย",
             after_tex=rf"{c}\left(1 - \frac{{1}}{{{N + 1}}}\right)", after=val, check=("eq", sp.summation(term, (kk, 1, N)), val)),
    ]
    return Built(f"จงหาค่าของ $\\displaystyle\\sum_{{k=1}}^{{{N}}} \\frac{{{c}}}{{k(k+1)}}$", rf"\sum_{{k=1}}^{{{N}}} \frac{{{c}}}{{k(k+1)}}", val,
                 ("sum", term, kk, 1, N), steps, ["แยก $\\frac{1}{k(k+1)}$ เป็นผลต่างของเศษส่วน"])


# ------------------------------------------------------------------ 5.3

@template("calc.5.3.geometric_semicircle", "5.3", "อินทิกรัลจำกัดเขตจากพื้นที่เชิงเรขาคณิต (ครึ่งวงกลม)", ["5.3.geometric"],
          {"r": (1, 6), "c": (1, 4), "part": ("enum", ["half", "quarter"])}, viz="area")
def geometric_semicircle(r_, d):
    rr = r_.int("r", 1, 6)
    c = r_.int("c", 1, 4) if d > 1 else 1
    if d == 1:
        r_.params["c"] = 1
    part = r_.choice("part", ["half", "quarter"])
    f = c * sp.sqrt(rr**2 - x**2)
    a = -rr if part == "half" else 0
    val = c * sp.pi * rr**2 / (2 if part == "half" else 4)
    steps = [
        Step("geometry.identify", f"$y = \\sqrt{{{rr**2} - x^2}}$ คือครึ่งบนของวงกลมรัศมี ${rr}$ ช่วง $[{a},{rr}]$ จึงเป็น{'ครึ่ง' if part == 'half' else 'หนึ่งในสี่ของ'}วงกลม"),
        Step("geometry.area", "พื้นที่ $= c\\cdot$ (ส่วนของ $\\pi r^2$)", after=val, check=("eq", sp.integrate(f, (x, a, rr)), val)),
    ]
    return Built(f"จงหาค่า ${integral_tex(f, a, rr)}$ โดยใช้พื้นที่ทางเรขาคณิต", integral_tex(f, a, rr), val, ("definite", f, a, rr), steps,
                 ["ยกกำลังสองทั้งสองข้างของ $y=\\sqrt{r^2-x^2}$ แล้วดูว่าเป็นรูปอะไร"],
                 viz={"type": "area", "f": poly_str(f), "a": a, "b": rr})


@template("calc.5.3.linearity", "5.3", "สมบัติเชิงเส้นของอินทิกรัลจำกัดเขต", ["5.3.properties"],
          {"A": (-9, 9), "B": (-9, 9), "p": (1, 5), "q": (1, 5), "rev": ("enum", [0, 1])})
def linearity(r, d):
    A, B = r.int("A", -9, 9), r.int("B", -9, 9)
    p, q = r.int("p", 1, 5), r.int("q", 1, 5)
    rev = r.choice("rev", [0] if d == 1 else [0, 1])
    a_, b_ = 1, 4
    ans = (p * A - q * B) * (-1 if rev else 1)
    lo, hi = (b_, a_) if rev else (a_, b_)
    f0, g0 = sp.Integer(A) / (b_ - a_), sp.Integer(B) / (b_ - a_)  # witness functions with the given integrals
    steps = [Step("integral.linearity", "ดึงค่าคงที่ออกและแยกผลบวก/ผลต่าง", after_tex=rf"{p}\int f - {q}\int g")]
    if rev:
        steps.append(Step("integral.reverse", "สลับขอบเขตทำให้เครื่องหมายเปลี่ยน: $\\int_b^a = -\\int_a^b$"))
    steps.append(Step("arith", "แทนค่า", after=sp.Integer(ans), check=("eq", sp.integrate(p * f0 - q * g0, (x, lo, hi)), ans)))
    st = rf"\int_{{{lo}}}^{{{hi}}} \left({p}f(x) - {q}g(x)\right)dx"
    return Built(f"กำหนด $\\int_1^4 f(x)\\,dx = {A}$ และ $\\int_1^4 g(x)\\,dx = {B}$ จงหา ${st}$", st, sp.Integer(ans),
                 ("value", sp.integrate(p * f0 - q * g0, (x, lo, hi))), steps, ["ใช้สมบัติเชิงเส้น", "ระวังทิศทางของขอบเขต"])


@template("calc.5.3.additivity", "5.3", "สมบัติการบวกช่วง (additivity)", ["5.3.properties"],
          {"A": (-12, 12), "B": (-12, 12)})
def additivity(r, d):
    A, B = r.int("A", -12, 12), r.int("B", -12, 12)
    if A == B:
        raise Reject("trivial")
    a_, b_, c_ = -1, 2, 5
    ans = A - B
    w = sp.Piecewise((sp.Integer(B) / (b_ - a_), x < b_), (sp.Integer(A - B) / (c_ - b_), True))
    steps = [Step("integral.additivity", f"$\\int_{{{a_}}}^{{{c_}}} f = \\int_{{{a_}}}^{{{b_}}} f + \\int_{{{b_}}}^{{{c_}}} f$"),
             Step("arith", f"$\\int_{{{b_}}}^{{{c_}}} f = {A} - ({B})$", after=sp.Integer(ans), check=("eq", sp.integrate(w, (x, b_, c_)), ans))]
    q = rf"\int_{{{b_}}}^{{{c_}}} f(x)\,dx" if d < 3 else rf"\int_{{{c_}}}^{{{b_}}} f(x)\,dx"
    if d == 3:
        ans = -ans
        steps.append(Step("integral.reverse", "สลับขอบเขต เครื่องหมายเปลี่ยน", after=sp.Integer(ans), check=("eq", -sp.integrate(w, (x, b_, c_)), ans)))
    return Built(f"กำหนด $\\int_{{{a_}}}^{{{c_}}} f(x)\\,dx = {A}$ และ $\\int_{{{a_}}}^{{{b_}}} f(x)\\,dx = {B}$ จงหา ${q}$", q, sp.Integer(ans),
                 ("value", sp.integrate(w, (x, b_, c_)) * (-1 if d == 3 else 1)), steps, ["แบ่งช่วงอินทิเกรตเป็นสองส่วน"])


@template("calc.5.3.signed_linear", "5.3", "พื้นที่เชิงเครื่องหมายของฟังก์ชันเชิงเส้น", ["5.3.signed_area", "5.3.geometric"],
          {"m": (-3, 3), "c": (-6, 6), "a": (-3, 0), "b": (1, 4)}, viz="area")
def signed_linear(r, d):
    m = r.int("m", -3, 3, exclude=(0,))
    c = r.int("c", -6, 6)
    a, b = r.int("a", -3, 0), r.int("b", 1, 4)
    f = m * x + c
    val = eval_between(m * x**2 / 2 + c * x, a, b)
    z = sp.Rational(-c, m)
    crosses = a < z < b
    steps = [Step("area.signed", f"กราฟ{'ตัดแกน x ที่ $x = ' + L(z) + '$ ส่วนที่อยู่ใต้แกนให้ค่าลบ' if crosses else 'ไม่ตัดแกน x ในช่วงนี้'}"),
             Step("geometry.trapezoid", "รวมพื้นที่สามเหลี่ยม/สี่เหลี่ยมคางหมูโดยคงเครื่องหมาย", after=val,
                  check=("eq", sp.integrate(f, (x, a, b)), val))]
    return Built(f"จงหาค่า ${integral_tex(f, a, b)}$ โดยตีความเป็นพื้นที่เชิงเครื่องหมาย", integral_tex(f, a, b), val, ("definite", f, a, b), steps,
                 ["หาจุดที่เส้นตรงตัดแกน $x$", "พื้นที่ใต้แกน $x$ มีค่าเป็นลบ"], viz={"type": "area", "f": poly_str(f), "a": a, "b": b, "signed": True})


@template("calc.5.3.average_value", "5.3", "ค่าเฉลี่ยของฟังก์ชัน", ["5.3.average"],
          {"p": (-3, 3), "q": (-4, 4), "s": (-5, 5), "a": (-2, 1), "w": (1, 4)}, viz="area")
def average_value(r, d):
    p = r.int("p", -3, 3, exclude=(0,))
    q = r.int("q", -4, 4)
    s = r.int("s", -5, 5)
    a = r.int("a", -2, 1)
    w = r.int("w", 1, 4)
    b = a + w
    f = p * x**2 + q * x + s
    F = p * x**3 / 3 + q * x**2 / 2 + s * x
    I = eval_between(F, a, b)
    av = I / w
    steps = ftc_steps(f, F, a, b) + [Step("average.formula", f"$\\operatorname{{av}}(f) = \\frac{{1}}{{b-a}}\\int_a^b f\\,dx = \\frac{{1}}{{{w}}}\\cdot {L(I)}$",
                                          after=av, check=("eq", I / w, av))]
    return Built(f"จงหาค่าเฉลี่ยของ $f(x) = {L(f)}$ บนช่วง $[{a},{b}]$", rf"\operatorname{{av}}(f),\ f(x)={L(f)},\ [{a},{b}]", av,
                 ("value", sp.integrate(f, (x, a, b)) / (b - a)), steps, ["$\\operatorname{av}(f)=\\frac{1}{b-a}\\int_a^b f(x)dx$"],
                 viz={"type": "area", "f": poly_str(f), "a": a, "b": b, "signed": True})


@template("calc.5.3.piecewise", "5.3", "อินทิกรัลของฟังก์ชันเป็นช่วง (piecewise)", ["5.3.piecewise", "5.3.properties"],
          {"p": (-4, 4), "m": (-3, 3), "c": (-3, 3), "s": (0, 2), "a": (-3, -1), "b": (3, 5)})
def piecewise(r, d):
    p = r.int("p", -4, 4, exclude=(0,))
    m = r.int("m", -3, 3, exclude=(0,))
    c = r.int("c", -3, 3)
    s = r.int("s", 0, 2)
    a, b = r.int("a", -3, -1), r.int("b", 3, 5)
    f = sp.Piecewise((sp.Integer(p), x < s), (m * x + c, True))
    left = p * (s - a)
    right = eval_between(m * x**2 / 2 + c * x, s, b)
    val = left + right
    steps = [Step("integral.additivity", f"แยกช่วงที่ $x = {s}$: $\\int_{{{a}}}^{{{s}}} {p}\\,dx + \\int_{{{s}}}^{{{b}}} ({L(m * x + c)})\\,dx$"),
             Step("integral.constant", f"ส่วนแรก $= {p}\\cdot({s}-({a})) = {left}$", after=sp.Integer(left), check=("eq", sp.integrate(sp.Integer(p), (x, a, s)), left)),
             Step("ftc.part2", "ส่วนที่สอง", after=right, check=("eq", sp.integrate(m * x + c, (x, s, b)), right)),
             Step("arith", "รวมสองส่วน", after=val, check=("eq", left + right, val))]
    disp = rf"\int_{{{a}}}^{{{b}}} f(x)\,dx,\quad f(x)=\begin{{cases}} {p} & x<{s} \\ {L(m * x + c)} & x\ge {s}\end{{cases}}"
    return Built(f"จงหา ${disp}$", disp, val, ("definite", f, a, b), steps, ["แบ่งช่วงอินทิเกรตตรงจุดที่นิยามฟังก์ชันเปลี่ยน"])


# ------------------------------------------------------------------ 5.4

G_FUNCS = [("poly", lambda tt: tt**2 + 1), ("cos", lambda tt: sp.cos(tt**2)), ("sqrt", lambda tt: sp.sqrt(1 + tt**3)),
           ("exp", lambda tt: sp.exp(-tt**2)), ("log", lambda tt: sp.log(1 + tt**2))]


@template("calc.5.4.ftc1_basic", "5.4", "FTC ส่วนที่ 1: อนุพันธ์ของฟังก์ชันสะสม", ["5.4.ftc1", "5.4.accumulation"],
          {"g": ("enum", [g[0] for g in G_FUNCS]), "a": (0, 3)})
def ftc1_basic(r, d):
    name = r.choice("g", [g[0] for g in G_FUNCS])
    g = dict(G_FUNCS)[name](t)
    a = r.int("a", 0, 3)
    F = sp.Integral(g, (t, a, x))
    ans = g.subs(t, x)
    steps = [Step("ftc.part1", "FTC ส่วนที่ 1: ถ้า $f$ ต่อเนื่อง แล้ว $\\frac{d}{dx}\\int_a^x f(t)\\,dt = f(x)$", assumptions=["f ต่อเนื่องบนช่วงที่พิจารณา"],
                  before_tex=rf"\frac{{d}}{{dx}}{L(F)}", after=ans, check=("eq", sp.diff(F, x), ans))]
    return Built(f"ให้ $F(x) = {L(F)}$ จงหา $F'(x)$", rf"\frac{{d}}{{dx}}{L(F)}", ans, ("derivative", F), steps,
                 ["ไม่ต้องหาอินทิกรัลก่อน", "แทน $t$ ด้วย $x$ ในตัวถูกอินทิเกรต"], domain=(0.2, 1.5))


UPPER = [("x2", x**2), ("x3", x**3), ("sin", sp.sin(x)), ("sqrt", sp.sqrt(x)), ("lin", 3 * x + 1)]


@template("calc.5.4.ftc1_chain", "5.4", "FTC ส่วนที่ 1 กับกฎลูกโซ่ (ขอบเขตบนเป็นฟังก์ชัน)", ["5.4.ftc1", "5.4.variable_limits"],
          {"g": ("enum", [g[0] for g in G_FUNCS]), "up": ("enum", [p[0] for p in UPPER]), "a": (0, 2)}, errors=["forgot_chain_rule"])
def ftc1_chain(r, d):
    g = dict(G_FUNCS)[r.choice("g", [gg[0] for gg in G_FUNCS])](t)
    up = dict(UPPER)[r.choice("up", [p[0] for p in UPPER])]
    a = r.int("a", 0, 2)
    F = sp.Integral(g, (t, a, up))
    ans = g.subs(t, up) * sp.diff(up, x)
    steps = [Step("ftc.part1", f"ให้ $u = {L(up)}$ ได้ $\\frac{{d}}{{du}}\\int_{{{a}}}^{{u}} f(t)dt = f(u)$"),
             Step("diff.chain", f"กฎลูกโซ่: คูณด้วย $\\frac{{du}}{{dx}} = {L(sp.diff(up, x))}$", after=ans, check=("eq", sp.diff(F, x), ans))]
    return Built(f"จงหา $\\dfrac{{d}}{{dx}}{L(F)}$", rf"\frac{{d}}{{dx}}{L(F)}", ans, ("derivative", F), steps,
                 ["ขอบเขตบนเป็นฟังก์ชันของ $x$ ต้องใช้กฎลูกโซ่"], domain=(0.2, 1.4))


@template("calc.5.4.ftc1_both_limits", "5.4", "FTC เมื่อขอบเขตทั้งสองเป็นฟังก์ชัน", ["5.4.ftc1", "5.4.variable_limits"],
          {"g": ("enum", [g[0] for g in G_FUNCS]), "up": ("enum", [p[0] for p in UPPER]), "lo": ("enum", ["x", "2x", "-x"])})
def ftc1_both(r, d):
    g = dict(G_FUNCS)[r.choice("g", [gg[0] for gg in G_FUNCS])](t)
    up = dict(UPPER)[r.choice("up", [p[0] for p in UPPER])]
    lo = {"x": x, "2x": 2 * x, "-x": -x}[r.choice("lo", ["x", "2x", "-x"])]
    if sp.simplify(up - lo) == 0:
        raise Reject("same limits")
    F = sp.Integral(g, (t, lo, up))
    ans = g.subs(t, up) * sp.diff(up, x) - g.subs(t, lo) * sp.diff(lo, x)
    steps = [Step("integral.additivity", "แยกที่ค่าคงที่ $c$: $\\int_{v}^{u} = \\int_c^{u} - \\int_c^{v}$"),
             Step("ftc.part1_chain", "ใช้ FTC + กฎลูกโซ่ทั้งสองพจน์: $f(u)u' - f(v)v'$", after=ans, check=("eq", sp.diff(F, x), ans))]
    return Built(f"จงหา $\\dfrac{{d}}{{dx}}{L(F)}$", rf"\frac{{d}}{{dx}}{L(F)}", ans, ("derivative", F), steps,
                 ["เขียนเป็นผลต่างของอินทิกรัลสองตัวที่มีขอบเขตล่างคงที่"], domain=(0.2, 1.2))


@template("calc.5.4.ftc2_poly", "5.4", "FTC ส่วนที่ 2: อินทิกรัลของพหุนาม", ["5.4.ftc2"],
          {"p": (-4, 4), "q": (-5, 5), "s": (-5, 5), "a": (-2, 1), "b": (2, 4)}, viz="area")
def ftc2_poly(r, d):
    p = r.int("p", -4, 4, exclude=(0,))
    q = r.int("q", -5, 5)
    s = r.int("s", -5, 5)
    a, b = r.int("a", -2, 1), r.int("b", 2, 4)
    deg = 3 if d == 3 else 2
    f = p * x**deg + q * x + s
    F = sp.integrate(f, x)
    val = eval_between(F, a, b)
    return Built(f"จงหาค่า ${integral_tex(f, a, b)}$", integral_tex(f, a, b), val, ("definite", f, a, b), ftc_steps(f, F, a, b),
                 ["ใช้กฎกำลัง $\\int x^n dx = \\frac{x^{n+1}}{n+1}$", "แทนขอบเขตบนลบขอบเขตล่าง"],
                 viz={"type": "area", "f": poly_str(f), "a": a, "b": b, "signed": True})


TRIG_DEF = [("cos", lambda c: c * sp.cos(x), sp.pi / 2), ("sin", lambda c: c * sp.sin(x), sp.pi),
            ("sec2", lambda c: c * sp.sec(x)**2, sp.pi / 4), ("exp", lambda c: c * sp.exp(x), sp.log(3)),
            ("recip", lambda c: c / x, sp.E**2)]


@template("calc.5.4.ftc2_transcendental", "5.4", "FTC ส่วนที่ 2: ตรีโกณ เอกซ์โพเนนเชียล และ 1/x", ["5.4.ftc2"],
          {"f": ("enum", [t_[0] for t_ in TRIG_DEF]), "c": (1, 6)}, viz="area")
def ftc2_trans(r, d):
    name = r.choice("f", [t_[0] for t_ in TRIG_DEF])
    c = r.int("c", 1, 6)
    _, mk, b = next(tt for tt in TRIG_DEF if tt[0] == name)
    f = mk(c)
    a = 1 if name == "recip" else 0
    F = {"cos": c * sp.sin(x), "sin": -c * sp.cos(x), "sec2": c * sp.tan(x), "exp": c * sp.exp(x), "recip": c * sp.log(x)}[name]
    val = eval_between(F, a, b)
    return Built(f"จงหาค่า ${integral_tex(f, a, b)}$", integral_tex(f, a, b), val, ("definite", f, a, b), ftc_steps(f, F, a, b),
                 ["นึกถึงฟังก์ชันที่อนุพันธ์เท่ากับตัวถูกอินทิเกรต"], domain=(0.3, 0.7),
                 viz={"type": "area", "f": poly_str(f), "a": a, "b": float(b)})


@template("calc.5.4.total_area", "5.4", "พื้นที่ทั้งหมด (total area) เมื่อกราฟตัดแกน x", ["5.4.total_area", "5.3.signed_area"],
          {"r1": (-3, 0), "r2": (1, 3), "c": (1, 3), "b": (2, 5)}, viz="area", errors=["used_signed_area"])
def total_area(r, d):
    r1, r2 = r.int("r1", -3, 0), r.int("r2", 1, 3)
    c = r.int("c", 1, 3)
    b = r.int("b", r2 + 1, r2 + 2)
    f = c * (x - r1) * (x - r2)
    F = sp.integrate(f, x)
    a = r1
    p1, p2 = eval_between(F, a, r2), eval_between(F, r2, b)
    val = abs(p1) + abs(p2)
    steps = [Step("roots", f"หาจุดตัดแกน $x$: $x={r1}, {r2}$ แบ่งช่วงเป็น $[{a},{r2}]$ และ $[{r2},{b}]$"),
             Step("ftc.part2", f"$\\int_{{{a}}}^{{{r2}}} f = {L(p1)}$ (ใต้แกน)", after=p1, check=("eq", sp.integrate(f, (x, a, r2)), p1)),
             Step("ftc.part2", f"$\\int_{{{r2}}}^{{{b}}} f = {L(p2)}$", after=p2, check=("eq", sp.integrate(f, (x, r2, b)), p2)),
             Step("area.total", "พื้นที่ทั้งหมด = ผลรวมค่าสัมบูรณ์", after=val, check=("eq", abs(p1) + abs(p2), val))]
    roots = sorted(sp.solve(f, x))
    pts = [a] + [rt for rt in roots if a < rt < b] + [b]
    ref = sum(abs(sp.integrate(f, (x, pts[i], pts[i + 1]))) for i in range(len(pts) - 1))
    return Built(f"จงหาพื้นที่ทั้งหมดที่ปิดล้อมระหว่างกราฟ $y = {L(sp.expand(f))}$ กับแกน $x$ บนช่วง $[{a},{b}]$",
                 rf"y={L(sp.expand(f))},\ [{a},{b}]", val, ("value", ref), steps,
                 ["พื้นที่ทั้งหมดไม่เท่ากับอินทิกรัลจำกัดเขตเมื่อกราฟอยู่ใต้แกน", "แยกช่วงที่รากของ $f$"],
                 viz={"type": "area", "f": poly_str(sp.expand(f)), "a": a, "b": b, "signed": True})


# ------------------------------------------------------------------ 5.5

@template("calc.5.5.linear_inner", "5.5", "การแทนค่า u = ax + b", ["5.5.substitution", "5.5.antiderivative", "5.5.verify"],
          {"a": (2, 6), "b": (-5, 5), "c": (1, 6), "m": ("enum", ["2", "3", "4", "5", "6", "-2", "-3", "1/2", "3/2"])}, "antiderivative")
def linear_inner(r, d):
    a = r.int("a", 2, 6)
    b = r.int("b", -5, 5, exclude=(0,))
    c = r.int("c", 1, 6)
    m = sp.Rational(r.choice("m", {1: ["2", "3", "4"], 2: ["5", "6", "-2", "-3"], 3: ["1/2", "3/2", "-3"]}[d]))
    g = a * x + b
    f = c * g**m
    F_u = c * u**(m + 1) / (a * (m + 1))
    ans = F_u.subs(u, g)
    dom = (float(-b / a) + 0.5, float(-b / a) + 3)
    return Built(f"จงหา ${integral_tex(f)}$", integral_tex(f), ans, ("antiderivative", f), sub_steps(f, g, sp.Integer(a), F_u, ans),
                 ["ให้ $u$ เป็นนิพจน์ข้างในวงเล็บ", "อย่าลืมหารด้วย $a$ จาก $du = a\\,dx$"], "antiderivative", domain=dom)


@template("calc.5.5.power_chain", "5.5", "การแทนค่า u = xᵐ + c (กฎลูกโซ่ย้อนกลับ)", ["5.5.substitution", "5.5.chain_reverse", "5.5.verify"],
          {"m": (2, 4), "c": (1, 9), "p": (2, 6), "k": (1, 6)}, "antiderivative")
def power_chain(r, d):
    m = r.int("m", 2, 3 if d < 3 else 4)
    c = r.int("c", 1, 9)
    p = r.int("p", 2, 6)
    kk = r.int("k", 1, 6)
    g = x**m + c
    f = kk * x**(m - 1) * g**p
    du = m * x**(m - 1)
    F_u = sp.Rational(kk, m) * u**(p + 1) / (p + 1)
    ans = F_u.subs(u, g)
    return Built(f"จงหา ${integral_tex(f)}$", integral_tex(f), ans, ("antiderivative", f), sub_steps(f, g, du, F_u, ans),
                 [f"สังเกตว่า $x^{{{m - 1}}}$ คือ (ค่าคงที่ ×) อนุพันธ์ของ $x^{m}$"], "antiderivative")


@template("calc.5.5.trig_power", "5.5", "การแทนค่ากับฟังก์ชันตรีโกณ (sinⁿx cos x)", ["5.5.substitution"],
          {"n": (2, 7), "kind": ("enum", ["sin", "cos"]), "a": (1, 3)}, "antiderivative")
def trig_power(r, d):
    nn = r.int("n", 2, 7)
    kind = r.choice("kind", ["sin", "cos"])
    a = r.int("a", 1, 3) if d > 1 else 1
    if d == 1:
        r.params["a"] = 1
    if kind == "sin":
        g, f, du = sp.sin(a * x), sp.sin(a * x)**nn * sp.cos(a * x), a * sp.cos(a * x)
        F_u = u**(nn + 1) / (a * (nn + 1))
    else:
        g, f, du = sp.cos(a * x), sp.cos(a * x)**nn * sp.sin(a * x), -a * sp.sin(a * x)
        F_u = -u**(nn + 1) / (a * (nn + 1))
    ans = F_u.subs(u, g)
    return Built(f"จงหา ${integral_tex(f)}$", integral_tex(f), ans, ("antiderivative", f), sub_steps(f, g, du, F_u, ans),
                 [f"ลอง $u = {L(g)}$"], "antiderivative", domain=(0.1, 1.2))


@template("calc.5.5.exp_sub", "5.5", "การแทนค่าในฟังก์ชันเอกซ์โพเนนเชียล", ["5.5.substitution"],
          {"form": ("enum", ["xexp", "cosexp", "sqrt"]), "a": (-3, 3), "c": (1, 5)}, "antiderivative")
def exp_sub(r, d):
    form = r.choice("form", ["xexp", "cosexp"] if d < 3 else ["sqrt", "cosexp"])
    a = r.int("a", -3, 3, exclude=(0,))
    c = r.int("c", 1, 5)
    if form == "xexp":
        g = a * x**2; f = c * x * sp.exp(g); du = 2 * a * x; F_u = sp.Rational(c, 2 * a) * sp.exp(u)
    elif form == "cosexp":
        g = sp.sin(a * x); f = c * sp.cos(a * x) * sp.exp(g); du = a * sp.cos(a * x); F_u = sp.Rational(c, a) * sp.exp(u)
    else:
        g = sp.sqrt(x); f = c * sp.exp(a * g) / sp.sqrt(x); du = 1 / (2 * sp.sqrt(x)); F_u = sp.Rational(2 * c, a) * sp.exp(a * u)
    ans = F_u.subs(u, g)
    return Built(f"จงหา ${integral_tex(f)}$", integral_tex(f), ans, ("antiderivative", f), sub_steps(f, g, du, F_u, ans),
                 ["ให้ $u$ เป็นเลขชี้กำลังหรือส่วนที่อยู่ข้างใน"], "antiderivative", domain=(0.2, 2))


@template("calc.5.5.log_sub", "5.5", "การแทนค่าที่ให้ผลเป็นลอการิทึม", ["5.5.substitution", "7.2.integration"],
          {"a": (1, 3), "b": (-4, 4), "c": (5, 15), "k": (1, 5)}, "antiderivative")
def log_sub(r, d):
    a = r.int("a", 1, 3)
    b = r.int("b", -4, 4)
    c = r.int("c", 5, 15)
    if b * b - 4 * a * c >= 0:
        raise Reject("must stay positive")
    kk = r.int("k", 1, 5)
    g = a * x**2 + b * x + c
    f = kk * (2 * a * x + b) / g
    ans = kk * sp.log(g)
    steps = [Step("sub.choose", f"ให้ $u = {L(g)}$ ซึ่ง $u > 0$ เสมอ (ดิสคริมิแนนต์ติดลบ)", after_tex=f"u={L(g)}"),
             Step("sub.du", f"$du = ({L(2 * a * x + b)})\\,dx$", check=("eq", sp.diff(g, x), 2 * a * x + b)),
             Step("integral.log", f"$\\int \\frac{{{kk}}}{{u}}du = {kk}\\ln|u|$"),
             Step("sub.back", "แทนค่ากลับ (ไม่ต้องใส่ค่าสัมบูรณ์เพราะ $u>0$)", after_tex=L(ans) + " + C", check=("deriv", ans, f))]
    return Built(f"จงหา ${integral_tex(f)}$", integral_tex(f), ans, ("antiderivative", f), steps,
                 ["ตัวเศษเป็นอนุพันธ์ของตัวส่วนหรือไม่?"], "antiderivative", domain=(-2, 2))


@template("calc.5.5.sqrt_sub", "5.5", "การแทนค่ากับรากที่สอง", ["5.5.substitution"], {"c": (1, 9), "k": (1, 6), "pw": ("enum", ["1/2", "3/2", "1/3"])}, "antiderivative")
def sqrt_sub(r, d):
    c = r.int("c", 1, 9)
    kk = r.int("k", 1, 6)
    pw = sp.Rational(r.choice("pw", {1: ["1/2"], 2: ["1/2", "3/2"], 3: ["1/3", "3/2"]}[d]))
    g = x**2 + c
    f = kk * x / g**pw
    F_u = sp.Rational(kk, 2) * u**(1 - pw) / (1 - pw)
    ans = F_u.subs(u, g)
    return Built(f"จงหา ${integral_tex(f)}$", integral_tex(f), ans, ("antiderivative", f), sub_steps(f, g, 2 * x, F_u, ans),
                 [f"ให้ $u = {L(g)}$ แล้ว $x\\,dx = \\frac{{du}}{{2}}$"], "antiderivative")


@template("calc.5.5.trig_inner", "5.5", "ฟังก์ชันตรีโกณที่มีมุมเป็น ax + b", ["5.5.substitution", "5.5.basic"],
          {"kind": ("enum", ["sin", "cos", "sec2", "csc2"]), "a": (2, 6), "b": (0, 3), "c": (1, 6)}, "antiderivative")
def trig_inner(r, d):
    kind = r.choice("kind", ["sin", "cos", "sec2", "csc2"])
    a = r.int("a", 2, 6)
    b = r.int("b", 0, 3) if kind in ("sin", "cos") else 0
    if kind not in ("sin", "cos"):
        r.params["b"] = 0
    c = r.int("c", 1, 6)
    g = a * x + b
    f, F_u = {"sin": (c * sp.sin(g), -sp.Rational(c, a) * sp.cos(u)), "cos": (c * sp.cos(g), sp.Rational(c, a) * sp.sin(u)),
              "sec2": (c * sp.sec(g)**2, sp.Rational(c, a) * sp.tan(u)), "csc2": (c * sp.csc(g)**2, -sp.Rational(c, a) * sp.cot(u))}[kind]
    ans = F_u.subs(u, g)
    return Built(f"จงหา ${integral_tex(f)}$", integral_tex(f), ans, ("antiderivative", f), sub_steps(f, g, sp.Integer(a), F_u, ans),
                 ["ให้ $u = ax+b$"], "antiderivative", domain=(0.05, 0.3))


# ------------------------------------------------------------------ 5.6

@template("calc.5.6.definite_sub_poly", "5.6", "การแทนค่าในอินทิกรัลจำกัดเขต (เปลี่ยนขอบเขต)", ["5.6.change_limits"],
          {"c": (0, 4), "p": (1, 4), "b": (1, 2), "k": (1, 4)})
def definite_sub_poly(r, d):
    c = r.int("c", 0, 4)
    p = r.int("p", 1, 4)
    b = r.int("b", 1, 2)
    kk = r.int("k", 1, 4)
    g = x**2 + c
    f = kk * x * g**p
    ua, ub = g.subs(x, 0), g.subs(x, b)
    val = sp.Rational(kk, 2) * (ub**(p + 1) - ua**(p + 1)) / (p + 1)
    steps = [Step("sub.choose", f"ให้ $u = {L(g)}$, $du = 2x\\,dx$", check=("eq", sp.diff(g, x), 2 * x)),
             Step("sub.limits", f"เปลี่ยนขอบเขต: $x=0 \\Rightarrow u={ua}$, $x={b} \\Rightarrow u={ub}$"),
             Step("sub.transform", "อินทิกรัลใหม่", after_tex=rf"\int_{{{ua}}}^{{{ub}}} \frac{{{kk}}}{{2}}u^{{{p}}}\,du"),
             Step("ftc.part2", "อินทิเกรตและแทนขอบเขตใหม่ (ไม่ต้องแทนกลับเป็น $x$)", after=val,
                  check=("eq", sp.integrate(sp.Rational(kk, 2) * u**p, (u, ua, ub)), val))]
    return Built(f"จงหาค่า ${integral_tex(f, 0, b)}$", integral_tex(f, 0, b), val, ("definite", f, 0, b), steps,
                 ["เปลี่ยนขอบเขตให้เป็นค่าของ $u$"])


@template("calc.5.6.definite_sub_trig", "5.6", "การแทนค่าในอินทิกรัลจำกัดเขตของฟังก์ชันตรีโกณ", ["5.6.change_limits"],
          {"n": (1, 5), "up": ("enum", ["pi/6", "pi/4", "pi/2"]), "k": (1, 6)})
def definite_sub_trig(r, d):
    nn = r.int("n", 1, 5)
    upn = r.choice("up", ["pi/2"] if d == 1 else ["pi/6", "pi/4", "pi/2"])
    up = {"pi/6": sp.pi / 6, "pi/4": sp.pi / 4, "pi/2": sp.pi / 2}[upn]
    kk = r.int("k", 1, 6)
    f = kk * sp.sin(x)**nn * sp.cos(x)
    ub = sp.sin(up)
    val = sp.nsimplify(kk * ub**(nn + 1) / (nn + 1))
    steps = [Step("sub.choose", "ให้ $u = \\sin x$, $du = \\cos x\\,dx$", check=("eq", sp.diff(sp.sin(x), x), sp.cos(x))),
             Step("sub.limits", f"$x = 0 \\Rightarrow u = 0$, $x = {L(up)} \\Rightarrow u = {L(ub)}$"),
             Step("ftc.part2", f"$\\int_0^{{{L(ub)}}} {kk}u^{nn}\\,du$", after=val, check=("eq", sp.integrate(kk * u**nn, (u, 0, ub)), val))]
    return Built(f"จงหาค่า ${integral_tex(f, 0, up)}$", integral_tex(f, 0, up), val, ("definite", f, 0, up), steps, ["ให้ $u=\\sin x$"])


@template("calc.5.6.definite_sub_exp", "5.6", "การแทนค่าในอินทิกรัลจำกัดเขตที่มี e", ["5.6.change_limits"],
          {"b": (1, 3), "k": (1, 4), "s": ("enum", [1, -1])})
def definite_sub_exp(r, d):
    b = r.int("b", 1, 3)
    kk = r.int("k", 1, 4)
    s = r.choice("s", [1, -1])
    f = kk * x * sp.exp(s * x**2)
    ub = s * b**2
    val = sp.Rational(kk, 2 * s) * (sp.exp(ub) - 1)
    steps = [Step("sub.choose", f"ให้ $u = {L(s * x**2)}$, $du = {L(2 * s * x)}\\,dx$"),
             Step("sub.limits", f"$x = 0 \\Rightarrow u = 0$, $x = {b} \\Rightarrow u = {ub}$"),
             Step("ftc.part2", "อินทิเกรต $e^u$", after=val, check=("eq", sp.integrate(sp.Rational(kk, 2 * s) * sp.exp(u), (u, 0, ub)), val))]
    return Built(f"จงหาค่า ${integral_tex(f, 0, b)}$", integral_tex(f, 0, b), val, ("definite", f, 0, b), steps, ["ให้ $u$ เป็นเลขชี้กำลัง"])


def _area_between(f, g, a, b, var=x, axis="x"):
    lbl = "x" if var == x else "y"
    I = sp.integrate(f - g, (var, a, b))
    steps = [Step("area.intersections", f"หาจุดตัด: แก้ ${L(f)} = {L(g)}$ ได้ ${lbl} = {L(a)}, {L(b)}$",
                  check=("true", sp.simplify((f - g).subs(var, a)) == 0 and sp.simplify((f - g).subs(var, b)) == 0)),
             Step("area.upper_lower", f"ในช่วงนี้ ${L(f)} \\ge {L(g)}$ (ทดสอบที่ ${lbl} = {L((a + b) / 2)}$)" + ("" if axis == "x" else " (ขวา − ซ้าย)"),
                  check=("true", (f - g).subs(var, (a + b) / 2) >= 0)),
             Step("area.integral", "ตั้งอินทิกรัล บน − ล่าง", after_tex=rf"\int_{{{L(a)}}}^{{{L(b)}}}\left[({L(f)}) - ({L(g)})\right]d{lbl}"),
             Step("ftc.part2", "คำนวณ", after=I, check=("eq", sp.integrate(sp.expand(f - g), (var, a, b)), I))]
    return I, steps


@template("calc.5.6.area_parabola_line", "5.6", "พื้นที่ระหว่างพาราโบลากับเส้นตรง", ["5.6.area_between", "5.6.intersections"],
          {"r1": (-3, 1), "w": (1, 4), "c": (1, 3)}, viz="area_between")
def area_parabola_line(r, d):
    r1 = r.int("r1", -3, 1)
    w = r.int("w", 1, 4)
    c = r.int("c", 1, 3) if d > 1 else 1
    if d == 1:
        r.params["c"] = 1
    r2 = r1 + w
    par = c * x**2
    line = sp.expand(c * ((r1 + r2) * x - r1 * r2))
    I, steps = _area_between(line, par, r1, r2)
    return Built(f"จงหาพื้นที่ของบริเวณที่ปิดล้อมด้วย $y = {L(par)}$ และ $y = {L(line)}$", rf"y={L(par)},\quad y={L(line)}", I,
                 ("definite", line - par, r1, r2), steps, ["หาจุดตัดก่อน", "เส้นใดอยู่ด้านบน?"],
                 viz={"type": "area_between", "f": poly_str(line), "g": poly_str(par), "a": r1, "b": r2})


@template("calc.5.6.area_two_parabolas", "5.6", "พื้นที่ระหว่างพาราโบลาสองเส้น", ["5.6.area_between"],
          {"s": (1, 3), "h": (-3, 3), "c": (1, 2)}, viz="area_between")
def area_two_parabolas(r, d):
    s = r.int("s", 1, 3)
    h = r.int("h", -3, 3)
    c = r.int("c", 1, 2)
    top = c * (s**2 - x**2) + h
    bot = c * (x**2 - s**2) + h
    I, steps = _area_between(top, bot, -s, s)
    return Built(f"จงหาพื้นที่ของบริเวณที่ปิดล้อมด้วย $y = {L(sp.expand(top))}$ และ $y = {L(sp.expand(bot))}$",
                 rf"y={L(sp.expand(top))},\ y={L(sp.expand(bot))}", I, ("definite", top - bot, -s, s), steps, ["ใช้ความสมมาตรช่วยคำนวณได้"],
                 viz={"type": "area_between", "f": poly_str(sp.expand(top)), "g": poly_str(sp.expand(bot)), "a": -s, "b": s})


@template("calc.5.6.area_wrt_y", "5.6", "พื้นที่โดยอินทิเกรตเทียบกับ y", ["5.6.integrate_y"], {"m": (1, 4), "c": (1, 2)}, viz="area_between")
def area_wrt_y(r, d):
    m = r.int("m", 1, 4)
    c = r.int("c", 1, 2)
    right = m * c * y
    left = c * y**2
    I, steps = _area_between(right, left, 0, m, var=y, axis="y")
    return Built(f"จงหาพื้นที่ของบริเวณที่ปิดล้อมด้วย $x = {L(left)}$ และ $x = {L(right)}$ (อินทิเกรตเทียบกับ $y$)",
                 rf"x={L(left)},\ x={L(right)}", I, ("definite", right - left, 0, m), steps,
                 ["เมื่อขอบเขตเขียนเป็น $x = g(y)$ ให้ใช้ ขวา − ซ้าย"], var=y,
                 viz={"type": "area_between", "f": poly_str(right).replace("y", "x"), "g": poly_str(left).replace("y", "x"), "a": 0, "b": m, "axis": "y"})


@template("calc.5.6.area_sign_change", "5.6", "พื้นที่ระหว่างเส้นโค้งที่สลับบน-ล่าง", ["5.6.sign_change", "5.6.area_between"],
          {"s": (1, 4), "c": (1, 3)}, viz="area_between", errors=["no_partition"])
def area_sign_change(r, d):
    s = r.int("s", 1, 4)
    c = r.int("c", 1, 3)
    f, g = c * x**3, c * s**2 * x
    I1 = sp.integrate(f - g, (x, -s, 0))
    I2 = sp.integrate(g - f, (x, 0, s))
    val = I1 + I2
    steps = [Step("area.intersections", f"${L(f)} = {L(g)} \\Rightarrow x = -{s}, 0, {s}$"),
             Step("area.partition", f"บน $[-{s},0]$: ${L(f)}$ อยู่บน; บน $[0,{s}]$: ${L(g)}$ อยู่บน จึงต้องแยกอินทิกรัล"),
             Step("ftc.part2", "ส่วนที่ 1", after=I1, check=("eq", sp.integrate(f - g, (x, -s, 0)), I1)),
             Step("ftc.part2", "ส่วนที่ 2", after=I2, check=("eq", sp.integrate(g - f, (x, 0, s)), I2)),
             Step("arith", "รวมพื้นที่", after=val, check=("eq", I1 + I2, val))]
    ref = sp.integrate(sp.Abs(f - g).rewrite(sp.Piecewise), (x, -s, s))
    return Built(f"จงหาพื้นที่ของบริเวณที่ปิดล้อมด้วย $y = {L(f)}$ และ $y = {L(g)}$", rf"y={L(f)},\ y={L(g)}", val, ("value", ref), steps,
                 ["มีจุดตัดสามจุด", "ถ้าไม่แยกช่วง ส่วนที่หักล้างจะทำให้ได้ 0"],
                 viz={"type": "area_between", "f": poly_str(f), "g": poly_str(g), "a": -s, "b": s})


@template("calc.5.6.area_sqrt_line", "5.6", "พื้นที่ระหว่าง y = √x กับเส้นตรง", ["5.6.area_between"], {"m": (1, 4)}, viz="area_between")
def area_sqrt_line(r, d):
    m = r.int("m", 1, 4)
    f, g = sp.sqrt(x), x / m
    I, steps = _area_between(f, g, 0, m**2)
    return Built(f"จงหาพื้นที่ของบริเวณที่ปิดล้อมด้วย $y = \\sqrt{{x}}$ และ $y = {L(g)}$", rf"y=\sqrt{{x}},\ y={L(g)}", I, ("definite", f - g, 0, m**2), steps,
                 ["แก้ $\\sqrt{x} = x/m$ หาจุดตัด"], viz={"type": "area_between", "f": "sqrt(x)", "g": poly_str(g), "a": 0, "b": m**2})
