"""Shared helpers for family generators."""
from __future__ import annotations

import sympy as sp

from ..core import L, Step, integral_tex

x, y, t, u, k, n = sp.symbols("x y t u k n")
R = sp.Rational


def poly_str(e) -> str:
    """Expression string for the frontend plot evaluator (same restricted grammar)."""
    return str(e).replace("**", "^")


def riemann(f, a, b, nn: int, method: str):
    dx = R(b - a, nn) if isinstance(a, int) and isinstance(b, int) else (b - a) / nn
    if method == "left":
        pts = [a + i * dx for i in range(nn)]
    elif method == "right":
        pts = [a + (i + 1) * dx for i in range(nn)]
    else:
        pts = [a + (2 * i + 1) * dx / 2 for i in range(nn)]
    return sp.nsimplify(sum(f.subs(x, p) for p in pts) * dx), dx, pts


def eval_between(F, a, b, var=x):
    return sp.simplify(F.subs(var, b) - F.subs(var, a))


def ftc_steps(f, F, a, b, var=x, area_word="") -> list[Step]:
    val = eval_between(F, a, b, var)
    return [
        Step("integral.antiderivative", f"หาปฏิยานุพันธ์ (antiderivative) ของ ${L(f)}$ ได้ $F({L(var)}) = {L(F)}$",
             before_tex=integral_tex(f, a, b, var), after=F, check=("deriv", F, f)),
        Step("ftc.part2", f"ใช้ทฤษฎีบทหลักมูลของแคลคูลัส ส่วนที่ 2 (FTC Part 2): $F({L(b)}) - F({L(a)})$" + area_word,
             before_tex=rf"\left[{L(F)}\right]_{{{L(a)}}}^{{{L(b)}}}", after=val, check=("eq", val, F.subs(var, b) - F.subs(var, a))),
    ]


def sub_steps(f, g, du_dx, F_u, answer, var=x, extra: str = "") -> list[Step]:
    """Substitution u = g(x): records the substitution, transformed integrand and back-substitution."""
    tu = sp.simplify(f / du_dx).subs(g, u)
    if tu.has(var):  # e.g. g = sin(ax): try rewriting the inner function explicitly
        tu = sp.simplify(sp.powsimp(sp.factor(f / du_dx))).subs(g, u)
    if tu.has(var) and g.is_polynomial(var) and sp.degree(g, var) == 1:  # invert a linear substitution
        tu = sp.simplify((f / du_dx).subs(var, sp.solve(sp.Eq(g, u), var)[0]))
    transformed = None if tu.has(var) else tu
    steps = [
        Step("sub.choose", f"เลือก $u = {L(g)}$ เพราะอนุพันธ์ของ $u$ ปรากฏอยู่ในตัวถูกอินทิเกรต" + extra, after_tex=f"u = {L(g)}"),
        Step("sub.du", f"หาอนุพันธ์: $du = {L(du_dx)}\\,d{L(var)}$", after=du_dx, check=("eq", sp.diff(g, var), du_dx)),
    ]
    if transformed is not None:
        steps.append(Step("sub.transform", "เขียนอินทิกรัลใหม่ในรูปของ $u$ ทั้งหมด",
                          before_tex=integral_tex(f, var=var), after_tex=integral_tex(transformed, var=u),
                          check=("eq", transformed.subs(u, g) * du_dx, f)))
    steps += [
        Step("integral.power_rule", "อินทิเกรตเทียบกับ $u$", after_tex=L(F_u) + " + C",
             check=("eq", sp.diff(F_u, u).subs(u, g) * du_dx, f) if transformed is not None else None),
        Step("sub.back", f"แทนค่ากลับ $u = {L(g)}$ แล้วตรวจสอบโดยการหาอนุพันธ์", after_tex=L(answer) + " + C",
             check=("deriv", answer, f)),
    ]
    return steps
