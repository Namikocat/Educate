"""Minimal second-subject example (Linear Algebra preview).

Demonstrates that the template registry, verification pipeline and UI are subject-agnostic.
It is NOT a complete course: two families for one introductory section only.
"""
from __future__ import annotations

import sympy as sp

from .core import Built, Reject, Step, L, template

SUBJ = "sample-linear-algebra"


@template("la.1.determinant_2x2", "la.1", "ดีเทอร์มิแนนต์ของเมทริกซ์ 2×2", ["la.1.determinant"],
          {"a": (-6, 6), "b": (-6, 6), "c": (-6, 6), "d": (-6, 6)}, subject=SUBJ)
def det2(r, dlev):
    a, b, c, d = (r.int(k, -6, 6) for k in "abcd")
    M = sp.Matrix([[a, b], [c, d]])
    val = a * d - b * c
    steps = [Step("la.det2", "$\\det\\begin{pmatrix}a&b\\\\c&d\\end{pmatrix} = ad - bc$", after=sp.Integer(val), check=("eq", M.det(), val))]
    return Built(f"จงหา $\\det {L(M)}$", rf"\det {L(M)}", sp.Integer(val), ("value", M.det()), steps, ["คูณแนวทแยงหลักลบแนวทแยงรอง"])


@template("la.1.dot_product", "la.1", "ผลคูณจุดของเวกเตอร์ใน R³", ["la.1.dot_product"],
          {"u1": (-5, 5), "u2": (-5, 5), "u3": (-5, 5), "v1": (-5, 5), "v2": (-5, 5), "v3": (-5, 5)}, subject=SUBJ)
def dot(r, dlev):
    u = sp.Matrix([r.int(f"u{i}", -5, 5) for i in (1, 2, 3)])
    v = sp.Matrix([r.int(f"v{i}", -5, 5) for i in (1, 2, 3)])
    if u.norm() == 0 or v.norm() == 0:
        raise Reject("zero vector")
    val = u.dot(v)
    steps = [Step("la.dot", "$\\mathbf u\\cdot\\mathbf v = u_1v_1 + u_2v_2 + u_3v_3$", after=sp.Integer(val), check=("eq", sum(u[i] * v[i] for i in range(3)), val))]
    return Built(f"จงหา $\\mathbf u\\cdot\\mathbf v$ เมื่อ $\\mathbf u = {L(u.T)}$, $\\mathbf v = {L(v.T)}$", rf"{L(u.T)}\cdot{L(v.T)}", sp.Integer(val),
                 ("value", u.dot(v)), steps, ["คูณสมาชิกตำแหน่งเดียวกันแล้วรวม"])
