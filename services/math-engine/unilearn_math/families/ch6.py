"""Chapter 6 - Applications of definite integrals (6.1-6.4)."""
from __future__ import annotations

import sympy as sp

from ..core import Built, Reject, Step, L, integral_tex, template
from ._h import R, poly_str, x, y

pi = sp.pi


def _vol_steps(setup_th: str, integrand, a, b, var, val, formula_tex: str):
    return [
        Step("volume.setup", setup_th, after_tex=formula_tex),
        Step("volume.integrand", "เขียนตัวถูกอินทิเกรตให้อยู่ในรูปขยาย", after=sp.expand(integrand), check=("eq", sp.expand(integrand), integrand)),
        Step("ftc.part2", "อินทิเกรตและแทนขอบเขต", before_tex=integral_tex(sp.expand(integrand), a, b, var), after=val,
             check=("eq", sp.integrate(integrand, (var, a, b)), val)),
    ]


# ------------------------------------------------------------------ 6.1

@template("calc.6.1.disk_power", "6.1", "วิธีจาน (Disk Method) รอบแกน x", ["6.1.disk"],
          {"c": (1, 3), "p": ("enum", ["1/2", "1", "2"]), "b": (1, 3)}, viz="revolution")
def disk_power(r, d):
    c = r.int("c", 1, 3)
    p = sp.Rational(r.choice("p", ["1/2", "1"] if d == 1 else ["1/2", "1", "2"]))
    b = r.int("b", 1, 3)
    f = c * x**p
    integrand = pi * f**2
    val = sp.integrate(integrand, (x, 0, b))
    steps = _vol_steps(f"หน้าตัดตั้งฉากกับแกน $x$ เป็นวงกลมรัศมี $R(x) = {L(f)}$ ดังนั้น $A(x) = \\pi R(x)^2$",
                       integrand, 0, b, x, val, rf"V = \int_0^{{{b}}} \pi\left({L(f)}\right)^2 dx")
    return Built(f"จงหาปริมาตรของทรงตันที่เกิดจากการหมุนบริเวณใต้กราฟ $y = {L(f)}$ บน $[0,{b}]$ รอบแกน $x$", rf"y={L(f)},\ 0\le x\le {b}",
                 val, ("definite", integrand, 0, b), steps, ["รัศมีของจาน = ความสูงของกราฟ", "$V=\\int_a^b \\pi R(x)^2dx$"],
                 viz={"type": "revolution", "f": poly_str(f), "a": 0, "b": b, "axis": "x", "method": "disk"})


@template("calc.6.1.disk_sphere_segment", "6.1", "ปริมาตรทรงกลมและส่วนของทรงกลม", ["6.1.disk"],
          {"r": (1, 5), "a": (-5, 0), "b": (0, 5)}, viz="revolution")
def disk_sphere(r_, d):
    rr = r_.int("r", 1, 5)
    if d == 1:
        a, b = -rr, rr
        r_.params.update(a=-rr, b=rr)
    else:
        a = r_.int("a", -rr, 0)
        b = r_.int("b", max(a + 1, 0), rr)
    f = sp.sqrt(rr**2 - x**2)
    integrand = pi * (rr**2 - x**2)
    val = sp.integrate(integrand, (x, a, b))
    steps = [Step("volume.setup", f"หมุนครึ่งวงกลม $y=\\sqrt{{{rr**2}-x^2}}$ รอบแกน $x$ รัศมีจาน $R(x)^2 = {rr**2} - x^2$",
                  check=("eq", f**2, rr**2 - x**2))] + _vol_steps("ตั้งอินทิกรัล", integrand, a, b, x, val, rf"V=\int_{{{a}}}^{{{b}}}\pi({rr**2}-x^2)dx")[1:]
    return Built(f"จงหาปริมาตรของทรงตันที่ได้จากการหมุนกราฟ $y = \\sqrt{{{rr**2} - x^2}}$, ${a} \\le x \\le {b}$ รอบแกน $x$",
                 rf"y=\sqrt{{{rr**2}-x^2}},\ {a}\le x\le {b}", val, ("definite", integrand, a, b), steps,
                 ["$R(x)^2$ ไม่มีรากที่สองแล้ว"], viz={"type": "revolution", "f": poly_str(f), "a": a, "b": b, "axis": "x", "method": "disk"})


@template("calc.6.1.washer_line_parabola", "6.1", "วิธีแหวน (Washer Method) ระหว่างเส้นตรงกับพาราโบลา", ["6.1.washer"],
          {"m": (1, 3), "c": (1, 3)}, viz="revolution", errors=["subtracted_radii_before_squaring"])
def washer_lp(r, d):
    m = r.int("m", 1, 3)
    c = r.int("c", 1, 3) if d > 1 else 1
    if d == 1:
        r.params["c"] = 1
    R_, r_ = c * m * x, c * x**2
    integrand = pi * (R_**2 - r_**2)
    val = sp.integrate(integrand, (x, 0, m))
    steps = [Step("area.intersections", f"${L(r_)} = {L(R_)}$ ที่ $x = 0, {m}$"),
             Step("washer.radii", f"รัศมีนอก $R(x) = {L(R_)}$, รัศมีใน $r(x) = {L(r_)}$ (เส้นตรงอยู่ห่างแกนมากกว่า)",
                  check=("true", (R_ - r_).subs(x, R(m, 2)) > 0))] + \
        _vol_steps("$A(x) = \\pi(R^2 - r^2)$ ไม่ใช่ $\\pi(R - r)^2$", integrand, 0, m, x, val, rf"V=\int_0^{{{m}}}\pi\left[({L(R_)})^2-(x^2)^2\right]dx")
    return Built(f"จงหาปริมาตรของทรงตันที่ได้จากการหมุนบริเวณระหว่าง $y = {L(R_)}$ และ $y = x^2$ รอบแกน $x$", rf"y={L(R_)},\ y=x^2", val,
                 ("definite", integrand, 0, m), steps, ["หาจุดตัด", "ยกกำลังสองแต่ละรัศมีก่อนลบกัน"],
                 viz={"type": "revolution", "f": poly_str(R_), "g": poly_str(r_), "a": 0, "b": m, "axis": "x", "method": "washer"})


@template("calc.6.1.washer_about_line", "6.1", "วิธีแหวนรอบเส้นตรงที่ไม่ใช่แกน", ["6.1.washer", "6.1.axis_choice"],
          {"b": (1, 2), "c": (1, 3)}, viz="revolution")
def washer_about_line(r, d):
    b = r.int("b", 1, 2)
    c = r.int("c", 1, 3)
    f = x**2
    R_, r_ = f + c, sp.Integer(c)
    integrand = pi * (R_**2 - r_**2)
    val = sp.integrate(integrand, (x, 0, b))
    steps = [Step("washer.radii", f"แกนหมุน $y = -{c}$: รัศมีนอก $R = x^2 - (-{c}) = {L(R_)}$, รัศมีใน $r = 0 - (-{c}) = {c}$")] + \
        _vol_steps("$V = \\int \\pi(R^2 - r^2)dx$", integrand, 0, b, x, val, rf"V=\int_0^{{{b}}}\pi\left[({L(R_)})^2 - {c}^2\right]dx")
    return Built(f"บริเวณใต้กราฟ $y = x^2$ เหนือแกน $x$ บน $[0,{b}]$ ถูกหมุนรอบเส้น $y = -{c}$ จงหาปริมาตร", rf"y=x^2,\ [0,{b}],\ \text{{แกน }} y=-{c}",
                 val, ("definite", integrand, 0, b), steps, ["รัศมีวัดจากแกนหมุน ไม่ใช่จากแกน $x$"],
                 viz={"type": "revolution", "f": "x^2", "g": "0", "a": 0, "b": b, "axis": "x", "axisValue": -c, "method": "washer"})


SHAPES = {"square": (1, "สี่เหลี่ยมจัตุรัส", "s^2"), "semicircle": (pi / 8, "ครึ่งวงกลม (เส้นผ่านศูนย์กลางอยู่บนฐาน)", r"\frac{\pi}{8}s^2"),
          "equilateral": (sp.sqrt(3) / 4, "สามเหลี่ยมด้านเท่า", r"\frac{\sqrt3}{4}s^2")}


@template("calc.6.1.cross_section_triangle", "6.1", "ทรงตันที่มีหน้าตัดกำหนดบนฐานสามเหลี่ยม", ["6.1.cross_section"],
          {"s": (1, 6), "Lb": (1, 6), "shape": ("enum", list(SHAPES))}, viz="cross_section")
def cross_triangle(r, d):
    s0 = r.int("s", 1, 6)
    Lb = r.int("Lb", 1, 6)
    shape = r.choice("shape", ["square"] if d == 1 else list(SHAPES))
    coef, th, form = SHAPES[shape]
    side = s0 * (1 - x / Lb)
    integrand = coef * side**2
    val = sp.integrate(integrand, (x, 0, Lb))
    steps = [Step("cross.side", f"ด้านของหน้าตัดที่ตำแหน่ง $x$: $s(x) = {L(side)}$"),
             Step("cross.area", f"พื้นที่หน้าตัด $A(x) = {form}$", after=sp.expand(integrand), check=("eq", coef * side**2, sp.expand(integrand))),
             Step("ftc.part2", "$V = \\int_0^L A(x)dx$", after=val, check=("eq", sp.integrate(sp.expand(integrand), (x, 0, Lb)), val))]
    return Built(f"ฐานของทรงตันคือบริเวณใต้เส้น $y = {L(side)}$ เหนือแกน $x$ จาก $x=0$ ถึง $x={Lb}$ หน้าตัดที่ตั้งฉากกับแกน $x$ เป็นรูป{th} ที่มีด้าน (หรือเส้นผ่านศูนย์กลาง) อยู่บนฐาน จงหาปริมาตร",
                 rf"s(x)={L(side)},\ 0\le x\le {Lb}", val, ("definite", integrand, 0, Lb), steps, ["หาความยาวด้านของหน้าตัดเป็นฟังก์ชันของ $x$"],
                 viz={"type": "cross_section", "f": poly_str(side), "a": 0, "b": Lb, "shape": shape})


@template("calc.6.1.cross_section_parabola", "6.1", "หน้าตัดตั้งฉากกับแกน y บนฐานพาราโบลา", ["6.1.cross_section", "6.1.axis_choice"],
          {"h": (1, 9), "shape": ("enum", list(SHAPES))}, viz="cross_section")
def cross_parabola(r, d):
    h = r.int("h", 1, 9)
    shape = r.choice("shape", list(SHAPES))
    coef, th, form = SHAPES[shape]
    side = 2 * sp.sqrt(y)
    integrand = sp.simplify(coef * side**2)
    val = sp.integrate(integrand, (y, 0, h))
    steps = [Step("cross.side", f"ที่ระดับ $y$ ความกว้างของฐานคือ $2\\sqrt{{y}}$ (จาก $x=-\\sqrt y$ ถึง $\\sqrt y$)"),
             Step("cross.area", f"$A(y) = {form}$ เมื่อ $s = 2\\sqrt y$", after=integrand, check=("eq", coef * 4 * y, integrand)),
             Step("ftc.part2", f"$V = \\int_0^{{{h}}} A(y)\\,dy$", after=val, check=("eq", sp.integrate(coef * 4 * y, (y, 0, h)), val))]
    return Built(f"ฐานของทรงตันคือบริเวณระหว่าง $y = x^2$ และ $y = {h}$ หน้าตัดที่ตั้งฉากกับแกน $y$ เป็นรูป{th} จงหาปริมาตร",
                 rf"y=x^2,\ y={h}", val, ("definite", integrand, 0, h), steps, ["ใช้ $y$ เป็นตัวแปรอินทิเกรต"], var=y)


@template("calc.6.1.disk_about_y", "6.1", "วิธีจานรอบแกน y", ["6.1.disk", "6.1.axis_choice"], {"c": (1, 3), "m": ("enum", ["1/2", "1", "2"]), "b": (1, 3)},
          viz="revolution")
def disk_about_y(r, d):
    c = r.int("c", 1, 3)
    m = sp.Rational(r.choice("m", ["1/2", "1", "2"]))
    b = r.int("b", 1, 3)
    g = c * y**m
    integrand = pi * g**2
    val = sp.integrate(integrand, (y, 0, b))
    steps = _vol_steps(f"หน้าตัดตั้งฉากกับแกน $y$ เป็นวงกลมรัศมี $R(y) = {L(g)}$", integrand, 0, b, y, val, rf"V=\int_0^{{{b}}}\pi\left({L(g)}\right)^2dy")
    return Built(f"จงหาปริมาตรของทรงตันที่ได้จากการหมุนบริเวณระหว่าง $x = {L(g)}$, แกน $y$ และ $0\\le y\\le {b}$ รอบแกน $y$",
                 rf"x={L(g)},\ 0\le y\le {b}", val, ("definite", integrand, 0, b), steps, ["รัศมีคือระยะในแนวนอน $x = g(y)$"], var=y)


# ------------------------------------------------------------------ 6.2

def _shell_steps(radius, height, a, b, var, val, axis_th):
    integrand = 2 * pi * radius * height
    return integrand, [
        Step("shell.radius_height", f"{axis_th}: รัศมีเปลือก $= {L(radius)}$, ความสูงเปลือก $= {L(height)}$"),
        Step("shell.formula", "$V = \\int_a^b 2\\pi(\\text{รัศมี})(\\text{ความสูง})\\,d" + ("x" if var == x else "y") + "$",
             after_tex=integral_tex(integrand, a, b, var)),
        Step("ftc.part2", "อินทิเกรต", after=val, check=("eq", sp.integrate(sp.expand(integrand), (var, a, b)), val)),
    ]


@template("calc.6.2.shell_poly", "6.2", "วิธีเปลือกทรงกระบอก (Shell Method) รอบแกน y", ["6.2.shell", "6.2.radius_height"], {"b": (1, 4), "c": (1, 3)}, viz="revolution")
def shell_poly(r, d):
    b = r.int("b", 1, 4)
    c = r.int("c", 1, 3)
    h = c * x * (b - x)
    val = sp.integrate(2 * pi * x * h, (x, 0, b))
    integrand, steps = _shell_steps(x, h, 0, b, x, val, "หมุนรอบแกน $y$")
    return Built(f"จงหาปริมาตรเมื่อหมุนบริเวณใต้กราฟ $y = {L(sp.expand(h))}$ เหนือแกน $x$ รอบแกน $y$", rf"y={L(sp.expand(h))}",
                 val, ("definite", integrand, 0, b), steps, ["วิธี washer ต้องแก้ $x$ ในรูป $y$ ซึ่งยุ่ง ใช้ shell ง่ายกว่า"],
                 viz={"type": "revolution", "f": poly_str(sp.expand(h)), "a": 0, "b": b, "axis": "y", "method": "shell"})


@template("calc.6.2.shell_between", "6.2", "วิธีเปลือกสำหรับบริเวณระหว่างสองเส้นโค้ง", ["6.2.shell", "6.2.radius_height"], {"m": (1, 4)}, viz="revolution")
def shell_between(r, d):
    m = r.int("m", 1, 4)
    h = m * x - x**2
    val = sp.integrate(2 * pi * x * h, (x, 0, m))
    integrand, steps = _shell_steps(x, h, 0, m, x, val, "หมุนรอบแกน $y$")
    return Built(f"จงหาปริมาตรเมื่อหมุนบริเวณระหว่าง $y = {L(m * x)}$ และ $y = x^2$ รอบแกน $y$", rf"y={L(m * x)},\ y=x^2", val,
                 ("definite", integrand, 0, m), steps, ["ความสูงเปลือก = บน − ล่าง"],
                 viz={"type": "revolution", "f": poly_str(m * x), "g": "x^2", "a": 0, "b": m, "axis": "y", "method": "shell"})


@template("calc.6.2.shell_about_x", "6.2", "วิธีเปลือกรอบแกน x (อินทิเกรตเทียบกับ y)", ["6.2.shell", "6.2.compare"], {"b": (1, 3)}, viz="revolution")
def shell_about_x(r, d):
    b = r.int("b", 1, 3)
    h = b**2 - y**2
    val = sp.integrate(2 * pi * y * h, (y, 0, b))
    integrand, steps = _shell_steps(y, h, 0, b, y, val, "หมุนรอบแกน $x$ เปลือกวางแนวนอน")
    steps.append(Step("method.compare", "ตรวจด้วยวิธีจาน: $\\int_0^{b^2}\\pi x\\,dx$ ให้ค่าเท่ากัน", check=("eq", sp.integrate(pi * x, (x, 0, b**2)), val)))
    return Built(f"บริเวณที่ปิดล้อมด้วย $y = \\sqrt{{x}}$, $y = 0$ และ $x = {b**2}$ ถูกหมุนรอบแกน $x$ จงหาปริมาตรด้วยวิธีเปลือก", rf"y=\sqrt x,\ x={b**2}",
                 val, ("definite", integrand, 0, b), steps, ["รัศมีเปลือก = $y$", "ความสูง = $x$ ขวา − $x$ ซ้าย"], var=y,
                 viz={"type": "revolution", "f": "sqrt(x)", "a": 0, "b": b**2, "axis": "x", "method": "disk"})


@template("calc.6.2.shell_vertical_line", "6.2", "วิธีเปลือกรอบเส้นตรงแนวตั้ง", ["6.2.shell", "6.2.axis"], {"b": (1, 3), "c": (1, 3), "side": ("enum", ["left", "right"])},
          viz="revolution")
def shell_vertical_line(r, d):
    b = r.int("b", 1, 3)
    c = r.int("c", 1, 3)
    side = r.choice("side", ["left", "right"])
    axis = -c if side == "left" else b + c
    radius = x - axis if side == "left" else axis - x
    h = x**2
    val = sp.integrate(2 * pi * radius * h, (x, 0, b))
    integrand, steps = _shell_steps(radius, h, 0, b, x, val, f"แกนหมุน $x = {axis}$")
    return Built(f"บริเวณใต้ $y = x^2$ บน $[0,{b}]$ ถูกหมุนรอบเส้น $x = {axis}$ จงหาปริมาตร", rf"y=x^2,\ [0,{b}],\ x={axis}", val,
                 ("definite", integrand, 0, b), steps, ["รัศมีคือระยะจาก $x$ ถึงแกนหมุน (เป็นบวกเสมอ)"],
                 viz={"type": "revolution", "f": "x^2", "a": 0, "b": b, "axis": "y", "axisValue": axis, "method": "shell"})


@template("calc.6.2.shell_transcendental", "6.2", "วิธีเปลือกกับฟังก์ชันอดิศัย", ["6.2.shell", "8.2.parts"], {"form": ("enum", ["exp", "sin"]), "k": (1, 4), "b": (1, 3)},
          viz="revolution")
def shell_trans(r, d):
    form = r.choice("form", ["exp", "sin"])
    kk = r.int("k", 1, 4)
    if form == "exp":
        b = r.int("b", 1, 3); h = kk * sp.exp(x)
    else:
        b = pi; r.params["b"] = 1; h = kk * sp.sin(x)
    val = sp.simplify(sp.integrate(2 * pi * x * h, (x, 0, b)))
    integrand, steps = _shell_steps(x, h, 0, b, x, val, "หมุนรอบแกน $y$")
    steps.insert(2, Step("ibp.note", "อินทิกรัล $\\int x\\,h(x)\\,dx$ ต้องใช้การอินทิเกรตทีละส่วน (Integration by Parts)"))
    return Built(f"จงหาปริมาตรเมื่อหมุนบริเวณใต้ $y = {L(h)}$ บน $[0,{L(b)}]$ รอบแกน $y$", rf"y={L(h)},\ [0,{L(b)}]", val,
                 ("definite", integrand, 0, b), steps, ["ใช้ shell เพราะหา $x$ ในรูป $y$ ยาก"],
                 viz={"type": "revolution", "f": poly_str(h), "a": 0, "b": float(b), "axis": "y", "method": "shell"})


# ------------------------------------------------------------------ 6.3

def _arc_steps(f, fp, integrand_simpl, a, b, var, val, note=""):
    v = "x" if var == x else "y"
    return [
        Step("diff.basic", f"หาอนุพันธ์: ${'dy/dx' if v == 'x' else 'dx/dy'} = {L(fp)}$", after=fp, check=("eq", sp.diff(f, var), fp)),
        Step("arc.formula", f"$L = \\int_a^b \\sqrt{{1 + ({'dy/dx' if v == 'x' else 'dx/dy'})^2}}\\,d{v}$" + note,
             after_tex=integral_tex(sp.sqrt(1 + fp**2), a, b, var)),
        Step("algebra.simplify", "จัดรูปตัวถูกอินทิเกรต", after=integrand_simpl, check=("eq", sp.sqrt(1 + fp**2), integrand_simpl)),
        Step("ftc.part2", "อินทิเกรตและแทนขอบเขต", after=val, check=("eq", sp.integrate(integrand_simpl, (var, a, b)), val)),
    ]


@template("calc.6.3.arc_three_halves", "6.3", "ความยาวส่วนโค้งของ y = (2/3)x^(3/2)", ["6.3.arc_length"],
          {"a": ("enum", [0, 3, 8]), "b": ("enum", [3, 8, 15, 24])}, viz="arc")
def arc_32(r, d):
    a = r.choice("a", [0, 3, 8])
    b = r.choice("b", [bb for bb in [3, 8, 15, 24] if bb > a])
    f = R(2, 3) * x**R(3, 2)
    fp = sp.sqrt(x)
    val = R(2, 3) * ((1 + b)**R(3, 2) - (1 + a)**R(3, 2))
    return Built(f"จงหาความยาวส่วนโค้งของ $y = {L(f)}$ จาก $x = {a}$ ถึง $x = {b}$", rf"y={L(f)},\ {a}\le x\le {b}", val,
                 ("definite", sp.sqrt(1 + x), a, b), _arc_steps(f, fp, sp.sqrt(1 + x), a, b, x, val),
                 ["$1 + (y')^2 = 1 + x$"], viz={"type": "arc", "f": poly_str(f), "a": a, "b": b, "n": 4})


@template("calc.6.3.arc_perfect_square", "6.3", "ความยาวส่วนโค้งที่ 1 + (y')² เป็นกำลังสองสมบูรณ์", ["6.3.arc_length"],
          {"a": ("enum", ["1/3", "1/6", "1/12", "1/24"]), "lo": (1, 2), "hi": (2, 4)}, viz="arc")
def arc_ps(r, d):
    a = sp.Rational(r.choice("a", ["1/3", "1/6", "1/12", "1/24"]))
    lo = r.int("lo", 1, 2)
    hi = r.int("hi", lo + 1, 4)
    f = a * x**3 + 1 / (12 * a * x)
    fp = 3 * a * x**2 - 1 / (12 * a * x**2)
    integ = 3 * a * x**2 + 1 / (12 * a * x**2)
    F = a * x**3 - 1 / (12 * a * x)
    val = sp.simplify(F.subs(x, hi) - F.subs(x, lo))
    steps = _arc_steps(f, fp, integ, lo, hi, x, val, note="  โดย $1+(y')^2 = \\left(" + L(integ) + "\\right)^2$")
    return Built(f"จงหาความยาวส่วนโค้งของ $y = {L(f)}$ บน $[{lo},{hi}]$", rf"y={L(f)},\ [{lo},{hi}]", val, ("definite", integ, lo, hi), steps,
                 ["ขยาย $1+(y')^2$ แล้วดูว่าเป็นกำลังสองสมบูรณ์"], domain=(lo, hi), viz={"type": "arc", "f": poly_str(f), "a": lo, "b": hi, "n": 4})


@template("calc.6.3.arc_log_cos", "6.3", "ความยาวส่วนโค้งของ y = ln(cos x)", ["6.3.arc_length", "7.2.integration"],
          {"up": ("enum", ["pi/6", "pi/4", "pi/3"])}, viz="arc")
def arc_logcos(r, d):
    upn = r.choice("up", ["pi/6", "pi/4", "pi/3"])
    up = {"pi/6": pi / 6, "pi/4": pi / 4, "pi/3": pi / 3}[upn]
    f = sp.log(sp.cos(x))
    fp = -sp.tan(x)
    val = sp.log(sp.sec(up) + sp.tan(up))
    return Built(f"จงหาความยาวส่วนโค้งของ $y = \\ln(\\cos x)$ บน $\\left[0, {L(up)}\\right]$", rf"y=\ln(\cos x),\ 0\le x\le {L(up)}",
                 sp.simplify(val), ("definite", sp.sec(x), 0, up), _arc_steps(f, fp, sp.sec(x), 0, up, x, sp.simplify(val),
                                                                        note=" และ $1+\\tan^2x = \\sec^2x$, $\\sec x>0$ บนช่วงนี้"),
                 ["$\\int\\sec x\\,dx = \\ln|\\sec x + \\tan x| + C$"], domain=(0.05, float(up) - 0.05),
                 viz={"type": "arc", "f": "ln(cos(x))", "a": 0, "b": float(up), "n": 4})


@template("calc.6.3.arc_line", "6.3", "ความยาวส่วนโค้งของเส้นตรง (ตรวจด้วยระยะทาง)", ["6.3.arc_length", "6.3.derivation"],
          {"m": (-4, 4), "c": (-3, 3), "a": (-2, 0), "w": (1, 5)}, difficulties=(1,), viz="arc")
def arc_line(r, d):
    m = r.int("m", -4, 4, exclude=(0,))
    c = r.int("c", -3, 3)
    a, w = r.int("a", -2, 0), r.int("w", 1, 5)
    b = a + w
    f = m * x + c
    val = sp.sqrt(1 + m**2) * w
    steps = _arc_steps(f, sp.Integer(m), sp.sqrt(1 + m**2), a, b, x, val)
    steps.append(Step("geometry.distance", "ตรวจด้วยสูตรระยะทางระหว่างสองจุด", check=("eq", sp.sqrt(w**2 + (m * w)**2), val)))
    return Built(f"จงหาความยาวของ $y = {L(f)}$ จาก $x = {a}$ ถึง $x = {b}$ ด้วยสูตรความยาวส่วนโค้ง", rf"y={L(f)},\ [{a},{b}]", val,
                 ("definite", sp.sqrt(1 + m**2) + 0 * x, a, b), steps, ["$y'$ เป็นค่าคงที่"], viz={"type": "arc", "f": poly_str(f), "a": a, "b": b, "n": 2})


@template("calc.6.3.arc_x_of_y", "6.3", "ความยาวส่วนโค้งเมื่อเขียน x เป็นฟังก์ชันของ y", ["6.3.arc_length", "6.3.x_of_y"],
          {"a": ("enum", [0, 3, 8]), "b": ("enum", [3, 8, 15])})
def arc_xy(r, d):
    a = r.choice("a", [0, 3])
    b = r.choice("b", [bb for bb in [3, 8, 15] if bb > a])
    g = R(2, 3) * y**R(3, 2)
    val = R(2, 3) * ((1 + b)**R(3, 2) - (1 + a)**R(3, 2))
    return Built(f"จงหาความยาวส่วนโค้งของ $x = {L(g)}$ จาก $y = {a}$ ถึง $y = {b}$", rf"x={L(g)},\ {a}\le y\le {b}", val,
                 ("definite", sp.sqrt(1 + y), a, b), _arc_steps(g, sp.sqrt(y), sp.sqrt(1 + y), a, b, y, val), ["ใช้ $dx/dy$"], var=y)


@template("calc.6.3.arc_catenary", "6.3", "ความยาวส่วนโค้งของ catenary y = (eˣ + e⁻ˣ)/2", ["6.3.arc_length", "7.3.exp"],
          {"k": (2, 6)}, viz="arc")
def arc_catenary(r, d):
    kk = r.int("k", 2, 6)
    b = sp.log(kk)
    f = (sp.exp(x) + sp.exp(-x)) / 2
    fp = (sp.exp(x) - sp.exp(-x)) / 2
    integ = (sp.exp(x) + sp.exp(-x)) / 2
    val = R(kk**2 - 1, 2 * kk)
    return Built(f"จงหาความยาวส่วนโค้งของ $y = \\frac{{e^x + e^{{-x}}}}{{2}}$ จาก $x=0$ ถึง $x = \\ln {kk}$", rf"y=\frac{{e^x+e^{{-x}}}}{{2}},\ [0,\ln {kk}]",
                 val, ("definite", integ, 0, b), _arc_steps(f, fp, integ, 0, b, x, val), ["$1 + \\left(\\frac{e^x-e^{-x}}{2}\\right)^2 = \\left(\\frac{e^x+e^{-x}}{2}\\right)^2$"],
                 viz={"type": "arc", "f": "(exp(x)+exp(-x))/2", "a": 0, "b": float(b), "n": 3})


# ------------------------------------------------------------------ 6.4

def _surf_steps(f, fp, radius, integ, a, b, var, val, axis="x"):
    v = "x" if var == x else "y"
    return [
        Step("diff.basic", f"อนุพันธ์ $= {L(fp)}$", after=fp, check=("eq", sp.diff(f, var), fp)),
        Step("surface.formula", f"$S = \\int_a^b 2\\pi\\,(\\text{{รัศมี}})\\sqrt{{1+(\\text{{อนุพันธ์}})^2}}\\,d{v}$ รัศมี $= {L(radius)}$ (ระยะถึงแกน {axis})",
             after_tex=integral_tex(2 * pi * radius * sp.sqrt(1 + fp**2), a, b, var)),
        Step("algebra.simplify", "จัดรูปตัวถูกอินทิเกรต", after=integ, check=("eq", 2 * pi * radius * sp.sqrt(1 + fp**2), integ)),
        Step("ftc.part2", "อินทิเกรต (มักใช้การแทนค่า)", after=val, check=("eq", sp.integrate(integ, (var, a, b)), val)),
    ]


@template("calc.6.4.surface_cone", "6.4", "พื้นที่ผิวของกรวย (หมุนเส้นตรงรอบแกน x)", ["6.4.surface", "6.4.about_x"],
          {"m": ("enum", ["3/4", "4/3", "1", "2"]), "b": (1, 4)}, viz="surface")
def surf_cone(r, d):
    m = sp.Rational(r.choice("m", ["3/4", "4/3", "1", "2"]))
    b = r.int("b", 1, 4)
    f = m * x
    integ = 2 * pi * m * sp.sqrt(1 + m**2) * x
    val = sp.integrate(integ, (x, 0, b))
    steps = _surf_steps(f, m, f, integ, 0, b, x, val)
    steps.append(Step("geometry.cone", "ตรวจด้วยสูตรพื้นที่ผิวข้างของกรวย $\\pi r \\ell$", check=("eq", pi * (m * b) * sp.sqrt(b**2 + (m * b)**2), val)))
    return Built(f"จงหาพื้นที่ผิวที่เกิดจากการหมุน $y = {L(f)}$, $0\\le x\\le {b}$ รอบแกน $x$", rf"y={L(f)},\ [0,{b}]", val, ("definite", integ, 0, b), steps,
                 ["รัศมีคือ $y$"], viz={"type": "revolution", "f": poly_str(f), "a": 0, "b": b, "axis": "x", "method": "surface"})


@template("calc.6.4.surface_sphere_zone", "6.4", "พื้นที่ผิวของส่วนของทรงกลม", ["6.4.surface"], {"r": (1, 5), "a": (-5, 0), "b": (0, 5)}, viz="surface")
def surf_sphere(r_, d):
    rr = r_.int("r", 1, 5)
    a = r_.int("a", -rr, 0)
    b = r_.int("b", max(0, a + 1), rr)
    f = sp.sqrt(rr**2 - x**2)
    fp = -x / sp.sqrt(rr**2 - x**2)
    integ = 2 * pi * rr + 0 * x
    val = 2 * pi * rr * (b - a)
    return Built(f"จงหาพื้นที่ผิวที่เกิดจากการหมุน $y = \\sqrt{{{rr**2} - x^2}}$, ${a}\\le x\\le {b}$ รอบแกน $x$", rf"y=\sqrt{{{rr**2}-x^2}},\ [{a},{b}]",
                 val, ("definite", integ, a, b), _surf_steps(f, fp, f, integ, a, b, x, val), ["$y\\sqrt{1+(y')^2}$ ลดรูปเป็นค่าคงที่ $r$"],
                 domain=(a + 0.1 * (b - a), b - 0.1 * (b - a)), viz={"type": "revolution", "f": poly_str(f), "a": a, "b": b, "axis": "x", "method": "surface"})


@template("calc.6.4.surface_sqrt", "6.4", "พื้นที่ผิวของ y = √x หมุนรอบแกน x", ["6.4.surface", "5.5.substitution"],
          {"a": ("enum", [0, 2, 6]), "b": ("enum", [2, 6, 12])}, viz="surface")
def surf_sqrt(r, d):
    a = r.choice("a", [0, 2])
    b = r.choice("b", [bb for bb in [2, 6, 12] if bb > a])
    f = sp.sqrt(x)
    fp = 1 / (2 * sp.sqrt(x))
    integ = pi * sp.sqrt(4 * x + 1)
    val = pi / 6 * ((4 * b + 1)**R(3, 2) - (4 * a + 1)**R(3, 2))
    return Built(f"จงหาพื้นที่ผิวที่เกิดจากการหมุน $y = \\sqrt{{x}}$, ${a}\\le x\\le {b}$ รอบแกน $x$", rf"y=\sqrt x,\ [{a},{b}]", sp.simplify(val),
                 ("definite", integ, a, b), _surf_steps(f, fp, f, integ, a, b, x, sp.simplify(val)), ["$2\\pi\\sqrt{x}\\sqrt{1+\\frac{1}{4x}} = \\pi\\sqrt{4x+1}$"],
                 domain=(0.2, 3), viz={"type": "revolution", "f": "sqrt(x)", "a": a, "b": b, "axis": "x", "method": "surface"})


@template("calc.6.4.surface_cubic", "6.4", "พื้นที่ผิวของ y = cx³ หมุนรอบแกน x", ["6.4.surface", "5.6.change_limits"],
          {"c": ("enum", ["1", "1/3", "1/9"]), "b": (1, 2)}, viz="surface")
def surf_cubic(r, d):
    c = sp.Rational(r.choice("c", ["1", "1/3", "1/9"]))
    b = r.int("b", 1, 2)
    f = c * x**3
    fp = 3 * c * x**2
    integ = 2 * pi * c * x**3 * sp.sqrt(1 + 9 * c**2 * x**4)
    val = pi / (27 * c) * ((1 + 9 * c**2 * b**4)**R(3, 2) - 1)
    steps = _surf_steps(f, fp, f, integ, 0, b, x, sp.simplify(val))
    steps.insert(3, Step("sub.choose", f"แทน $w = 1 + {L(9 * c**2)}x^4$, $dw = {L(36 * c**2)}x^3dx$"))
    return Built(f"จงหาพื้นที่ผิวที่เกิดจากการหมุน $y = {L(f)}$, $0\\le x\\le {b}$ รอบแกน $x$", rf"y={L(f)},\ [0,{b}]", sp.simplify(val),
                 ("definite", integ, 0, b), steps, ["ใช้การแทนค่า $w = 1+(y')^2$"],
                 viz={"type": "revolution", "f": poly_str(f), "a": 0, "b": b, "axis": "x", "method": "surface"})


@template("calc.6.4.surface_about_y", "6.4", "พื้นที่ผิวเมื่อหมุนรอบแกน y", ["6.4.about_y", "6.4.surface"], {"b": (1, 2)}, viz="surface")
def surf_about_y(r, d):
    b = r.int("b", 1, 2)
    g = y**3 / 3
    gp = y**2
    integ = 2 * pi * g * sp.sqrt(1 + y**4)
    val = pi / 9 * ((1 + b**4)**R(3, 2) - 1)
    return Built(f"จงหาพื้นที่ผิวที่เกิดจากการหมุน $x = \\frac{{y^3}}{{3}}$, $0 \\le y \\le {b}$ รอบแกน $y$", rf"x=\frac{{y^3}}{{3}},\ [0,{b}]",
                 sp.simplify(val), ("definite", integ, 0, b), _surf_steps(g, gp, g, integ, 0, b, y, sp.simplify(val), axis="y"),
                 ["รัศมีคือ $x = g(y)$ ใช้ $dx/dy$"], var=y)
