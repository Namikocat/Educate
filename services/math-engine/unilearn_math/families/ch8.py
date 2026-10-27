"""Chapter 8 - Techniques of integration (8.1-8.5, 8.8)."""
from __future__ import annotations

import sympy as sp

from ..core import Built, Reject, Step, L, integral_tex, template
from ..verify import DIVERGES
from ._h import R, poly_str, u, x

pi = sp.pi


def _anti(f, ans, steps, hints, domain=None, viz=None):
    return Built(f"จงหา ${integral_tex(f)}$", integral_tex(f), ans, ("antiderivative", f), steps, hints, "antiderivative", domain=domain, viz=viz)


def _final(ans, f, txt="ตรวจคำตอบโดยการหาอนุพันธ์"):
    return Step("verify.differentiate", txt, after_tex=L(ans) + " + C", check=("deriv", ans, f))


# ------------------------------------------------------------------ 8.1

@template("calc.8.1.split_fraction", "8.1", "แยกเศษส่วนก่อนอินทิเกรต", ["8.1.algebraic_simplification", "8.1.basic_formulas"],
          {"a": (1, 6), "b": (-6, 6), "c": (1, 9)}, "antiderivative")
def split_fraction(r, d):
    a, b, c = r.int("a", 1, 6), r.int("b", -6, 6), r.int("c", 1, 9)
    f = (a * x**2 + b * x + c) / x
    ans = a * x**2 / 2 + b * x + c * sp.log(sp.Abs(x))
    steps = [Step("algebra.split", "หารแต่ละพจน์ด้วย $x$", after=a * x + b + c / x, check=("eq", a * x + b + c / x, f)),
             Step("integral.basic", "อินทิเกรตทีละพจน์ ($\\int \\frac1x dx = \\ln|x|$)"), _final(ans, f)]
    return _anti(f, ans, steps, ["เขียนเป็นผลบวกของพจน์ง่าย ๆ"], domain=(0.3, 3))


@template("calc.8.1.complete_square_arctan", "8.1", "กำลังสองสมบูรณ์แล้วได้ arctan", ["8.1.basic_formulas", "8.1.completing_square"],
          {"p": (-4, 4), "q": (1, 4), "k": (1, 6)}, "antiderivative")
def complete_square(r, d):
    p, q, kk = r.int("p", -4, 4), r.int("q", 1, 4), r.int("k", 1, 6)
    den = sp.expand((x + p)**2 + q**2)
    f = kk / den
    ans = sp.Rational(kk, q) * sp.atan((x + p) / q)
    steps = [Step("algebra.complete_square", f"${L(den)} = (x {'+' if p >= 0 else '-'} {abs(p)})^2 + {q**2}$", check=("eq", (x + p)**2 + q**2, den)),
             Step("sub.choose", f"ให้ $u = x {'+' if p >= 0 else '-'} {abs(p)}$ แล้วใช้ $\\int \\frac{{du}}{{u^2 + a^2}} = \\frac1a\\tan^{{-1}}\\frac ua$"),
             _final(ans, f)]
    return _anti(f, ans, steps, ["ทำกำลังสองสมบูรณ์ที่ตัวส่วน"], domain=(-3, 3))


@template("calc.8.1.arcsin_form", "8.1", "รูปแบบ 1/√(a² − u²) ได้ arcsin", ["8.1.basic_formulas", "8.1.completing_square"],
          {"p": (-3, 3), "q": (1, 5), "k": (1, 4)}, "antiderivative")
def arcsin_form(r, d):
    p, q, kk = r.int("p", -3, 3), r.int("q", 1, 5), r.int("k", 1, 4)
    inside = sp.expand(q**2 - (x - p)**2)
    f = kk / sp.sqrt(inside)
    ans = kk * sp.asin((x - p) / q)
    steps = [Step("algebra.complete_square", f"${L(inside)} = {q**2} - (x - ({p}))^2$", check=("eq", q**2 - (x - p)**2, inside)),
             Step("integral.arcsin", f"$\\int\\frac{{du}}{{\\sqrt{{a^2-u^2}}}} = \\sin^{{-1}}\\frac{{u}}{{a}} + C$ โดย $a = {q}$"), _final(ans, f)]
    return _anti(f, ans, steps, ["จัดรูปภายใต้รากให้เป็น $a^2 - u^2$"], domain=(p - q * 0.6, p + q * 0.6))


@template("calc.8.1.long_division", "8.1", "หารยาวเมื่อดีกรีตัวเศษ ≥ ตัวส่วน", ["8.1.algebraic_simplification"],
          {"a": (-4, 4), "b": (-5, 5), "c": (-6, 6)}, "antiderivative")
def long_division(r, d):
    a, b, c = r.int("a", -4, 4, exclude=(0,)), r.int("b", -5, 5), r.int("c", -6, 6)
    rem = c - a * (b - a)
    if rem == 0:
        raise Reject("exact division")
    f = (x**2 + b * x + c) / (x + a)
    q_ = x + (b - a)
    ans = x**2 / 2 + (b - a) * x + rem * sp.log(sp.Abs(x + a))
    steps = [Step("algebra.long_division", "หารยาว", after=q_ + rem / (x + a), check=("eq", q_ + rem / (x + a), f)),
             Step("integral.basic", "อินทิเกรตทีละพจน์"), _final(ans, f)]
    return _anti(f, ans, steps, ["ดีกรีตัวเศษไม่น้อยกว่าตัวส่วน ให้หารก่อน"], domain=(-a + 0.5, -a + 4))


@template("calc.8.1.trig_square", "8.1", "ขยายกำลังสองแล้วใช้เอกลักษณ์ตรีโกณ", ["8.1.identities", "8.1.trig"], {"a": (1, 4), "form": ("enum", ["sincos", "sectan"])}, "antiderivative")
def trig_square(r, d):
    a = r.int("a", 1, 4)
    form = r.choice("form", ["sincos"] if d < 3 else ["sincos", "sectan"])
    if form == "sincos":
        f = (a * sp.sin(x) + sp.cos(x))**2
        expanded = a**2 * sp.sin(x)**2 + a * sp.sin(2 * x) + sp.cos(x)**2
        ans = R(a**2 + 1, 2) * x - R(a**2 - 1, 4) * sp.sin(2 * x) - R(a, 2) * sp.cos(2 * x)
        idt = "$\\sin^2x = \\frac{1-\\cos 2x}{2}$, $\\cos^2 x = \\frac{1+\\cos 2x}{2}$, $2\\sin x\\cos x = \\sin 2x$"
    else:
        f = (sp.sec(x) + sp.tan(x))**2
        expanded = 2 * sp.sec(x)**2 + 2 * sp.sec(x) * sp.tan(x) - 1
        ans = 2 * sp.tan(x) + 2 * sp.sec(x) - x
        idt = "$\\tan^2 x = \\sec^2 x - 1$"
    steps = [Step("trig.identity", "ขยายแล้วใช้เอกลักษณ์ " + idt, after=expanded, check=("eq", expanded, f)), _final(ans, f)]
    return _anti(f, ans, steps, ["ขยายกำลังสองก่อน"], domain=(0.1, 1.2))


@template("calc.8.1.exp_fraction", "8.1", "อินทิกรัลรูป eˣ/(eˣ + c)", ["8.1.exp_log", "5.5.substitution"], {"k": (1, 6), "c": (1, 9)}, "antiderivative")
def exp_fraction(r, d):
    kk, c = r.int("k", 1, 6), r.int("c", 1, 9)
    f = kk * sp.exp(x) / (sp.exp(x) + c)
    ans = kk * sp.log(sp.exp(x) + c)
    steps = [Step("sub.choose", f"ให้ $u = e^x + {c}$, $du = e^x dx$", check=("eq", sp.diff(sp.exp(x) + c, x), sp.exp(x))),
             Step("integral.log", "$\\int \\frac{du}{u} = \\ln|u|$ และ $u>0$"), _final(ans, f)]
    return _anti(f, ans, steps, ["ตัวเศษคืออนุพันธ์ของตัวส่วน"], domain=(-2, 2))


# ------------------------------------------------------------------ 8.2

def _ibp_steps(uu, dv, du, v, f, rest_int, ans):
    return [
        Step("ibp.identify", "ผลคูณของฟังก์ชันสองชนิด ใช้การอินทิเกรตทีละส่วน (Integration by Parts) ตามหลัก LIATE"),
        Step("ibp.choose", f"เลือก $u = {L(uu)}$ และ $dv = {L(dv)}\\,dx$", after_tex=rf"u={L(uu)},\ dv={L(dv)}\,dx"),
        Step("ibp.compute", f"$du = {L(du)}\\,dx$, $v = {L(v)}$", check=("eq", sp.diff(uu, x), du)),
        Step("ibp.v_check", "ตรวจ $v' = dv$", check=("eq", sp.diff(v, x), dv)),
        Step("ibp.formula", "$\\int u\\,dv = uv - \\int v\\,du$", after_tex=rf"{L(uu * v)} - {integral_tex(sp.simplify(v * du))}",
             check=("eq", sp.diff(uu * v, x) - v * du, f)),
        Step("ibp.remaining", "อินทิเกรตส่วนที่เหลือ", after=rest_int, check=("deriv", rest_int, sp.simplify(v * du))),
        _final(ans, f),
    ]


@template("calc.8.2.poly_exp", "8.2", "Integration by Parts: พหุนาม × เอกซ์โพเนนเชียล", ["8.2.parts", "8.2.choose_u", "8.2.verify"], {"a": (-4, 4), "p": (-5, 5), "c": (1, 4)}, "antiderivative")
def ibp_poly_exp(r, d):
    a, p, c = r.int("a", -4, 4, exclude=(0,)), r.int("p", -5, 5), r.int("c", 1, 4)
    uu, dv = c * x + p, sp.exp(a * x)
    f = uu * dv
    du, v = sp.Integer(c), sp.exp(a * x) / a
    rest = c * sp.exp(a * x) / a**2
    ans = uu * v - rest
    return _anti(f, ans, _ibp_steps(uu, dv, du, v, f, rest, ans), ["เลือก $u$ เป็นพหุนามเพราะหาอนุพันธ์แล้วง่ายขึ้น"])


@template("calc.8.2.poly_trig", "8.2", "Integration by Parts: พหุนาม × ตรีโกณ", ["8.2.parts", "8.2.verify"], {"a": (1, 5), "kind": ("enum", ["sin", "cos"]), "c": (1, 4)}, "antiderivative")
def ibp_poly_trig(r, d):
    a, c = r.int("a", 1, 5), r.int("c", 1, 4)
    kind = r.choice("kind", ["sin", "cos"])
    uu = c * x
    if kind == "sin":
        dv, v = sp.sin(a * x), -sp.cos(a * x) / a
    else:
        dv, v = sp.cos(a * x), sp.sin(a * x) / a
    f = uu * dv
    du = sp.Integer(c)
    rest = sp.integrate(v * du, x)
    ans = uu * v - rest
    return _anti(f, ans, _ibp_steps(uu, dv, du, v, f, rest, ans), ["ให้ $u = x$"])


@template("calc.8.2.poly_log", "8.2", "Integration by Parts: พหุนาม × ลอการิทึม", ["8.2.parts", "8.2.choose_u"], {"n": (0, 4), "c": (1, 3)}, "antiderivative")
def ibp_poly_log(r, d):
    nn, c = r.int("n", 1, 4), r.int("c", 1, 3)
    uu, dv = sp.log(c * x), x**nn
    f = uu * dv
    du, v = 1 / x, x**(nn + 1) / (nn + 1)
    rest = x**(nn + 1) / (nn + 1)**2
    ans = uu * v - rest
    return _anti(f, ans, _ibp_steps(uu, dv, du, v, f, rest, ans), ["ลอการิทึมควรเป็น $u$ เพราะอนุพันธ์ของมันง่าย"], domain=(0.3, 3))


@template("calc.8.2.single_function", "8.2", "Integration by Parts กับฟังก์ชันเดียว (ln, arctan)", ["8.2.parts"], {"a": (1, 5), "kind": ("enum", ["ln", "atan", "asin"])}, "antiderivative")
def ibp_single(r, d):
    a = r.int("a", 1, 5)
    kind = r.choice("kind", ["ln"] if d == 1 else ["atan", "asin", "ln"])
    uu = {"ln": sp.log(a * x), "atan": sp.atan(a * x), "asin": sp.asin(a * x)}[kind]
    dv, v = sp.Integer(1), x
    du = sp.diff(uu, x)
    f = uu
    rest = sp.integrate(sp.simplify(v * du), x)
    ans = uu * x - rest
    dom = (0.3, 3) if kind != "asin" else (0.05 / a, 0.8 / a)
    return _anti(f, ans, _ibp_steps(uu, dv, du, v, f, rest, ans), ["ให้ $dv = dx$"], domain=dom)


@template("calc.8.2.repeated", "8.2", "Integration by Parts ซ้ำสองครั้ง", ["8.2.repeated"], {"a": (-3, 3), "kind": ("enum", ["exp", "sin", "cos"])}, "antiderivative")
def ibp_repeated(r, d):
    a = r.int("a", -3, 3, exclude=(0,))
    kind = r.choice("kind", ["exp", "sin", "cos"])
    g = {"exp": sp.exp(a * x), "sin": sp.sin(a * x), "cos": sp.cos(a * x)}[kind]
    f = x**2 * g
    v1 = sp.integrate(g, x)
    first_rest = sp.simplify(2 * x * v1)
    ans = sp.simplify(x**2 * v1 - sp.integrate(first_rest, x))
    steps = [Step("ibp.choose", f"ครั้งที่ 1: $u = x^2$, $dv = {L(g)}dx$ ได้ $v = {L(v1)}$", check=("eq", sp.diff(v1, x), g)),
             Step("ibp.formula", "ได้อินทิกรัลใหม่ที่ดีกรีของ $x$ ลดลง", after_tex=rf"{L(x**2 * v1)} - {integral_tex(first_rest)}",
                  check=("eq", sp.diff(x**2 * v1, x) - first_rest, f)),
             Step("ibp.repeat", "ครั้งที่ 2: ใช้ Integration by Parts กับ $\\int " + L(first_rest) + "\\,dx$ โดย $u = x$",
                  after=sp.integrate(first_rest, x), check=("deriv", sp.integrate(first_rest, x), first_rest)),
             _final(ans, f)]
    return _anti(f, ans, steps, ["ใช้ซ้ำจนพหุนามหายไป", "วิธีตาราง (tabular) ช่วยได้"])


@template("calc.8.2.cyclic", "8.2", "Integration by Parts แบบวนกลับ (cyclic)", ["8.2.cyclic"], {"a": (1, 3), "b": (1, 4), "kind": ("enum", ["sin", "cos"])}, "antiderivative")
def ibp_cyclic(r, d):
    a, b = r.int("a", 1, 3), r.int("b", 1, 4)
    kind = r.choice("kind", ["sin", "cos"])
    if kind == "sin":
        f = sp.exp(a * x) * sp.sin(b * x); ans = sp.exp(a * x) * (a * sp.sin(b * x) - b * sp.cos(b * x)) / (a**2 + b**2)
    else:
        f = sp.exp(a * x) * sp.cos(b * x); ans = sp.exp(a * x) * (a * sp.cos(b * x) + b * sp.sin(b * x)) / (a**2 + b**2)
    I = sp.Symbol("I")
    steps = [Step("ibp.choose", "ใช้ Integration by Parts สองครั้ง โดยให้ $u$ เป็นฟังก์ชันตรีโกณทั้งสองครั้ง"),
             Step("ibp.cyclic", f"อินทิกรัลเดิม $I$ ปรากฏอีกครั้งทางขวา: $I = (\\dots) - \\frac{{{b**2}}}{{{a**2}}}I$"),
             Step("algebra.solve", f"ย้าย $I$ มารวมกัน: $\\left(1 + \\frac{{{b**2}}}{{{a**2}}}\\right)I = \\dots$ แล้วแก้หา $I$"), _final(ans, f)]
    return _anti(f, ans, steps, ["ถ้าอินทิกรัลเดิมกลับมา ให้แก้สมการหา $I$"])


@template("calc.8.2.definite_parts", "8.2", "Integration by Parts แบบจำกัดเขต", ["8.2.definite"], {"b": (1, 3), "kind": ("enum", ["xexp", "xlog", "xsin"])})
def ibp_definite(r, d):
    b = r.int("b", 1, 3)
    kind = r.choice("kind", ["xexp", "xlog", "xsin"])
    if kind == "xexp":
        f, lo, hi = x * sp.exp(x), 0, b
        F = (x - 1) * sp.exp(x)
    elif kind == "xlog":
        f, lo, hi = x * sp.log(x), 1, sp.E**b
        F = x**2 * sp.log(x) / 2 - x**2 / 4
    else:
        f, lo, hi = x * sp.sin(x), 0, pi * b / 2
        F = sp.sin(x) - x * sp.cos(x)
    val = sp.simplify(F.subs(x, hi) - F.subs(x, lo))
    steps = [Step("ibp.formula", "$\\int_a^b u\\,dv = [uv]_a^b - \\int_a^b v\\,du$"),
             Step("integral.antiderivative", f"ได้ $F(x) = {L(F)}$", after=F, check=("deriv", F, f)),
             Step("ftc.part2", "แทนขอบเขต", after=val, check=("eq", F.subs(x, hi) - F.subs(x, lo), val))]
    return Built(f"จงหาค่า ${integral_tex(f, lo, hi)}$", integral_tex(f, lo, hi), val, ("definite", f, lo, hi), steps, ["ใช้ Integration by Parts แล้วแทนขอบเขต"],
                 domain=(1.1, 2.5), viz={"type": "area", "f": poly_str(f), "a": float(lo), "b": float(hi)})


# ------------------------------------------------------------------ 8.3

@template("calc.8.3.odd_sine", "8.3", "กำลังคี่ของ sin: เก็บ sin ไว้หนึ่งตัว", ["8.3.odd_powers"], {"m": (0, 4), "p": ("enum", [3, 5])}, "antiderivative")
def odd_sine(r, d):
    m = r.int("m", 0, 4)
    p = r.choice("p", [3] if d < 3 else [3, 5])
    f = sp.sin(x)**p * sp.cos(x)**m
    poly_u = sp.expand(-(1 - u**2)**((p - 1) // 2) * u**m)
    F_u = sp.integrate(poly_u, u)
    ans = F_u.subs(u, sp.cos(x))
    steps = [Step("trig.odd_power", f"แยก $\\sin^{p}x = \\sin^{p - 1}x\\,\\sin x = (1-\\cos^2x)^{{{(p - 1) // 2}}}\\sin x$",
                  check=("eq", (1 - sp.cos(x)**2)**((p - 1) // 2) * sp.sin(x) * sp.cos(x)**m, f)),
             Step("sub.choose", "ให้ $u = \\cos x$, $du = -\\sin x\\,dx$", after_tex=integral_tex(poly_u, var=u),
                  check=("eq", poly_u.subs(u, sp.cos(x)) * (-sp.sin(x)), f)),
             Step("integral.power_rule", "อินทิเกรตพหุนามของ $u$", after_tex=L(F_u) + " + C"), _final(ans, f, "แทน $u = \\cos x$ กลับ")]
    return _anti(f, ans, steps, ["กำลังของ $\\sin$ เป็นคี่ ให้ $u = \\cos x$"], domain=(0.1, 1.4))


@template("calc.8.3.odd_cosine", "8.3", "กำลังคี่ของ cos: เก็บ cos ไว้หนึ่งตัว", ["8.3.odd_powers"], {"m": (1, 4), "p": ("enum", [3, 5])}, "antiderivative")
def odd_cosine(r, d):
    m = r.int("m", 1, 4)
    p = r.choice("p", [3] if d < 3 else [3, 5])
    f = sp.cos(x)**p * sp.sin(x)**m
    poly_u = sp.expand((1 - u**2)**((p - 1) // 2) * u**m)
    F_u = sp.integrate(poly_u, u)
    ans = F_u.subs(u, sp.sin(x))
    steps = [Step("trig.odd_power", f"$\\cos^{p}x = (1-\\sin^2x)^{{{(p - 1) // 2}}}\\cos x$"),
             Step("sub.choose", "ให้ $u = \\sin x$, $du = \\cos x\\,dx$", after_tex=integral_tex(poly_u, var=u), check=("eq", poly_u.subs(u, sp.sin(x)) * sp.cos(x), f)),
             _final(ans, f, "อินทิเกรตแล้วแทนกลับ")]
    return _anti(f, ans, steps, ["กำลังของ $\\cos$ เป็นคี่ ให้ $u = \\sin x$"], domain=(0.1, 1.4))


@template("calc.8.3.even_powers", "8.3", "กำลังคู่: ใช้สูตรลดกำลัง (half-angle)", ["8.3.even_powers", "8.3.identities"], {"a": (1, 4), "kind": ("enum", ["sin2", "cos2", "sin2cos2"])}, "antiderivative")
def even_powers(r, d):
    a = r.int("a", 1, 4)
    kind = r.choice("kind", ["sin2", "cos2"] if d < 3 else ["sin2cos2"])
    if kind == "sin2":
        f = sp.sin(a * x)**2; red = (1 - sp.cos(2 * a * x)) / 2
    elif kind == "cos2":
        f = sp.cos(a * x)**2; red = (1 + sp.cos(2 * a * x)) / 2
    else:
        f = sp.sin(a * x)**2 * sp.cos(a * x)**2; red = (1 - sp.cos(4 * a * x)) / 8
    ans = sp.integrate(red, x)
    steps = [Step("trig.half_angle", "ใช้สูตรลดกำลัง $\\sin^2\\theta = \\frac{1-\\cos2\\theta}{2}$, $\\cos^2\\theta = \\frac{1+\\cos2\\theta}{2}$", after=red, check=("eq", red, f)),
             _final(ans, f, "อินทิเกรตทีละพจน์")]
    return _anti(f, ans, steps, ["กำลังคู่ทั้งหมด ใช้ half-angle"])


@template("calc.8.3.tan_sec_even", "8.3", "tanᵐx sec⁴x: ให้ u = tan x", ["8.3.tan_sec"], {"m": (1, 4), "s": ("enum", [2, 4])}, "antiderivative")
def tan_sec_even(r, d):
    m = r.int("m", 1, 4)
    s = r.choice("s", [2] if d == 1 else [4])
    f = sp.tan(x)**m * sp.sec(x)**s
    poly_u = sp.expand(u**m * (1 + u**2)**((s - 2) // 2))
    ans = sp.integrate(poly_u, u).subs(u, sp.tan(x))
    steps = [Step("trig.identity", f"เก็บ $\\sec^2 x$ ไว้หนึ่งตัว ส่วนที่เหลือใช้ $\\sec^2x = 1 + \\tan^2 x$"),
             Step("sub.choose", "ให้ $u = \\tan x$, $du = \\sec^2x\\,dx$", after_tex=integral_tex(poly_u, var=u), check=("eq", poly_u.subs(u, sp.tan(x)) * sp.sec(x)**2, f)),
             _final(ans, f)]
    return _anti(f, ans, steps, ["กำลังของ $\\sec$ เป็นคู่"], domain=(0.05, 1.2))


@template("calc.8.3.tan_odd_sec", "8.3", "tanᵐx secⁿx (m คี่): ให้ u = sec x", ["8.3.tan_sec"], {"n": (1, 4), "m": ("enum", [1, 3, 5])}, "antiderivative")
def tan_odd_sec(r, d):
    nn = r.int("n", 1, 4)
    m = r.choice("m", [1, 3] if d < 3 else [3, 5])
    f = sp.tan(x)**m * sp.sec(x)**nn
    poly_u = sp.expand((u**2 - 1)**((m - 1) // 2) * u**(nn - 1))
    ans = sp.integrate(poly_u, u).subs(u, sp.sec(x))
    steps = [Step("trig.identity", "แยก $\\sec x\\tan x$ ไว้ แล้ว $\\tan^2x = \\sec^2x - 1$"),
             Step("sub.choose", "ให้ $u = \\sec x$, $du = \\sec x\\tan x\\,dx$", after_tex=integral_tex(poly_u, var=u),
                  check=("eq", poly_u.subs(u, sp.sec(x)) * sp.sec(x) * sp.tan(x), f)), _final(ans, f)]
    return _anti(f, ans, steps, ["กำลังของ $\\tan$ เป็นคี่"], domain=(0.05, 1.2))


@template("calc.8.3.product_to_sum", "8.3", "ผลคูณ sin(mx)cos(nx): สูตรผลคูณเป็นผลบวก", ["8.3.products"], {"m": (1, 6), "n": (1, 6), "kind": ("enum", ["sc", "ss", "cc"])}, "antiderivative")
def product_to_sum(r, d):
    m, nn = r.int("m", 1, 6), r.int("n", 1, 6)
    if m == nn:
        raise Reject("m == n")
    kind = r.choice("kind", ["sc", "ss", "cc"])
    if kind == "sc":
        f = sp.sin(m * x) * sp.cos(nn * x); rw = (sp.sin((m - nn) * x) + sp.sin((m + nn) * x)) / 2
    elif kind == "ss":
        f = sp.sin(m * x) * sp.sin(nn * x); rw = (sp.cos((m - nn) * x) - sp.cos((m + nn) * x)) / 2
    else:
        f = sp.cos(m * x) * sp.cos(nn * x); rw = (sp.cos((m - nn) * x) + sp.cos((m + nn) * x)) / 2
    ans = sp.integrate(rw, x)
    steps = [Step("trig.product_to_sum", "ใช้สูตรผลคูณเป็นผลบวก", after=rw, check=("eq", rw, f)), _final(ans, f, "อินทิเกรตแต่ละพจน์")]
    return _anti(f, ans, steps, ["$\\sin A\\cos B = \\frac12[\\sin(A-B)+\\sin(A+B)]$"])


@template("calc.8.3.wallis_definite", "8.3", "อินทิกรัลจำกัดเขตของกำลัง cos/sin บน [0, π/2]", ["8.3.even_powers", "8.3.odd_powers"],
          {"n": (2, 6), "kind": ("enum", ["sin", "cos"])})
def wallis(r, d):
    nn = r.int("n", 2, 6)
    kind = r.choice("kind", ["sin", "cos"])
    f = (sp.sin(x) if kind == "sin" else sp.cos(x))**nn
    # reduction formula I_n = (n-1)/n I_{n-2}
    val = pi / 2 if nn % 2 == 0 else sp.Integer(1)
    start = 2 if nn % 2 == 0 else 3
    for j in range(start, nn + 1, 2):
        val = val * sp.Rational(j - 1, j)
    steps = [Step("trig.reduction", "สูตรลดทอน: $I_n = \\frac{n-1}{n}I_{n-2}$ โดย $I_0 = \\frac\\pi2$, $I_1 = 1$"),
             Step("arith", "คูณต่อเนื่อง", after=val, check=("eq", sp.integrate(f, (x, 0, pi / 2)), val))]
    return Built(f"จงหาค่า ${integral_tex(f, 0, pi / 2)}$", integral_tex(f, 0, pi / 2), val, ("definite", f, 0, pi / 2), steps,
                 ["กำลังคี่ใช้ $u$-substitution กำลังคู่ใช้ half-angle"])


# ------------------------------------------------------------------ 8.4

def _ts(sub_tex, tri_tex, f, ans, extra_assump, hints, domain):
    domain = (float(domain[0]), float(domain[1]))
    steps = [Step("trigsub.pattern", f"รูปแบบ {tri_tex}: แทน {sub_tex}", assumptions=extra_assump),
             Step("trigsub.triangle", "เขียนสามเหลี่ยมอ้างอิง (reference triangle) เพื่อแปลงฟังก์ชันตรีโกณกลับเป็น $x$"),
             Step("trigsub.back", "แทนกลับเป็น $x$", after_tex=L(ans) + " + C", check=("deriv", ans, f))]
    return _anti(f, ans, steps, hints, domain=domain)


@template("calc.8.4.over_x2_sqrt_minus", "8.4", "∫ dx / (x²√(a² − x²))", ["8.4.trig_sub", "8.4.triangle"], {"a2": (1, 20)}, "antiderivative")
def ts1(r, d):
    a = sp.sqrt(r.int("a2", 1, 20))
    f = 1 / (x**2 * sp.sqrt(a**2 - x**2))
    ans = -sp.sqrt(a**2 - x**2) / (a**2 * x)
    return _ts(f"$x = {L(a)}\\sin\\theta$, $dx = {L(a)}\\cos\\theta\\,d\\theta$, $\\sqrt{{{L(a**2)}-x^2}} = {L(a)}\\cos\\theta$", "$\\sqrt{a^2 - x^2}$", f, ans,
               ["-π/2 ≤ θ ≤ π/2 จึง cos θ ≥ 0"], ["$\\int\\csc^2\\theta\\,d\\theta = -\\cot\\theta$"], (0.1 * a, 0.9 * a))


@template("calc.8.4.x2_over_sqrt_minus", "8.4", "∫ x²/√(a² − x²) dx", ["8.4.trig_sub", "8.4.back_sub"], {"a2": (1, 20)}, "antiderivative")
def ts2(r, d):
    a = sp.sqrt(r.int("a2", 1, 20))
    f = x**2 / sp.sqrt(a**2 - x**2)
    ans = a**2 / 2 * sp.asin(x / a) - x * sp.sqrt(a**2 - x**2) / 2
    return _ts(f"$x = {L(a)}\\sin\\theta$", "$\\sqrt{a^2 - x^2}$", f, ans, ["θ = sin⁻¹(x/a) อยู่ใน [-π/2, π/2]"],
               ["ได้ $\\int a^2\\sin^2\\theta\\,d\\theta$ ใช้ half-angle"], (-0.9 * a, 0.9 * a))


@template("calc.8.4.over_plus_32", "8.4", "∫ dx / (a² + x²)^{3/2}", ["8.4.trig_sub"], {"a2": (1, 20)}, "antiderivative")
def ts3(r, d):
    a = sp.sqrt(r.int("a2", 1, 20))
    f = 1 / (a**2 + x**2)**R(3, 2)
    ans = x / (a**2 * sp.sqrt(a**2 + x**2))
    return _ts(f"$x = {L(a)}\\tan\\theta$, $dx = {L(a)}\\sec^2\\theta\\,d\\theta$", "$\\sqrt{a^2 + x^2}$", f, ans, ["-π/2 < θ < π/2"],
               ["ได้ $\\frac{1}{a^2}\\int\\cos\\theta\\,d\\theta$"], (-3, 3))


@template("calc.8.4.over_sqrt_plus", "8.4", "∫ dx / √(x² + a²)", ["8.4.trig_sub"], {"a2": (1, 20)}, "antiderivative")
def ts4(r, d):
    a = sp.sqrt(r.int("a2", 1, 20))
    f = 1 / sp.sqrt(x**2 + a**2)
    ans = sp.log(x + sp.sqrt(x**2 + a**2))
    return _ts(f"$x = {L(a)}\\tan\\theta$", "$\\sqrt{a^2 + x^2}$", f, ans, ["sec θ + tan θ > 0 จึงไม่ต้องใส่ค่าสัมบูรณ์"],
               ["$\\int\\sec\\theta\\,d\\theta = \\ln|\\sec\\theta + \\tan\\theta|$", "ค่าคงที่ $-\\ln a$ รวมเข้ากับ $C$"], (-3, 3))


@template("calc.8.4.sqrt_minus_over_x", "8.4", "∫ √(x² − a²)/x dx (x > a)", ["8.4.trig_sub", "8.4.domain"], {"a2": (1, 20)}, "antiderivative")
def ts5(r, d):
    a = sp.sqrt(r.int("a2", 1, 20))
    f = sp.sqrt(x**2 - a**2) / x
    ans = sp.sqrt(x**2 - a**2) - a * sp.asec(x / a)
    return _ts(f"$x = {L(a)}\\sec\\theta$, $0 \\le \\theta < \\frac\\pi2$", "$\\sqrt{x^2 - a^2}$", f, ans, ["x > a จึงเลือก 0 ≤ θ < π/2 และ tan θ ≥ 0"],
               ["ได้ $a\\int\\tan^2\\theta\\,d\\theta$"], (1.1 * a, 3 * a))


@template("calc.8.4.over_x2_sqrt_plus", "8.4", "∫ dx / (x²√(x² + a²))", ["8.4.trig_sub", "8.4.triangle"], {"a2": (1, 20)}, "antiderivative")
def ts6(r, d):
    a = sp.sqrt(r.int("a2", 1, 20))
    f = 1 / (x**2 * sp.sqrt(x**2 + a**2))
    ans = -sp.sqrt(x**2 + a**2) / (a**2 * x)
    return _ts(f"$x = {L(a)}\\tan\\theta$", "$\\sqrt{a^2+x^2}$", f, ans, ["x > 0 สำหรับการตรวจ"], ["ได้ $\\frac{1}{a^2}\\int\\frac{\\cos\\theta}{\\sin^2\\theta}d\\theta$"], (0.3, 3))


@template("calc.8.4.definite_circle", "8.4", "อินทิกรัลจำกัดเขตด้วยการแทนค่าตรีโกณ (เปลี่ยนขอบเขตเป็น θ)", ["8.4.trig_sub", "5.6.change_limits"],
          {"a2": (1, 20), "kind": ("enum", ["quarter", "asin"])})
def ts_definite(r, d):
    a = sp.sqrt(r.int("a2", 1, 20))
    kind = r.choice("kind", ["quarter", "asin"])
    if kind == "quarter":
        f, hi, val = sp.sqrt(a**2 - x**2), a, pi * a**2 / 4
        th = "\\frac\\pi2"
    else:
        f, hi, val = 1 / sp.sqrt(a**2 - x**2), a / 2, pi / 6
        th = "\\frac\\pi6"
    steps = [Step("trigsub.pattern", f"แทน $x = {L(a)}\\sin\\theta$"), Step("sub.limits", f"$x=0 \\Rightarrow \\theta = 0$, $x = {L(hi)} \\Rightarrow \\theta = {th}$"),
             Step("ftc.part2", "อินทิเกรตในตัวแปร $\\theta$", after=val, check=("eq", sp.integrate(f, (x, 0, hi)), val))]
    return Built(f"จงหาค่า ${integral_tex(f, 0, hi)}$", integral_tex(f, 0, hi), val, ("definite", f, 0, hi), steps, ["เปลี่ยนขอบเขตเป็นค่าของ $\\theta$"])


# ------------------------------------------------------------------ 8.5

def _pf_steps(f, decomp, ans, method_th):
    return [Step("pf.proper", "ตรวจว่าเป็นฟังก์ชันตรรกยะแท้ (ดีกรีเศษ < ส่วน) และแยกตัวประกอบตัวส่วน"),
            Step("pf.decompose", f"แยกเศษส่วนย่อย; หาสัมประสิทธิ์ด้วย{method_th}", after=decomp, check=("eq", decomp, f)),
            Step("pf.integrate", "อินทิเกรตแต่ละเศษส่วนย่อย"), _final(ans, f)]


@template("calc.8.5.two_linear", "8.5", "เศษส่วนย่อย: ตัวประกอบเชิงเส้นต่างกันสองตัว", ["8.5.distinct_linear", "8.5.coefficients"],
          {"r": (-4, 4), "s": (-4, 4), "p": (-5, 5), "q": (-6, 6)}, "antiderivative")
def pf_two(r_, d):
    rr, s = r_.int("r", -4, 4), r_.int("s", -4, 4)
    p, q = r_.int("p", -5, 5), r_.int("q", -6, 6)
    if rr == s or (p * rr + q) == 0 or (p * s + q) == 0:
        raise Reject("degenerate")
    f = (p * x + q) / sp.expand((x - rr) * (x - s))
    A, B = sp.Rational(p * rr + q, rr - s), sp.Rational(p * s + q, s - rr)
    decomp = A / (x - rr) + B / (x - s)
    ans = A * sp.log(sp.Abs(x - rr)) + B * sp.log(sp.Abs(x - s))
    return _anti(f, ans, _pf_steps(f, decomp, ans, f" cover-up: $A = {L(A)}$, $B = {L(B)}$"), ["แยกตัวประกอบตัวส่วน"], domain=(max(rr, s) + 0.5, max(rr, s) + 4))


@template("calc.8.5.three_linear", "8.5", "เศษส่วนย่อย: ตัวประกอบเชิงเส้นสามตัว", ["8.5.distinct_linear"], {"r": (-3, 3), "k": (1, 6)}, "antiderivative")
def pf_three(r_, d):
    rr = r_.int("r", -3, 3)
    kk = r_.int("k", 1, 6)
    roots = [rr - 1, rr, rr + 1]
    den = sp.expand((x - roots[0]) * (x - roots[1]) * (x - roots[2]))
    f = kk / den
    coef = [sp.Rational(kk, sp.prod([rt - o for o in roots if o != rt])) for rt in roots]
    decomp = sum(c / (x - rt) for c, rt in zip(coef, roots))
    ans = sum(c * sp.log(sp.Abs(x - rt)) for c, rt in zip(coef, roots))
    return _anti(f, ans, _pf_steps(f, decomp, ans, "วิธีปิดตัวประกอบ (Heaviside cover-up)"), ["ตัวส่วนแยกเป็น $(x-a)(x-b)(x-c)$"], domain=(rr + 1.5, rr + 5))


@template("calc.8.5.repeated_linear", "8.5", "เศษส่วนย่อย: ตัวประกอบเชิงเส้นซ้ำ", ["8.5.repeated_linear", "8.5.coefficients"],
          {"r": (-3, 3), "s": (-3, 3), "p": (-4, 4), "q": (-5, 5)}, "antiderivative")
def pf_repeated(r_, d):
    rr, s = r_.int("r", -3, 3), r_.int("s", -3, 3)
    p, q = r_.int("p", -4, 4), r_.int("q", -5, 5)
    if rr == s or p * s + q == 0 or p * rr + q == 0:
        raise Reject("degenerate")
    f = (p * x + q) / sp.expand((x - rr)**2 * (x - s))
    Cc = sp.Rational(p * s + q, (s - rr)**2)
    B = sp.Rational(p * rr + q, rr - s)
    A = -Cc
    decomp = A / (x - rr) + B / (x - rr)**2 + Cc / (x - s)
    ans = A * sp.log(sp.Abs(x - rr)) - B / (x - rr) + Cc * sp.log(sp.Abs(x - s))
    return _anti(f, ans, _pf_steps(f, decomp, ans, f" cover-up สำหรับ $B$, $C$ และเทียบสัมประสิทธิ์ $x^2$ ได้ $A = -C$"),
                 ["ตัวประกอบซ้ำ $(x-r)^2$ ต้องมีทั้ง $\\frac{A}{x-r}$ และ $\\frac{B}{(x-r)^2}$"], domain=(max(rr, s) + 0.5, max(rr, s) + 4))


@template("calc.8.5.irreducible_quadratic", "8.5", "เศษส่วนย่อย: ตัวประกอบกำลังสองที่ลดทอนไม่ได้", ["8.5.irreducible_quadratic"],
          {"r": (-3, 3), "c": (1, 3), "k": (1, 10)}, "antiderivative")
def pf_quadratic(r_, d):
    rr, c, kk = r_.int("r", -3, 3), r_.int("c", 1, 3), r_.int("k", 1, 10)
    f = kk / ((x - rr) * (x**2 + c**2))
    A = sp.Rational(kk, rr**2 + c**2)
    decomp = A / (x - rr) + (-A * x - A * rr) / (x**2 + c**2)
    ans = A * sp.log(sp.Abs(x - rr)) - A / 2 * sp.log(x**2 + c**2) - A * rr / c * sp.atan(x / c)
    return _anti(f, ans, _pf_steps(f, decomp, ans, f"การเทียบสัมประสิทธิ์: $\\frac{{A}}{{x-r}} + \\frac{{Bx + D}}{{x^2+{c**2}}}$"),
                 ["$x^2 + c^2$ แยกตัวประกอบจริงไม่ได้ ใช้ตัวเศษ $Bx + D$", "ได้ทั้ง $\\ln$ และ $\\tan^{-1}$"], domain=(rr + 0.5, rr + 4))


@template("calc.8.5.improper_rational", "8.5", "ฟังก์ชันตรรกยะไม่แท้: หารก่อนแล้วแยกเศษส่วนย่อย", ["8.5.division", "8.5.distinct_linear"],
          {"r": (-3, 3), "s": (-3, 3), "b": (-4, 4), "c": (-6, 6)}, "antiderivative")
def pf_improper(r_, d):
    rr, s = r_.int("r", -3, 3), r_.int("s", -3, 3)
    b, c = r_.int("b", -4, 4), r_.int("c", -6, 6)
    if rr >= s:
        raise Reject("order")
    den = sp.expand((x - rr) * (x - s))
    f = (x**2 + b * x + c) / den
    p, q = b + rr + s, c - rr * s
    if p * rr + q == 0 or p * s + q == 0:
        raise Reject("cancels")
    A, B = sp.Rational(p * rr + q, rr - s), sp.Rational(p * s + q, s - rr)
    decomp = 1 + A / (x - rr) + B / (x - s)
    ans = x + A * sp.log(sp.Abs(x - rr)) + B * sp.log(sp.Abs(x - s))
    steps = [Step("algebra.long_division", "ดีกรีเท่ากัน: หารยาวได้ $1 + \\frac{\\text{เศษ}}{\\text{ส่วน}}$", after=1 + (p * x + q) / den, check=("eq", 1 + (p * x + q) / den, f))] + \
        _pf_steps(f, decomp, ans, "cover-up")[1:]
    return _anti(f, ans, steps, ["ต้องหารยาวก่อนเสมอเมื่อเป็นเศษส่วนไม่แท้"], domain=(s + 0.5, s + 4))


@template("calc.8.5.definite", "8.5", "เศษส่วนย่อยในอินทิกรัลจำกัดเขต", ["8.5.distinct_linear", "7.2.properties"], {"p": (1, 3), "q": (2, 5), "b": (1, 4)})
def pf_definite(r, d):
    p = r.int("p", 1, 3)
    q = r.int("q", p + 1, 5)
    b = r.int("b", 1, 4)
    f = 1 / ((x + p) * (x + q))
    F = (sp.log(x + p) - sp.log(x + q)) / (q - p)
    val = sp.simplify(sp.expand_log(F.subs(x, b) - F.subs(x, 0), force=True))
    steps = [Step("pf.decompose", f"$\\frac{{1}}{{(x+{p})(x+{q})}} = \\frac{{1}}{{{q - p}}}\\left(\\frac{{1}}{{x+{p}}} - \\frac{{1}}{{x+{q}}}\\right)$",
                  check=("eq", (1 / (x + p) - 1 / (x + q)) / (q - p), f)),
             Step("ftc.part2", "อินทิเกรตเป็น $\\ln$ แล้วแทนขอบเขต", after=val, check=("eq", F.subs(x, b) - F.subs(x, 0), val))]
    return Built(f"จงหาค่า ${integral_tex(f, 0, b)}$", integral_tex(f, 0, b), val, ("definite", f, 0, b), steps, ["รวม $\\ln$ ด้วยสมบัติลอการิทึม"])


# ------------------------------------------------------------------ 8.8

def _improper(statement_f, f, a, b, ans, steps, hints, viz=None):
    disp = integral_tex(f, a, b)
    return Built(f"จงหาค่า ${disp}$ หรือระบุว่าลู่ออก (diverges)", disp, ans, ("improper", f, a, b), steps, hints, "improper",
                 answer_tex=None if ans != DIVERGES else r"\text{ลู่ออก (diverges)}", viz=viz)


@template("calc.8.8.p_integral_infinity", "8.8", "p-integral บน [1, ∞)", ["8.8.infinite_interval", "8.8.convergence"],
          {"c": (1, 6), "p": ("enum", ["1/2", "1", "3/2", "2", "3"])}, "improper", viz="improper")
def p_inf(r, d):
    c = r.int("c", 1, 6)
    p = sp.Rational(r.choice("p", ["1/2", "1", "3/2", "2", "3"]))
    f = c / x**p
    bb = sp.Symbol("b", positive=True)
    if p > 1:
        ans = sp.Rational(c) / (p - 1)
        lim_txt = f"$\\lim_{{b\\to\\infty}} {L(c * (1 - bb**(1 - p)) / (p - 1))} = {L(ans)}$"
    else:
        ans = DIVERGES
        lim_txt = "ลิมิตเป็น $\\infty$ จึงลู่ออก"
    steps = [Step("improper.limit", "นิยามด้วยลิมิต: $\\int_1^\\infty f = \\lim_{b\\to\\infty}\\int_1^b f$"),
             Step("improper.evaluate", lim_txt, check=("eq", sp.limit(sp.integrate(f, (x, 1, bb)), bb, sp.oo), ans) if ans != DIVERGES else
                  ("true", sp.limit(sp.integrate(f, (x, 1, bb)), bb, sp.oo) == sp.oo)),
             Step("improper.p_test", f"สอดคล้องกับ p-test: ลู่เข้าเมื่อ $p>1$ (ที่นี่ $p={L(p)}$)")]
    return _improper(None, f, 1, sp.oo, ans, steps, ["เขียนเป็นลิมิตของขอบเขตบน"], viz={"type": "improper", "f": poly_str(f), "a": 1, "b": 12})


@template("calc.8.8.exp_decay", "8.8", "อินทิกรัลไม่ตรงแบบของ e^{-ax} และ x e^{-ax}", ["8.8.infinite_interval"], {"a": (1, 5), "c": (1, 6), "form": ("enum", ["exp", "xexp"])},
          "improper", viz="improper")
def exp_decay(r, d):
    a, c = r.int("a", 1, 5), r.int("c", 1, 6)
    form = r.choice("form", ["exp"] if d == 1 else ["xexp"])
    f = c * sp.exp(-a * x) if form == "exp" else c * x * sp.exp(-a * x)
    ans = sp.Rational(c, a) if form == "exp" else sp.Rational(c, a**2)
    bb = sp.Symbol("b", positive=True)
    Fb = sp.integrate(f, (x, 0, bb))
    steps = [Step("improper.limit", "$\\int_0^\\infty = \\lim_{b\\to\\infty}\\int_0^b$", after=Fb),
             Step("improper.evaluate", "$e^{-ab} \\to 0$ (และ $be^{-ab}\\to 0$ โดยกฎของโลปิตาล)", after=ans, check=("eq", sp.limit(Fb, bb, sp.oo), ans))]
    return _improper(None, f, 0, sp.oo, ans, steps, ["อาจต้องใช้ Integration by Parts"], viz={"type": "improper", "f": poly_str(f), "a": 0, "b": 8})


@template("calc.8.8.p_integral_zero", "8.8", "ตัวถูกอินทิเกรตไม่มีขอบเขตที่ x = 0", ["8.8.unbounded_integrand", "8.8.convergence"],
          {"c": (1, 6), "p": ("enum", ["1/3", "1/2", "2/3", "1", "2"])}, "improper", viz="improper")
def p_zero(r, d):
    c = r.int("c", 1, 6)
    p = sp.Rational(r.choice("p", ["1/3", "1/2", "2/3", "1", "2"]))
    f = c / x**p
    eps = sp.Symbol("epsilon", positive=True)
    ans = sp.Rational(c) / (1 - p) if p < 1 else DIVERGES
    lim = sp.limit(sp.integrate(f, (x, eps, 1)), eps, 0, "+")
    steps = [Step("improper.limit", "ตัวถูกอินทิเกรตไม่นิยามที่ $x=0$: $\\int_0^1 f = \\lim_{\\epsilon\\to0^+}\\int_\\epsilon^1 f$"),
             Step("improper.evaluate", "หาลิมิต", check=("eq", lim, ans) if ans != DIVERGES else ("true", lim == sp.oo)),
             Step("improper.p_test", f"ใกล้ 0 ลู่เข้าเมื่อ $p < 1$ (ที่นี่ $p = {L(p)}$)")]
    return _improper(None, f, 0, 1, ans, steps, ["ปัญหาอยู่ที่ขอบเขตล่าง"], viz={"type": "improper", "f": poly_str(f), "a": 0.02, "b": 1})


@template("calc.8.8.arctan_both", "8.8", "อินทิกรัลบน (−∞, ∞): แยกที่จุดใดจุดหนึ่ง", ["8.8.infinite_interval", "8.8.split"], {"a": (1, 5), "c": (1, 4), "half": ("enum", [0, 1])},
          "improper", viz="improper")
def arctan_both(r, d):
    a, c = r.int("a", 1, 5), r.int("c", 1, 4)
    half = r.choice("half", [1] if d == 1 else [0, 1])
    f = c / (x**2 + a**2)
    lo = 0 if half else -sp.oo
    ans = c * pi / (2 * a) if half else c * pi / a
    steps = [Step("improper.split", "ถ้าขอบเขตเป็น $-\\infty$ ถึง $\\infty$ ต้องแยกเป็นสองอินทิกรัลและแต่ละส่วนต้องลู่เข้า (ไม่ใช่ใช้ $\\lim_{b\\to\\infty}\\int_{-b}^b$ ซึ่งคือ principal value)"),
             Step("integral.arctan", f"$\\int\\frac{{{c}}}{{x^2+{a**2}}}dx = \\frac{{{c}}}{{{a}}}\\tan^{{-1}}\\frac{{x}}{{{a}}}$", check=("deriv", c * sp.atan(x / a) / a, f)),
             Step("improper.evaluate", "$\\tan^{-1}(\\pm\\infty) = \\pm\\frac\\pi2$", after=ans)]
    return _improper(None, f, lo, sp.oo, ans, steps, ["$\\lim_{x\\to\\infty}\\tan^{-1}x = \\frac\\pi2$"], viz={"type": "improper", "f": poly_str(f), "a": -10, "b": 10})


@template("calc.8.8.interior_singularity", "8.8", "จุดเอกฐานภายในช่วง: ต้องแยกอินทิกรัล", ["8.8.split", "8.8.incorrect_cancellation"],
          {"a": ("enum", [1, 8]), "b": ("enum", [1, 8, 27]), "form": ("enum", ["two_thirds", "square"])}, "improper", viz="improper",
          errors=["ignored_singularity"])
def interior(r, d):
    a = r.choice("a", [1, 8])
    b = r.choice("b", [1, 8, 27])
    form = r.choice("form", ["two_thirds", "square"])
    if form == "square":
        f = 1 / x**2
        ans = DIVERGES
        steps = [Step("improper.singularity", "$\\frac{1}{x^2}$ ไม่มีขอบเขตที่ $x=0$ ซึ่งอยู่ในช่วง จึงต้องแยก $\\int_{-a}^0 + \\int_0^b$"),
                 Step("improper.evaluate", "$\\int_0^b \\frac{dx}{x^2} = \\lim_{\\epsilon\\to0^+}\\left(\\frac1\\epsilon - \\frac1b\\right) = \\infty$ จึงลู่ออก",
                      check=("true", sp.integrate(f, (x, 0, b)) == sp.oo)),
                 Step("improper.warning", f"ถ้าแทนค่าตรงๆ จะได้ $-\\frac{{1}}{{{b}}} - \\frac{{1}}{{{a}}}$ ซึ่งผิด (ติดลบทั้งที่ตัวถูกอินทิเกรตเป็นบวก)")]
        verify = ("improper", f, -a, b)
        disp_f = f
    else:
        disp_f = 1 / sp.root(x**2, 3)  # |x|^(-2/3), real-valued on both sides
        right = sp.integrate(x**R(-2, 3), (x, 0, b))
        left = sp.integrate(x**R(-2, 3), (x, 0, a))  # by symmetry of |x|^(-2/3)
        ans = right + left
        steps = [Step("improper.singularity", "ไม่มีขอบเขตที่ $x = 0$ แยกเป็นสองอินทิกรัลไม่ตรงแบบ"),
                 Step("improper.evaluate", f"$\\int_0^{{{b}}} x^{{-2/3}}dx = 3\\sqrt[3]{{{b}}}$ และ $\\int_{{-{a}}}^0 |x|^{{-2/3}}dx = 3\\sqrt[3]{{{a}}}$",
                      check=("eq", right, 3 * sp.root(b, 3))),
                 Step("arith", "ทั้งสองส่วนลู่เข้า จึงรวมกันได้", after=ans)]
        verify = ("value", 3 * sp.root(a, 3) + 3 * sp.root(b, 3))
    disp = integral_tex(disp_f, -a, b)
    return Built(f"จงหาค่า ${disp}$ หรือระบุว่าลู่ออก (diverges)", disp, ans, verify, steps, ["มีจุดที่ตัวถูกอินทิเกรตไม่นิยามอยู่ภายในช่วงหรือไม่?"], "improper",
                 answer_tex=None if ans != DIVERGES else r"\text{ลู่ออก (diverges)}", canonical=f"{form}|{a}|{b}",
                 viz={"type": "improper", "f": "1/x^2" if form == "square" else "1/abs(x)^(2/3)", "a": -a, "b": b, "singularity": 0})


@template("calc.8.8.comparison", "8.8", "ตรวจการลู่เข้าด้วยการเปรียบเทียบแบบลิมิต", ["8.8.comparison", "8.8.convergence"],
          {"p": ("enum", ["1/2", "1", "3/2", "2", "3"]), "c": (1, 9), "form": ("enum", ["plus", "sqrt"])}, "choice")
def comparison(r, d):
    p = sp.Rational(r.choice("p", ["1/2", "1", "3/2", "2", "3"]))
    c = r.int("c", 1, 9)
    form = r.choice("form", ["plus", "sqrt"])
    f = 1 / (x**p + c) if form == "plus" else 1 / sp.sqrt(x**(2 * p) + c)
    ans = "converges" if p > 1 else "diverges"

    def independent():
        ratio = sp.limit(f / x**(-p), x, sp.oo)
        assert ratio.is_positive and ratio.is_finite
        return "converges" if sp.integrate(x**(-p), (x, 1, sp.oo)).is_finite else "diverges"

    steps = [Step("comparison.choose", f"สำหรับ $x$ ใหญ่ $f(x) \\approx \\frac{{1}}{{x^{{{L(p)}}}}}$"),
             Step("comparison.limit", "$\\lim_{x\\to\\infty}\\frac{f(x)}{1/x^p} = 1$ เป็นจำนวนบวกจำกัด จึงลู่เข้า/ออกพร้อมกัน (Limit Comparison Test)",
                  check=("true", sp.limit(f / x**(-p), x, sp.oo) == 1)),
             Step("improper.p_test", f"$\\int_1^\\infty \\frac{{dx}}{{x^{{{L(p)}}}}}$ {'ลู่เข้า' if p > 1 else 'ลู่ออก'}", check=("true", independent() == ans))]
    disp = integral_tex(f, 1, sp.oo)
    return Built(f"อินทิกรัล ${disp}$ ลู่เข้าหรือลู่ออก?", disp, ans, ("choice", independent), steps, ["เปรียบเทียบกับ p-integral"], "choice",
                 choices=[{"id": "converges", "label": "ลู่เข้า (converges)"}, {"id": "diverges", "label": "ลู่ออก (diverges)"}])


@template("calc.8.8.log_improper", "8.8", "อินทิกรัลไม่ตรงแบบที่มี ln x", ["8.8.unbounded_integrand", "8.2.parts"], {"form": ("enum", ["ln01", "lnx2", "lnx"]), "c": (1, 5)}, "improper")
def log_improper(r, d):
    form = r.choice("form", ["ln01", "lnx2", "lnx"])
    c = r.int("c", 1, 5)
    if form == "ln01":
        f, a, b, ans = c * sp.log(x), 0, 1, -sp.Integer(c)
        txt = "ไม่มีขอบเขตที่ $0$; ใช้ $\\lim_{\\epsilon\\to0^+}\\epsilon\\ln\\epsilon = 0$"
    elif form == "lnx2":
        f, a, b, ans = c * sp.log(x) / x**2, 1, sp.oo, sp.Integer(c)
        txt = "Integration by Parts แล้ว $\\frac{\\ln b}{b}\\to 0$"
    else:
        f, a, b, ans = c * sp.log(x) / x, 1, sp.oo, DIVERGES
        txt = "$\\int\\frac{\\ln x}{x}dx = \\frac{(\\ln x)^2}{2}\\to\\infty$ จึงลู่ออก"
    ref = sp.integrate(f, (x, a, b))
    steps = [Step("improper.limit", "เขียนเป็นลิมิต"), Step("improper.evaluate", txt, check=("true", (ref == sp.oo) if ans == DIVERGES else (sp.simplify(ref - ans) == 0)))]
    return _improper(None, f, a, b, ans, steps, ["ใช้ Integration by Parts กับ $\\ln x$"])
