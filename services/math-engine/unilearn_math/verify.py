"""Verification pipeline: every generated instance is checked before it can be published.

Order: params -> schema -> build -> reference answer (independent) -> each step's transformation
-> final answer -> difficulty/uniqueness -> publish or reject.
Symbolic proof is primary; high-precision numeric agreement is recorded separately as a weaker
method and never reported as a proof.
"""
from __future__ import annotations

import random

import mpmath
import sympy as sp

from .core import L, Built, Rand, Reject, REGISTRY, Step, Template, canonical_key, difficulty_score, seed_key, validate_params

x = sp.Symbol("x")
DIVERGES = "diverges"
NUMERIC_POINTS = 10


def _num(e, var, val):
    try:
        z = complex(sp.N(e.subs(var, val), 30))
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    if z != z or abs(z.imag) > 1e-12 * max(1, abs(z.real)) or abs(z.real) == float("inf"):
        return None
    return z.real


def deabs(e, var=x, domain=None):
    """Replace |g| by g or -g when g has constant sign on the sampling domain (sound on that domain)."""
    e = sp.sympify(e)
    lo, hi = domain or (0.3, 2.7)
    pts = [sp.Rational(round(lo + (hi - lo) * i / 8, 6)) for i in range(9)]
    reps = {}
    for ab in e.atoms(sp.Abs):
        vals = [_num(ab.args[0], var, p) for p in pts]
        if all(v is not None and v > 0 for v in vals):
            reps[ab] = ab.args[0]
        elif all(v is not None and v < 0 for v in vals):
            reps[ab] = -ab.args[0]
    return e.xreplace(reps) if reps else e


def d_dx(F, var=x, domain=None):
    return sp.diff(deabs(F, var, domain), var)


def equal(a, b, var=x, domain=None, seed=0) -> tuple[bool | None, str]:
    """True=proved symbolically, None=only numerically agreeing, False=disproved."""
    a, b = deabs(a, var, domain), deabs(b, var, domain)
    try:
        diff = sp.simplify(sp.expand(a - b))
        if diff == 0:
            return True, "symbolic"
        d2 = sp.simplify(sp.expand_log(sp.trigsimp(diff), force=True))
        if d2 == 0:
            return True, "symbolic"
        if d2.is_number and d2.free_symbols == set() and abs(complex(sp.N(d2))) > 1e-12:
            return False, "symbolic"
    except Exception:
        pass
    free = (sp.sympify(a).free_symbols | sp.sympify(b).free_symbols) - {var}
    if free:
        return False, "free-symbols"
    lo, hi = domain or (0.3, 2.7)
    rng = random.Random(seed)
    good = 0
    for _ in range(NUMERIC_POINTS * 3):
        p = sp.Rational(round(rng.uniform(lo, hi), 6))
        va, vb = _num(a, var, p), _num(b, var, p)
        if va is None or vb is None:
            continue
        if abs(va - vb) > 1e-9 * max(1.0, abs(va), abs(vb)):
            return False, "numeric"
        good += 1
        if good >= NUMERIC_POINTS:
            return None, "numeric"
    return False, "inconclusive"


def reference(built: Built):
    """Compute the reference answer independently of the family's own answer."""
    kind = built.verify[0]
    v = built.var
    if kind == "antiderivative":
        return ("deriv", built.verify[1])
    if kind == "definite":
        _, f, a, b = built.verify
        return ("value", sp.integrate(f, (v, a, b)))
    if kind == "derivative":
        return ("value", sp.diff(built.verify[1], v))
    if kind == "limit":
        _, e, pt, d = built.verify
        return ("value", sp.limit(e, v, pt, d))
    if kind == "sum":
        _, term, kk, lo, hi = built.verify
        return ("value", sp.summation(term, (kk, lo, hi)))
    if kind == "improper":
        _, f, a, b = built.verify
        r = sp.integrate(f, (v, a, b))
        if r.has(sp.oo, -sp.oo, sp.zoo, sp.nan, sp.AccumBounds) or isinstance(r, sp.Integral):
            return ("value", DIVERGES)
        return ("value", r)
    if kind == "value":
        return ("value", built.verify[1])
    if kind == "choice":
        return ("value", built.verify[1]())
    raise ValueError(f"unknown verify kind {kind}")


def check_answer_against(built: Built, ref) -> tuple[bool | None, str]:
    tag, val = ref
    if tag == "deriv":
        return equal(d_dx(built.answer, built.var, built.domain), val, built.var, built.domain)
    if isinstance(val, str) or isinstance(built.answer, str):
        return (built.answer == val, "exact")
    if built.answer_type == "improper" and val == DIVERGES:
        return (False, "exact")
    return equal(sp.nsimplify(built.answer) if isinstance(built.answer, float) else built.answer, val, built.var, built.domain)


def check_step(step: Step, built: Built) -> None:
    if step.check is None:
        step.verified, step.check_method = None, "explanatory"
        return
    kind = step.check[0]
    if kind == "eq":
        ok, m = equal(step.check[1], step.check[2], built.var, built.domain)
    elif kind == "deriv":
        ok, m = equal(d_dx(step.check[1], built.var, built.domain), step.check[2], built.var, built.domain)
    elif kind == "true":
        ok, m = bool(step.check[1]), "predicate"
    else:
        raise ValueError(kind)
    step.verified = ok is not False
    step.check_method = m


class Published(dict):
    pass


def generate(tid: str, seed: int, difficulty: int = 2, max_tries: int = 40) -> dict:
    """Run the full pipeline. Rejected samples are resampled deterministically (seed, attempt)."""
    tpl: Template = REGISTRY[tid]
    if difficulty not in tpl.difficulties:
        difficulty = min(tpl.difficulties, key=lambda d: abs(d - difficulty))
    reasons: list[str] = []
    for attempt in range(max_tries):
        r = Rand(seed_key(tid, tpl.version, seed, difficulty) + f"|{attempt}")
        try:
            built = tpl.gen(r, difficulty)
        except Reject as e:
            reasons.append(f"reject:{e}")
            continue
        errs = validate_params(tpl, r.params)
        if errs:
            raise AssertionError(f"{tid}: schema violation {errs}")
        ref = reference(built)
        ok, method = check_answer_against(built, ref)
        if ok is False:
            raise AssertionError(f"{tid} seed={seed} d={difficulty}: answer {built.answer} != reference {ref[1]} ({method})")
        for st in built.steps:
            check_step(st, built)
        bad = [s.rule for s in built.steps if s.verified is False]
        if bad:
            raise AssertionError(f"{tid} seed={seed}: step verification failed {bad}")
        return _publish(tpl, built, seed, difficulty, attempt, r.params, method)
    raise RuntimeError(f"{tid}: no valid instance after {max_tries} tries: {reasons[-3:]}")


def _publish(tpl: Template, b: Built, seed: int, difficulty: int, attempt: int, params: dict, method: str) -> dict:
    if b.answer_tex is not None:
        ans_tex = b.answer_tex
    elif isinstance(b.answer, str):
        ans_tex = next((c["label"] for c in (b.choices or []) if c["id"] == b.answer), b.answer)
    else:
        ans_tex = L(b.answer) + (" + C" if b.answer_type == "antiderivative" else "")
    return {
        "id": f"{tpl.id}@{tpl.version}#{seed}.{difficulty}",
        "templateId": tpl.id, "templateVersion": tpl.version, "seed": seed, "difficulty": difficulty,
        "attempt": attempt, "params": params, "section": tpl.section_id, "subject": tpl.subject, "title": tpl.title_th,
        "statement": b.statement, "display": b.display, "answerType": b.answer_type, "choices": b.choices,
        "answerTex": ans_tex,
        "variable": str(b.var), "steps": [s.to_json() for s in b.steps], "hints": b.hints, "viz": b.viz,
        "verification": {"answer": method, "steps": [s.check_method for s in b.steps]},
        "complexity": difficulty_score(b.answer) if not isinstance(b.answer, str) else 0,
        "canonical": canonical_key(tpl.id, b), "objectives": tpl.objectives,
        "_verify": b.verify, "_built": b,
    }


def public(problem: dict) -> dict:
    return {k: v for k, v in problem.items() if not k.startswith("_")}
