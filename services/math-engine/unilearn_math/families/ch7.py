"""Chapter 7 - Transcendental functions (7.1, 7.2, 7.3, 7.5)."""
from __future__ import annotations

import sympy as sp

from ..core import Built, Reject, Step, L, integral_tex, template
from ._h import R, poly_str, sub_steps, u, x

yv = sp.Symbol("y")


def _deriv_built(statement, f, ans, steps, hints, domain=None, viz=None):
    return Built(statement, rf"\frac{{d}}{{dx}}\left[{L(f)}\right]", ans, ("derivative", f), steps, hints, domain=domain, viz=viz)


# ------------------------------------------------------------------ 7.1

def _inverse_steps(f, finv):
    return [
        Step("inverse.swap", f"เขียน $y = {L(f)}$ แล้วแก้สมการหา $x$ ในรูปของ $y$"),
        Step("inverse.solve", "สลับบทบาท $x$ กับ $y$", after=finv),
        Step("inverse.verify", "ตรวจสอบ: $f(f^{-1}(x)) = x$", check=("eq", sp.simplify(f.subs(x, finv)), x)),
    ]


@template("calc.7.1.inverse_linear", "7.1", "หาฟังก์ชันผกผันของฟังก์ชันเชิงเส้น", ["7.1.inverse", "7.1.one_to_one"],
          {"a": (-6, 6), "b": (-9, 9)}, difficulties=(1,), viz="inverse")
def inverse_linear(r, d):
    a = r.int("a", -6, 6, exclude=(0, 1))
    b = r.int("b", -9, 9)
    f = a * x + b
    finv = (x - b) / a
    ref = sp.solve(sp.Eq(yv, f), x)[0].subs(yv, x)
    return Built(f"จงหา $f^{{-1}}(x)$ เมื่อ $f(x) = {L(f)}$", rf"f(x)={L(f)}", finv, ("value", ref), _inverse_steps(f, finv),
                 ["ให้ $y = f(x)$ แล้วแก้หา $x$"], viz={"type": "inverse", "f": poly_str(f), "g": poly_str(finv), "a": -5, "b": 5})


@template("calc.7.1.inverse_rational", "7.1", "หาฟังก์ชันผกผันของฟังก์ชันตรรกยะเชิงเส้น", ["7.1.inverse", "7.1.domain_range"],
          {"a": (-4, 4), "b": (-5, 5), "c": (1, 3), "dd": (-5, 5)})
def inverse_rational(r, d):
    a, b = r.int("a", -4, 4), r.int("b", -5, 5)
    c, dd = r.int("c", 1, 3), r.int("dd", -5, 5)
    if a * dd - b * c == 0:
        raise Reject("not one-to-one")
    f = (a * x + b) / (c * x + dd)
    finv = (b - dd * x) / (c * x - a)
    ref = sp.solve(sp.Eq(yv, f), x)[0].subs(yv, x)
    steps = _inverse_steps(f, finv)
    steps.insert(2, Step("inverse.domain", f"โดเมนของ $f^{{-1}}$ คือเรนจ์ของ $f$: $x \\ne {L(R(a, c))}$ (โดเมนและเรนจ์สลับกัน)"))
    return Built(f"จงหา $f^{{-1}}(x)$ เมื่อ $f(x) = {L(f)}$", rf"f(x)={L(f)}", finv, ("value", ref), steps,
                 ["คูณไขว้แล้วรวมพจน์ที่มี $x$ ไว้ข้างเดียว"], domain=(float(R(a, c)) + 0.7, float(R(a, c)) + 3))


@template("calc.7.1.inverse_power", "7.1", "ฟังก์ชันผกผันของฟังก์ชันกำลัง (จำกัดโดเมน)", ["7.1.inverse", "7.1.one_to_one"],
          {"h": (-3, 3), "kk": (-4, 4), "form": ("enum", ["cube", "square"])}, viz="inverse")
def inverse_power(r, d):
    h, kk = r.int("h", -3, 3), r.int("kk", -4, 4)
    form = r.choice("form", ["cube", "square"])
    if form == "cube":
        f = (x - h)**3 + kk; finv = h + (x - kk)**R(1, 3); dom_txt = ""
    else:
        f = (x - h)**2 + kk; finv = h + sp.sqrt(x - kk); dom_txt = f" เมื่อ $x \\ge {h}$"
    ref = h + sp.root(x - kk, 3) if form == "cube" else h + sp.sqrt(x - kk)
    steps = _inverse_steps(f, finv)
    if form == "square":
        steps.insert(0, Step("inverse.restrict", f"บน $x\\ge {h}$ ฟังก์ชันเพิ่มขึ้นตลอด จึงเป็นฟังก์ชันหนึ่งต่อหนึ่ง เลือกรากที่เป็นบวก"))
    return Built(f"จงหา $f^{{-1}}(x)$ เมื่อ $f(x) = {L(f)}${dom_txt}", rf"f(x)={L(f)}", finv, ("value", ref), steps,
                 ["ย้ายค่าคงที่แล้วถอดราก"], domain=(kk + 0.5, kk + 6),
                 viz={"type": "inverse", "f": poly_str(f), "g": poly_str(finv), "a": h, "b": h + 3})


@template("calc.7.1.inverse_derivative_poly", "7.1", "อนุพันธ์ของฟังก์ชันผกผัน ณ จุด (พหุนาม)", ["7.1.inverse_derivative"],
          {"p": (1, 5), "q": (-5, 5), "a": (-2, 2)})
def inverse_derivative_poly(r, d):
    p, q = r.int("p", 1, 5), r.int("q", -5, 5)
    a = r.int("a", -2, 2)
    f = x**3 + p * x + q
    b = f.subs(x, a)
    fp = sp.diff(f, x)
    ans = 1 / fp.subs(x, a)
    steps = [Step("inverse.monotone", f"$f'(x) = {L(fp)} > 0$ ทุก $x$ ดังนั้น $f$ เป็นหนึ่งต่อหนึ่ง", check=("true", p > 0)),
             Step("inverse.point", f"$f({a}) = {b}$ ดังนั้น $f^{{-1}}({b}) = {a}$", check=("eq", f.subs(x, a), b)),
             Step("inverse.derivative", f"$(f^{{-1}})'(b) = \\frac{{1}}{{f'(f^{{-1}}(b))}} = \\frac{{1}}{{f'({a})}}$", after=ans, check=("eq", 1 / fp.subs(x, a), ans))]
    # independent check: implicit differentiation of f(y) = x at the point
    yy = sp.Function("Y")(x)
    imp = sp.solve(sp.diff(f.subs(x, yy) - x, x), sp.diff(yy, x))[0].subs(yy, a)
    return Built(f"ให้ $f(x) = {L(f)}$ จงหา $(f^{{-1}})'({b})$", rf"(f^{{-1}})'({b}),\ f(x)={L(f)}", ans, ("value", imp), steps,
                 [f"หาค่า $a$ ที่ทำให้ $f(a) = {b}$ ก่อน"])


@template("calc.7.1.inverse_derivative_trans", "7.1", "อนุพันธ์ของฟังก์ชันผกผัน (ฟังก์ชันอดิศัย)", ["7.1.inverse_derivative"],
          {"a": (2, 6), "b": (1, 3), "form": ("enum", ["sin", "exp"])})
def inverse_derivative_trans(r, d):
    a = r.int("a", 2, 6)
    b = r.int("b", 1, 3)
    form = r.choice("form", ["sin", "exp"])
    if form == "sin":
        if b >= a:
            raise Reject("not monotone")
        f = a * x + b * sp.sin(x)
    else:
        f = a * x + b * sp.exp(x)
    y0 = f.subs(x, 0)
    ans = 1 / sp.diff(f, x).subs(x, 0)
    steps = [Step("inverse.monotone", f"$f'(x) = {L(sp.diff(f, x))} > 0$ จึงมีฟังก์ชันผกผัน"),
             Step("inverse.point", f"$f(0) = {L(y0)}$", check=("eq", f.subs(x, 0), y0)),
             Step("inverse.derivative", "$(f^{-1})'(f(0)) = 1/f'(0)$", after=ans, check=("eq", 1 / sp.diff(f, x).subs(x, 0), ans))]
    return Built(f"ให้ $f(x) = {L(f)}$ จงหา $(f^{{-1}})'({L(y0)})$", rf"(f^{{-1}})'({L(y0)})", ans, ("value", 1 / sp.diff(f, x).subs(x, 0)), steps,
                 ["ไม่จำเป็นต้องหาสูตรของ $f^{-1}$"])


@template("calc.7.1.one_to_one_interval", "7.1", "ตรวจสอบความเป็นฟังก์ชันหนึ่งต่อหนึ่งบนช่วง", ["7.1.one_to_one"],
          {"h": (-3, 3), "p": (-4, 3), "w": (1, 4)}, "choice")
def one_to_one(r, d):
    h = r.int("h", -3, 3)
    p = r.int("p", -4, 3)
    w = r.int("w", 1, 4)
    q = p + w
    f = sp.expand((x - h)**2 + 1)
    ans = "yes" if not (p < h < q) else "no"

    def independent():
        crit = [c for c in sp.solve(sp.diff(f, x), x) if p < c < q]
        return "no" if crit else "yes"

    steps = [Step("diff.basic", f"$f'(x) = {L(sp.diff(f, x))}$ เป็นศูนย์ที่ $x = {h}$"),
             Step("inverse.monotone", (f"$x={h}$ อยู่ภายใน $({p},{q})$ ฟังก์ชันเปลี่ยนจากลดเป็นเพิ่ม จึงไม่เป็นหนึ่งต่อหนึ่ง" if ans == "no"
                                       else f"$x={h}$ ไม่อยู่ภายใน $({p},{q})$ ฟังก์ชันเป็นทางเดียว (monotonic) จึงเป็นหนึ่งต่อหนึ่ง"),
                  check=("true", independent() == ans))]
    return Built(f"$f(x) = {L(f)}$ บนช่วง $[{p},{q}]$ เป็นฟังก์ชันหนึ่งต่อหนึ่งหรือไม่?", rf"f(x)={L(f)},\ [{p},{q}]", ans,
                 ("choice", independent), steps, ["ฟังก์ชันที่เพิ่มขึ้นหรือลดลงตลอดช่วงเป็นหนึ่งต่อหนึ่ง"], "choice",
                 choices=[{"id": "yes", "label": "เป็น (one-to-one)"}, {"id": "no", "label": "ไม่เป็น"}],
                 viz={"type": "function_plot", "expressions": [poly_str(f)], "domain": [p - 1, q + 1]})


# ------------------------------------------------------------------ 7.2

INNER = [("quad", lambda a, b: a * x**2 + b), ("lin", lambda a, b: a * x + b), ("sin", lambda a, b: sp.sin(x) + b + 1), ("exp", lambda a, b: sp.exp(a * x) + b)]


@template("calc.7.2.ln_chain", "7.2", "อนุพันธ์ของ ln(g(x))", ["7.2.differentiation"], {"g": ("enum", [i[0] for i in INNER]), "a": (1, 5), "b": (1, 6), "c": (1, 4)})
def ln_chain(r, d):
    g = dict(INNER)[r.choice("g", [i[0] for i in INNER])](r.int("a", 1, 5), r.int("b", 1, 6))
    c = r.int("c", 1, 4)
    f = c * sp.log(g)
    ans = c * sp.diff(g, x) / g
    steps = [Step("diff.ln_chain", "$\\frac{d}{dx}\\ln u = \\frac{u'}{u}$ (กฎลูกโซ่)", assumptions=["u > 0"]),
             Step("diff.basic", f"$u = {L(g)}$, $u' = {L(sp.diff(g, x))}$", after=ans, check=("eq", sp.diff(f, x), ans))]
    return _deriv_built(f"จงหา $\\dfrac{{d}}{{dx}}\\left[{L(f)}\\right]$", f, ans, steps, ["ใช้ $\\frac{d}{dx}\\ln u = \\frac{u'}{u}$"], domain=(0.2, 2))


@template("calc.7.2.log_differentiation", "7.2", "การหาอนุพันธ์โดยใช้ลอการิทึม (logarithmic differentiation)", ["7.2.log_diff"],
          {"p": (1, 4), "q": (1, 3), "rr": (1, 3), "c": (1, 4)})
def log_diff(r, d):
    p, q, rr, c = r.int("p", 1, 4), r.int("q", 1, 3), r.int("rr", 1, 3), r.int("c", 1, 4)
    yexpr = x**p * (x**2 + 1)**q / (x + c)**rr
    lnrhs = p * sp.log(x) + q * sp.log(x**2 + 1) - rr * sp.log(x + c)
    dl = p / x + 2 * q * x / (x**2 + 1) - rr / (x + c)
    ans = yexpr * dl
    steps = [Step("log.take", "ใส่ $\\ln$ ทั้งสองข้าง แล้วใช้สมบัติลอการิทึมแยกผลคูณ/ผลหาร", after_tex=r"\ln y = " + L(lnrhs),
                  check=("eq", sp.expand_log(sp.log(yexpr), force=True), lnrhs)),
             Step("diff.implicit", "หาอนุพันธ์ทั้งสองข้าง: $\\frac{y'}{y} = $ ...", after=dl, check=("eq", sp.diff(lnrhs, x), dl)),
             Step("algebra.multiply", "คูณด้วย $y$", after=ans, check=("eq", sp.diff(yexpr, x), ans))]
    return _deriv_built(f"ใช้การหาอนุพันธ์โดยลอการิทึม หา $y'$ เมื่อ $y = {L(yexpr)}$ ($x>0$)", yexpr, ans, steps,
                        ["$\\ln$ เปลี่ยนผลคูณเป็นผลบวก"], domain=(0.3, 3))


@template("calc.7.2.ln_integral", "7.2", "อินทิกรัลที่ให้ผลเป็น ln|ax+b|", ["7.2.integration"], {"k": (1, 9), "a": (1, 5), "b": (-6, 6)}, "antiderivative")
def ln_integral(r, d):
    kk, a, b = r.int("k", 1, 9), r.int("a", 1, 5), r.int("b", -6, 6)
    g = a * x + b
    f = kk / g
    ans = sp.Rational(kk, a) * sp.log(sp.Abs(g))
    steps = [Step("sub.choose", f"ให้ $u = {L(g)}$, $du = {a}\\,dx$"),
             Step("integral.log", "$\\int \\frac{du}{u} = \\ln|u| + C$ (ต้องมีค่าสัมบูรณ์เพราะ $u$ อาจติดลบ)"),
             Step("sub.back", "แทนกลับ", after_tex=L(ans) + " + C", check=("deriv", ans, f))]
    z = -b / a
    return Built(f"จงหา ${integral_tex(f)}$", integral_tex(f), ans, ("antiderivative", f), steps, ["$\\int \\frac{1}{u}du = \\ln|u|$"],
                 "antiderivative", domain=(z + 0.5, z + 4))


@template("calc.7.2.ln_definite", "7.2", "อินทิกรัลจำกัดเขตของ 1/x", ["7.2.definition", "7.2.integration"], {"c": (1, 6), "kk": (1, 4), "form": ("enum", ["e", "shift"])})
def ln_definite(r, d):
    c, kk = r.int("c", 1, 6), r.int("kk", 1, 4)
    form = r.choice("form", ["e", "shift"])
    if form == "e":
        f, a, b = c / x, 1, sp.E**kk
        val = c * kk
        F = c * sp.log(x)
    else:
        f, a, b = c / (x + kk), 0, kk
        val = c * sp.log(2)
        F = c * sp.log(x + kk)
    steps = [Step("ln.definition", "$\\ln x = \\int_1^x \\frac{1}{t}dt$ และ $\\frac{d}{dx}\\ln|x| = \\frac1x$"),
             Step("ftc.part2", "แทนขอบเขต", before_tex=rf"\left[{L(F)}\right]_{{{L(a)}}}^{{{L(b)}}}", after=val, check=("eq", F.subs(x, b) - F.subs(x, a), val))]
    return Built(f"จงหาค่า ${integral_tex(f, a, b)}$", integral_tex(f, a, b), val, ("definite", f, a, b), steps, ["$\\ln e^k = k$"])


@template("calc.7.2.log_properties", "7.2", "รวมลอการิทึมเป็นพจน์เดียว", ["7.2.properties"], {"a": (2, 7), "b": (2, 7), "m": (1, 3), "n": (1, 3)}, difficulties=(1, 2))
def log_props(r, d):
    a, b = r.int("a", 2, 7), r.int("b", 2, 7)
    if a == b:
        raise Reject("same base")
    m, nn = r.int("m", 1, 3), r.int("n", 1, 3)
    expr_tex = rf"{m}\ln {a} - {nn}\ln {b}" if d == 1 else rf"{m}\ln {a} + \ln {b**2} - {nn}\ln {b}"
    val = sp.Rational(a**m, b**nn) if d == 1 else sp.Rational(a**m * b**2, b**nn)
    ans = sp.log(val)
    lhs = m * sp.log(a) - nn * sp.log(b) if d == 1 else m * sp.log(a) + sp.log(b**2) - nn * sp.log(b)
    steps = [Step("log.power", "กฎยกกำลัง: $r\\ln a = \\ln a^r$"), Step("log.product_quotient", "รวม $\\ln A + \\ln B = \\ln AB$, $\\ln A - \\ln B = \\ln\\frac AB$",
                                                                        after=ans, check=("eq", lhs, ans))]
    return Built(f"จงเขียน ${expr_tex}$ ให้อยู่ในรูป $\\ln$ เพียงพจน์เดียว", expr_tex, ans, ("value", lhs), steps, ["ใช้กฎของลอการิทึม"])


@template("calc.7.2.tan_integral", "7.2", "อินทิกรัลของ tan และ cot", ["7.2.integration"], {"kind": ("enum", ["tan", "cot"]), "a": (1, 4), "k": (1, 5)}, "antiderivative")
def tan_integral(r, d):
    kind = r.choice("kind", ["tan", "cot"])
    a, kk = r.int("a", 1, 4), r.int("k", 1, 5)
    if kind == "tan":
        f = kk * sp.tan(a * x); ans = -sp.Rational(kk, a) * sp.log(sp.Abs(sp.cos(a * x))); g = sp.cos(a * x)
    else:
        f = kk * sp.cot(a * x); ans = sp.Rational(kk, a) * sp.log(sp.Abs(sp.sin(a * x))); g = sp.sin(a * x)
    steps = [Step("trig.rewrite", f"เขียน ${L(f)}$ เป็นเศษส่วนของ $\\sin$ และ $\\cos$"),
             Step("sub.choose", f"ให้ $u = {L(g)}$ ตัวเศษเป็น (ค่าคงที่ ×) $du$"),
             Step("sub.back", "ได้ลอการิทึมของค่าสัมบูรณ์", after_tex=L(ans) + " + C", check=("deriv", ans, f))]
    return Built(f"จงหา ${integral_tex(f)}$", integral_tex(f), ans, ("antiderivative", f), steps, ["$\\tan x = \\frac{\\sin x}{\\cos x}$"], "antiderivative",
                 domain=(0.05, 0.35))


# ------------------------------------------------------------------ 7.3

@template("calc.7.3.exp_derivative", "7.3", "อนุพันธ์ของ e^{g(x)}", ["7.3.differentiation"], {"c": (1, 5), "a": (-3, 3), "b": (-3, 3), "form": ("enum", ["poly", "sin", "sqrt"])})
def exp_derivative(r, d):
    c, a, b = r.int("c", 1, 5), r.int("a", -3, 3, exclude=(0,)), r.int("b", -3, 3)
    form = r.choice("form", ["poly"] if d == 1 else ["poly", "sin", "sqrt"])
    g = {"poly": a * x**2 + b * x, "sin": sp.sin(a * x), "sqrt": a * sp.sqrt(x)}[form]
    f = c * sp.exp(g)
    ans = f * sp.diff(g, x)
    steps = [Step("diff.exp_chain", "$\\frac{d}{dx}e^{u} = e^{u}\\,u'$"), Step("diff.basic", f"$u' = {L(sp.diff(g, x))}$", after=ans, check=("eq", sp.diff(f, x), ans))]
    return _deriv_built(f"จงหา $\\dfrac{{d}}{{dx}}\\left[{L(f)}\\right]$", f, ans, steps, ["อนุพันธ์ของ $e^u$ คือตัวเองคูณ $u'$"], domain=(0.2, 2))


@template("calc.7.3.exp_integral", "7.3", "อินทิกรัลของ e^{ax+b}", ["7.3.integration"], {"k": (1, 8), "a": (-5, 5), "b": (-4, 4)}, "antiderivative")
def exp_integral(r, d):
    kk, a, b = r.int("k", 1, 8), r.int("a", -5, 5, exclude=(0, 1)), r.int("b", -4, 4)
    g = a * x + b
    f = kk * sp.exp(g)
    F_u = sp.Rational(kk, a) * sp.exp(u)
    ans = F_u.subs(u, g)
    return Built(f"จงหา ${integral_tex(f)}$", integral_tex(f), ans, ("antiderivative", f), sub_steps(f, g, sp.Integer(a), F_u, ans), ["ให้ $u = ax + b$"], "antiderivative")


@template("calc.7.3.general_base_derivative", "7.3", "อนุพันธ์ของ aᵘ", ["7.3.base_a"], {"a": (2, 10), "c": (1, 4), "form": ("enum", ["x", "x2", "sin"])})
def base_deriv(r, d):
    a, c = r.int("a", 2, 10), r.int("c", 1, 4)
    form = r.choice("form", ["x"] if d == 1 else ["x2", "sin"])
    g = {"x": x, "x2": x**2 + 1, "sin": sp.sin(x)}[form]
    f = c * a**g
    ans = f * sp.log(a) * sp.diff(g, x)
    steps = [Step("exp.base_change", f"${a}^{{u}} = e^{{u\\ln {a}}}$", check=("eq", a**g, sp.exp(g * sp.log(a)))),
             Step("diff.exp_chain", f"$\\frac{{d}}{{dx}}{a}^u = {a}^u\\ln {a}\\cdot u'$", after=ans, check=("eq", sp.diff(f, x), ans))]
    return _deriv_built(f"จงหา $\\dfrac{{d}}{{dx}}\\left[{L(f)}\\right]$", f, ans, steps, ["อย่าลืมตัวคูณ $\\ln a$"])


@template("calc.7.3.general_base_integral", "7.3", "อินทิกรัลของ aˣ", ["7.3.base_a", "7.3.integration"], {"a": (2, 10), "c": (1, 5), "form": ("enum", ["x", "xx2"])}, "antiderivative")
def base_int(r, d):
    a, c = r.int("a", 2, 10), r.int("c", 1, 5)
    form = r.choice("form", ["x"] if d == 1 else ["x", "xx2"])
    if form == "x":
        f = c * a**x; ans = c * a**x / sp.log(a)
    else:
        f = c * x * a**(x**2); ans = c * a**(x**2) / (2 * sp.log(a))
    steps = [Step("exp.base_change", f"${a}^x = e^{{x\\ln {a}}}$"), Step("integral.exp", "อินทิเกรตแล้วหารด้วย $\\ln a$ (และ 2 จากการแทนค่าหากมี)",
                                                                        after_tex=L(ans) + " + C", check=("deriv", ans, f))]
    return Built(f"จงหา ${integral_tex(f)}$", integral_tex(f), ans, ("antiderivative", f), steps, ["$\\int a^x dx = \\frac{a^x}{\\ln a} + C$"], "antiderivative")


@template("calc.7.3.solve_exponential", "7.3", "แก้สมการเอกซ์โพเนนเชียล", ["7.3.identities", "7.2.properties"], {"a": (-4, 4), "b": (-5, 5), "c": (2, 20)})
def solve_exp(r, d):
    a, b, c = r.int("a", -4, 4, exclude=(0,)), r.int("b", -5, 5), r.int("c", 2, 20)
    ans = (sp.log(c) - b) / a
    steps = [Step("log.take", f"ใส่ $\\ln$ ทั้งสองข้าง: ${L(a * x + b)} = \\ln {c}$ (เพราะ $\\ln e^u = u$)"),
             Step("algebra.solve", "แก้สมการเชิงเส้น", after=ans, check=("eq", sp.exp(a * ans + b), c))]
    ref = [s for s in sp.solve(sp.Eq(sp.exp(a * x + b), c), x) if s.is_real][0]
    return Built(f"จงแก้สมการ $e^{{{L(a * x + b)}}} = {c}$", rf"e^{{{L(a * x + b)}}} = {c}", ans, ("value", ref), steps, ["$\\ln$ เป็นฟังก์ชันผกผันของ $e^x$"])


@template("calc.7.3.variable_power", "7.3", "อนุพันธ์ของ x^{g(x)}", ["7.3.differentiation", "7.2.log_diff"], {"a": (1, 4), "form": ("enum", ["ax", "sin", "ln"])})
def variable_power(r, d):
    a = r.int("a", 1, 4)
    form = r.choice("form", ["ax", "sin", "ln"])
    g = {"ax": a * x, "sin": a * sp.sin(x), "ln": a * sp.log(x)}[form]
    f = x**g
    ans = f * (sp.diff(g, x) * sp.log(x) + g / x)
    steps = [Step("exp.base_change", f"$x^{{{L(g)}}} = e^{{({L(g)})\\ln x}}$", assumptions=["x > 0"], check=("eq", f, sp.exp(g * sp.log(x)))),
             Step("diff.product", "หาอนุพันธ์เลขชี้กำลัง $g\\ln x$ ด้วยกฎผลคูณ", after=sp.diff(g * sp.log(x), x)),
             Step("diff.exp_chain", "คูณด้วย $x^{g(x)}$", after=ans, check=("eq", sp.diff(f, x), ans))]
    return _deriv_built(f"จงหา $\\dfrac{{d}}{{dx}}\\left[{L(f)}\\right]$ สำหรับ $x>0$", f, ans, steps, ["ไม่ใช้กฎกำลังเพราะเลขชี้กำลังเป็นตัวแปร"], domain=(0.3, 3))


@template("calc.7.3.log_base_derivative", "7.3", "อนุพันธ์ของ logₐ g(x)", ["7.3.base_a"], {"a": (2, 10), "p": (1, 4), "q": (1, 6)})
def log_base_derivative(r, d):
    a, p, q = r.int("a", 2, 10), r.int("p", 1, 4), r.int("q", 1, 6)
    g = p * x**2 + q
    f = sp.log(g, a)
    ans = sp.diff(g, x) / (g * sp.log(a))
    steps = [Step("log.base_change", f"$\\log_{{{a}}} u = \\frac{{\\ln u}}{{\\ln {a}}}$"), Step("diff.ln_chain", "หาอนุพันธ์", after=ans, check=("eq", sp.diff(f, x), ans))]
    return Built(f"จงหา $\\dfrac{{d}}{{dx}}\\log_{{{a}}}\\left({L(g)}\\right)$", rf"\frac{{d}}{{dx}}\log_{{{a}}}({L(g)})", ans, ("derivative", f), steps,
                 ["เปลี่ยนฐานเป็น $\\ln$ ก่อน"])


# ------------------------------------------------------------------ 7.5

def _lh_check(num, den, pt, dirn="+"):
    n0, d0 = sp.limit(num, x, pt, dirn), sp.limit(den, x, pt, dirn)
    zero = n0 == 0 and d0 == 0
    inf = n0.is_infinite and d0.is_infinite
    return zero, inf, n0, d0


def _lh_built(statement, num, den, pt, ans, steps, hints, dirn="+"):
    e = num / den
    disp = rf"\lim_{{x\to {L(pt)}{'^+' if dirn == '+' and pt == 0 else ''}}} {L(e)}"
    return Built(statement or f"จงหา ${disp}$", disp, ans, ("limit", e, pt, dirn), steps, hints)


def _lh_steps(num, den, pt, times=1):
    zero, inf, n0, d0 = _lh_check(num, den, pt)
    form = "0/0" if zero else "∞/∞"
    steps = [Step("lhopital.check", f"แทนค่าได้รูปแบบไม่กำหนด {form}: ตัวเศษ $\\to {L(n0)}$, ตัวส่วน $\\to {L(d0)}$ จึงใช้กฎของโลปิตาลได้",
                  assumptions=["f, g หาอนุพันธ์ได้ใกล้จุดนั้น", "g'(x) ≠ 0 ใกล้จุดนั้น"], check=("true", zero or inf))]
    for i in range(times):
        num, den = sp.diff(num, x), sp.diff(den, x)
        steps.append(Step("lhopital.apply", f"หาอนุพันธ์ตัวเศษและตัวส่วนแยกกัน (ครั้งที่ {i + 1})", after=num / den))
        if i < times - 1:
            z2, i2, _, _ = _lh_check(num, den, pt)
            steps.append(Step("lhopital.check", "ยังเป็นรูปแบบไม่กำหนด ใช้ซ้ำได้", check=("true", z2 or i2)))
    val = sp.limit(num / den, x, pt)
    steps.append(Step("limit.evaluate", "หาลิมิต (ไม่เป็นรูปแบบไม่กำหนดแล้ว)", after=val))
    return steps, val


@template("calc.7.5.lh_polynomial", "7.5", "รูปแบบ 0/0 ของพหุนาม", ["7.5.zero_over_zero", "7.5.conditions"], {"r": (-3, 3), "p": (-4, 4), "q": (-4, 4)})
def lh_poly(r_, d):
    rr, p, q = r_.int("r", -3, 3), r_.int("p", -4, 4), r_.int("q", -4, 4)
    if p == rr or q == rr or p == q:
        raise Reject("degenerate")
    num, den = sp.expand((x - rr) * (x - p)), sp.expand((x - rr) * (x - q))
    if d == 3:
        num, den = sp.expand(num * (x - rr)), sp.expand(den * (x - rr))
    steps, val = _lh_steps(num, den, rr, 2 if d == 3 else 1)
    steps.append(Step("limit.alternative", "ทางเลือก: แยกตัวประกอบแล้วตัด $(x-r)$ ได้ผลเดียวกัน", check=("eq", sp.cancel(num / den).subs(x, rr), val)))
    return _lh_built(None, num, den, rr, val, steps, ["แทนค่าก่อนเสมอเพื่อตรวจรูปแบบ"])


@template("calc.7.5.lh_trig", "7.5", "รูปแบบ 0/0 ที่มีฟังก์ชันตรีโกณ", ["7.5.zero_over_zero", "7.5.repeated"], {"a": (1, 6), "b": (1, 6), "form": ("enum", ["sin", "cos", "tan"])})
def lh_trig(r, d):
    a, b = r.int("a", 1, 6), r.int("b", 1, 6)
    form = r.choice("form", {1: ["sin"], 2: ["sin", "tan"], 3: ["cos"]}[d])
    if form == "sin":
        num, den, times = sp.sin(a * x), b * x, 1
    elif form == "tan":
        num, den, times = sp.tan(a * x), sp.sin(b * x), 1
    else:
        num, den, times = 1 - sp.cos(a * x), b * x**2, 2
    steps, val = _lh_steps(num, den, 0, times)
    return _lh_built(None, num, den, 0, val, steps, ["$\\frac{d}{dx}\\sin(ax) = a\\cos(ax)$"])


@template("calc.7.5.lh_exp", "7.5", "รูปแบบ 0/0 ที่มี eˣ", ["7.5.zero_over_zero", "7.5.repeated"], {"a": (-4, 4), "b": (1, 5)})
def lh_exp(r, d):
    a, b = r.int("a", -4, 4, exclude=(0,)), r.int("b", 1, 5)
    if d < 3:
        num, den, times = sp.exp(a * x) - 1, b * x, 1
    else:
        num, den, times = sp.exp(a * x) - 1 - a * x, b * x**2, 2
    steps, val = _lh_steps(num, den, 0, times)
    return _lh_built(None, num, den, 0, val, steps, ["$e^0 = 1$"])


@template("calc.7.5.lh_infinity", "7.5", "รูปแบบ ∞/∞ เมื่อ x → ∞", ["7.5.inf_over_inf", "7.5.repeated"], {"n": (1, 3), "a": (1, 3), "form": ("enum", ["poly_exp", "log_power", "rational"])})
def lh_inf(r, d):
    nn, a = r.int("n", 1, 3), r.int("a", 1, 3)
    form = r.choice("form", ["rational", "log_power", "poly_exp"])
    if form == "poly_exp":
        num, den, times = x**nn, sp.exp(a * x), nn
    elif form == "log_power":
        num, den, times = sp.log(x), x**nn, 1
    else:
        num, den, times = a * x**2 + nn * x, nn * x**2 + 1, 2
    steps, val = _lh_steps(num, den, sp.oo, times)
    return _lh_built(None, num, den, sp.oo, val, steps, ["$e^{ax}$ โตเร็วกว่าพหุนามทุกตัว"])


@template("calc.7.5.lh_zero_times_inf", "7.5", "รูปแบบ 0·∞ (แปลงเป็นเศษส่วน)", ["7.5.other_forms"], {"p": (1, 3)})
def lh_0inf(r, d):
    p = r.int("p", 1, 3)
    e = x**p * sp.log(x)
    num, den = sp.log(x), x**(-p)
    steps = [Step("lhopital.transform", f"$0\\cdot(-\\infty)$: เขียนใหม่เป็น $\\frac{{\\ln x}}{{x^{{-{p}}}}}$ ได้รูป $\\frac{{-\\infty}}{{\\infty}}$", check=("eq", num / den, e))]
    s2, val = _lh_steps(num, den, 0, 1)
    disp = rf"\lim_{{x\to 0^+}} {L(e)}"
    return Built(f"จงหา ${disp}$", disp, val, ("limit", e, 0, "+"), steps + s2, ["ย้ายตัวประกอบหนึ่งไปเป็นตัวส่วน"])


@template("calc.7.5.lh_one_to_inf", "7.5", "รูปแบบ 1^∞", ["7.5.other_forms"], {"a": (-4, 4), "b": (1, 4)})
def lh_1inf(r, d):
    a, b = r.int("a", -4, 4, exclude=(0,)), r.int("b", 1, 4)
    e = (1 + sp.Rational(a) / x)**(b * x)
    lnL = sp.limit(b * x * sp.log(1 + a / x), x, sp.oo)
    val = sp.exp(lnL)
    steps = [Step("lhopital.transform", f"ให้ $y = {L(e)}$ แล้ว $\\ln y = {b}x\\ln\\left(1 + \\frac{{{a}}}{{x}}\\right) = \\frac{{\\ln(1 + {a}/x)}}{{1/({b}x)}}$ เป็นรูป 0/0"),
             Step("lhopital.apply", "ใช้กฎของโลปิตาลกับ $\\ln y$", after=lnL, check=("eq", sp.limit(sp.diff(sp.log(1 + a / x), x) / sp.diff(1 / (b * x), x), x, sp.oo), lnL)),
             Step("limit.exp", "$\\lim y = e^{\\lim \\ln y}$ (ความต่อเนื่องของ $e^x$)", after=val)]
    disp = rf"\lim_{{x\to\infty}} {L(e)}"
    return Built(f"จงหา ${disp}$", disp, val, ("limit", e, sp.oo, "+"), steps, ["ใส่ $\\ln$ ก่อน"])


@template("calc.7.5.lh_not_applicable", "7.5", "ตรวจเงื่อนไข: เมื่อกฎของโลปิตาลใช้ไม่ได้", ["7.5.conditions", "7.5.not_applicable"],
          {"r": (-3, 3), "p": (1, 6), "q": (1, 6)}, errors=["applied_lhopital_without_indeterminate"])
def lh_not_applicable(r_, d):
    rr, p, q = r_.int("r", -3, 3), r_.int("p", 1, 6), r_.int("q", 1, 6)
    num, den = x**2 + p, x + q
    if den.subs(x, rr) == 0:
        raise Reject("den zero")
    val = sp.Rational(rr**2 + p, rr + q)
    wrong = sp.Rational(2 * rr, 1)
    steps = [Step("lhopital.check", f"แทนค่า $x = {rr}$: ตัวเศษ $= {rr**2 + p}$, ตัวส่วน $= {rr + q} \\ne 0$ ไม่ใช่รูปแบบไม่กำหนด", check=("true", den.subs(x, rr) != 0)),
             Step("limit.direct", "ใช้การแทนค่าโดยตรง (ฟังก์ชันต่อเนื่องที่จุดนี้)", after=val, check=("eq", num.subs(x, rr) / den.subs(x, rr), val)),
             Step("lhopital.warning", f"ถ้าใช้กฎของโลปิตาลผิดเงื่อนไขจะได้ $\\frac{{2x}}{{1}} \\to {wrong}$ ซึ่งผิด")]
    return _lh_built(None, num, den, rr, val, steps, ["ตรวจรูปแบบก่อนใช้กฎของโลปิตาลทุกครั้ง"])


@template("calc.7.5.conjugate_alternative", "7.5", "รูปแบบ ∞ − ∞ (วิธีทางเลือก: คอนจูเกต)", ["7.5.other_forms", "7.5.alternatives"], {"a": (1, 8), "b": (-5, 5)})
def conjugate(r, d):
    a, b = r.int("a", 1, 8), r.int("b", -5, 5)
    e = sp.sqrt(x**2 + a * x + b) - x
    val = sp.Rational(a, 2)
    steps = [Step("limit.indeterminate", "รูปแบบ $\\infty - \\infty$"),
             Step("algebra.conjugate", "คูณด้วยคอนจูเกต $\\frac{\\sqrt{\\cdot}+x}{\\sqrt{\\cdot}+x}$", after=(a * x + b) / (sp.sqrt(x**2 + a * x + b) + x),
                  check=("eq", (a * x + b) / (sp.sqrt(x**2 + a * x + b) + x), e)),
             Step("limit.divide", "หารเศษและส่วนด้วย $x$ แล้วให้ $x\\to\\infty$", after=val)]
    disp = rf"\lim_{{x\to\infty}}\left({L(e)}\right)"
    return Built(f"จงหา ${disp}$", disp, val, ("limit", e, sp.oo, "+"), steps, ["การใช้โลปิตาลไม่ใช่ทางเดียว"], domain=(5, 50))
