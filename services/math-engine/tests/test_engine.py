"""Unit, regression and property tests for the math engine."""
from __future__ import annotations

import json

import pytest
import sympy as sp
from hypothesis import HealthCheck, given, settings, strategies as st

from unilearn_math import families  # noqa: F401
from unilearn_math import sample_subject  # noqa: F401
from unilearn_math.answer import check
from unilearn_math.core import REGISTRY
from unilearn_math.safe_parse import MathInputError, parse
from unilearn_math.server import handle
from unilearn_math.verify import DIVERGES, equal, generate

x = sp.Symbol("x")
REQUIRED = ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "6.1", "6.2", "6.3", "6.4",
            "7.1", "7.2", "7.3", "7.5", "8.1", "8.2", "8.3", "8.4", "8.5", "8.8"]
CALC = sorted(t for t in REGISTRY if t.startswith("calc."))


# ----------------------------------------------------------- parser

@pytest.mark.parametrize("src,expected", [
    ("1/2", sp.Rational(1, 2)), ("0.5", sp.Rational(1, 2)), ("2x", 2 * x), ("x^2", x**2), ("x**2", x**2),
    ("-x^2", -x**2), ("2^-1", sp.Rational(1, 2)), ("sin x", sp.sin(x)), ("sin^2(x)", sp.sin(x)**2), ("xe^x", x * sp.exp(x)),
    ("ln|x|", sp.log(sp.Abs(x))), ("sqrt(x+1)", sp.sqrt(x + 1)), ("π", sp.pi), ("2(x+1)", 2 * x + 2), ("e^(2x)", sp.exp(2 * x)),
    ("arctan(x/2)", sp.atan(x / 2)), ("log(2, 8)", sp.log(8, 2)), ("x²", x**2), ("3·x", 3 * x), ("(x+1)(x-1)", (x + 1) * (x - 1)),
    ("E^x", sp.exp(x)), ("Abs(x)", sp.Abs(x)),
])
def test_parse_valid(src, expected):
    assert sp.simplify(parse(src) - expected) == 0


@pytest.mark.parametrize("src", [
    "__import__('os').system('dir')", "x; import os", "exec(1)", "lambda: 1", "x" * 500, "(" * 60 + "x" + ")" * 60,
    "10^10^10", "9^9999", "foo(x)", "", "   ", "x +", "1/0", "a.b", "x[0]", "0^-1", "'x'",
])
def test_parse_rejects(src):
    with pytest.raises(MathInputError):
        parse(src)


def test_parse_never_evaluates_python():
    # names that exist in Python but not in the allowlist must be rejected, not executed
    for bad in ["open", "eval", "globals", "os", "sys", "print"]:
        with pytest.raises(MathInputError):
            parse(f"{bad}(x)")


# ----------------------------------------------------------- equivalence

def test_equal_symbolic_and_numeric():
    assert equal(sp.Rational(1, 2), sp.Float(0.5))[0] is not False
    assert equal((x + 1)**2, x**2 + 2 * x + 1)[0] is True
    assert equal(sp.sin(x)**2, 1 - sp.cos(x)**2)[0] is True
    assert equal(x, x + 1)[0] is False


def _problem(tid, seed=1, d=2):
    return generate(tid, seed, d)


def test_check_antiderivative_constant_and_forms():
    p = _problem("calc.8.2.poly_exp", 3, 2)
    b = p["_built"]
    ans = b.answer
    assert check(p, str(ans) + " + C")["correct"]
    r = check(p, str(ans))
    assert r["correct"] and r["missingConstant"]
    assert check(p, str(ans + 7))["correct"]            # differs by a constant
    assert not check(p, str(2 * ans))["correct"]


def test_check_log_abs_equivalent():
    p = _problem("calc.7.2.ln_integral", 2, 1)
    s = str(p["_built"].answer).replace("Abs", "")      # ln(3x+1) instead of ln|3x+1| on a domain where it's positive
    assert check(p, s)["correct"]


def test_check_reports_parse_errors_in_thai():
    p = _problem("calc.5.4.ftc2_poly")
    r = check(p, "x +* 2")
    assert not r["correct"] and r.get("parseError")


def test_check_rejects_foreign_symbols():
    p = _problem("calc.5.4.ftc2_poly")
    assert not check(p, "y + 1")["correct"]


def test_improper_divergence_words():
    for s in range(40):
        p = generate("calc.8.8.p_integral_infinity", s, 2)
        if p["_built"].answer == DIVERGES:
            assert check(p, "diverges")["correct"]
            assert check(p, "ลู่ออก")["correct"]
            assert not check(p, "1")["correct"]
            return
    pytest.fail("no divergent instance sampled")


# ----------------------------------------------------------- curriculum coverage

def test_every_required_section_has_five_families():
    for sec in REQUIRED:
        fams = [t for t in REGISTRY.values() if t.section_id == sec and t.subject == "calculus"]
        assert len(fams) >= 5, f"{sec} has {len(fams)} families"


def test_at_least_100_families():
    assert len(CALC) >= 100


# ----------------------------------------------------------- regression for every family

@pytest.mark.parametrize("tid", CALC + ["la.1.determinant_2x2", "la.1.dot_product"])
def test_family_regression(tid):
    tpl = REGISTRY[tid]
    keys = set()
    for d in tpl.difficulties:
        for s in range(6):
            p = generate(tid, s, d)
            assert p["statement"] and p["display"] and p["steps"], tid
            assert all(st_["verified"] is not False for st_ in p["steps"])
            assert p["verification"]["answer"] in ("symbolic", "numeric", "exact")
            keys.add(p["canonical"])
            # the reference answer, typed as a student would, must be accepted
            b = p["_built"]
            text = b.answer if isinstance(b.answer, str) else str(b.answer)
            res = check(p, text)
            assert res["correct"], (tid, s, d, text, res)
    assert len(keys) >= 2, f"{tid}: no variety"


@pytest.mark.parametrize("tid", ["calc.5.5.linear_inner", "calc.8.5.two_linear", "calc.7.5.lh_trig", "calc.6.1.washer_line_parabola"])
def test_reproducible(tid):
    a, b = generate(tid, 42, 2), generate(tid, 42, 2)
    assert a["display"] == b["display"] and a["answerTex"] == b["answerTex"] and a["params"] == b["params"]
    assert json.dumps(a["steps"]) == json.dumps(b["steps"])


def test_difficulty_changes_parameters():
    p1 = generate("calc.5.1.left_sum", 5, 1)
    p3 = generate("calc.5.1.left_sum", 5, 3)
    assert p1["params"]["n"] < p3["params"]["n"]


@settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(tid=st.sampled_from(CALC), seed=st.integers(0, 10**6), d=st.integers(1, 3))
def test_property_generated_instances_verify(tid, seed, d):
    p = generate(tid, seed, d)
    b = p["_built"]
    assert all(s["verified"] is not False for s in p["steps"])
    text = b.answer if isinstance(b.answer, str) else str(b.answer)
    assert check(p, text)["correct"]


# ----------------------------------------------------------- server protocol

def test_server_roundtrip():
    r = handle({"id": 1, "method": "ping"})
    assert r["ok"] and r["result"]["templates"] >= 100
    g = handle({"id": 2, "method": "generate", "params": {"templateId": "calc.5.5.power_chain", "seed": 7, "difficulty": 2}})
    assert g["ok"] and "answer" not in g["result"] and "_built" not in g["result"]
    c = handle({"id": 3, "method": "check", "params": {"templateId": "calc.5.5.power_chain", "seed": 7, "difficulty": 2, "answer": "x"}})
    assert c["ok"] and c["result"]["correct"] is False
    bad = handle({"id": 4, "method": "nope"})
    assert not bad["ok"]
    e = handle({"id": 5, "method": "exam", "params": {"sections": ["5.5", "8.2"], "count": 6, "seed": 1}})
    assert e["ok"] and len(e["result"]) == 6 and all("answerTex" not in q for q in e["result"])
    assert len({q["canonical"] for q in e["result"]}) == 6


def test_server_preview():
    assert handle({"id": 1, "method": "preview", "params": {"text": "x^2/2"}})["result"]["ok"]
    assert not handle({"id": 1, "method": "preview", "params": {"text": "import os"}})["result"]["ok"]
