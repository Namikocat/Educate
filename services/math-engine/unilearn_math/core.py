"""Problem-template contract, seeded sampling, structured solution steps and the registry."""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Any, Callable

import sympy as sp

RULE_ENGINE_VERSION = "1.0.0"

x = sp.Symbol("x")


class Reject(Exception):
    """Raised by a generator when sampled parameters give a degenerate/invalid instance."""


# ---------------------------------------------------------------- sampling


class Rand:
    """Seeded sampler that records every drawn parameter for reproducibility and schema checks."""

    def __init__(self, seed_key: str):
        self._r = random.Random(seed_key)
        self.params: dict[str, Any] = {}

    def int(self, name: str, lo: int, hi: int, exclude: tuple = ()) -> int:
        choices = [i for i in range(lo, hi + 1) if i not in exclude]
        val = self._r.choice(choices)
        self.params[name] = val
        return val

    def choice(self, name: str, options: list):
        idx = self._r.randrange(len(options))
        val = options[idx]
        self.params[name] = val if isinstance(val, (int, str)) else str(val)
        return val

    def sign(self, name: str) -> int:
        return self.choice(name, [-1, 1])


# ---------------------------------------------------------------- solution structure


@dataclass
class Step:
    rule: str                      # rule id, e.g. "ibp.formula"
    explain_th: str                # Thai explanation (may contain $latex$)
    before: sp.Basic | None = None
    after: sp.Basic | None = None
    before_tex: str | None = None  # overrides when the object is not a plain expression (integrals, sums)
    after_tex: str | None = None
    assumptions: list[str] = field(default_factory=list)
    # verification of this transformation: ("eq", a, b) | ("deriv", F, f) | ("none", reason)
    check: tuple | None = None
    viz: str | None = None
    verified: bool | None = None
    check_method: str | None = None

    def to_json(self) -> dict:
        return {
            "rule": self.rule, "explain": self.explain_th,
            "before": self.before_tex if self.before_tex is not None else (L(self.before) if self.before is not None else None),
            "after": self.after_tex if self.after_tex is not None else (L(self.after) if self.after is not None else None),
            "assumptions": self.assumptions, "verified": self.verified, "checkMethod": self.check_method, "viz": self.viz,
        }


@dataclass
class Built:
    """What a family generator returns before the verification pipeline runs."""
    statement: str                 # Thai text with $..$ inline math
    display: str                   # main LaTeX shown large
    answer: Any                    # sympy expr, or a choice id (str)
    verify: tuple                  # independent reference computation (see verify.py)
    steps: list[Step]
    hints: list[str]
    answer_type: str = "expr"      # expr | antiderivative | choice | improper
    choices: list[dict] | None = None
    var: sp.Symbol = x
    domain: tuple | None = None    # sampling interval for numeric checks, e.g. (0.5, 3)
    viz: dict | None = None
    canonical: str | None = None   # override for duplicate detection
    answer_tex: str | None = None


@dataclass
class Template:
    id: str
    section_id: str
    title_th: str
    objectives: list[str]
    params: dict[str, tuple]       # parameter schema: name -> (lo, hi) or ("enum", [...])
    gen: Callable[[Rand, int], Built]
    answer_type: str
    difficulties: tuple[int, ...] = (1, 2, 3)
    visualization: str | None = None
    common_errors: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    subject: str = "calculus"

    def meta(self) -> dict:
        return {"id": self.id, "subject": self.subject, "section": self.section_id, "title": self.title_th,
                "objectives": self.objectives, "params": {k: list(v) if isinstance(v, tuple) else v for k, v in self.params.items()},
                "answerType": self.answer_type, "difficulties": list(self.difficulties), "visualization": self.visualization,
                "commonErrors": self.common_errors, "version": self.version}


REGISTRY: dict[str, Template] = {}


def template(id: str, section: str, title: str, objectives: list[str], params: dict, answer_type: str = "expr",
             difficulties=(1, 2, 3), viz: str | None = None, errors: list[str] | None = None, version: str = "1.0.0",
             subject: str = "calculus"):
    def deco(fn: Callable[[Rand, int], Built]):
        if id in REGISTRY:
            raise ValueError(f"duplicate template id {id}")
        REGISTRY[id] = Template(id, section, title, objectives, params, fn, answer_type, tuple(difficulties), viz,
                                errors or [], version, subject)
        return fn
    return deco


def seed_key(tid: str, version: str, seed: int, difficulty: int) -> str:
    return f"{tid}|{version}|{seed}|{difficulty}|{RULE_ENGINE_VERSION}"


def validate_params(tpl: Template, params: dict) -> list[str]:
    errs = []
    for name, val in params.items():
        spec = tpl.params.get(name)
        if spec is None:
            errs.append(f"parameter {name} not declared in schema")
        elif spec and spec[0] == "enum":
            if val not in spec[1] and str(val) not in [str(s) for s in spec[1]]:
                errs.append(f"{name}={val} not in enum")
        elif isinstance(val, int) and not (spec[0] <= val <= spec[1]):
            errs.append(f"{name}={val} outside [{spec[0]}, {spec[1]}]")
    return errs


def canonical_key(tid: str, built: Built) -> str:
    raw = built.canonical or (built.statement + "||" + built.display)
    return hashlib.sha1(f"{tid}::{raw}".encode()).hexdigest()[:16]


# ---------------------------------------------------------------- LaTeX helpers

def L(e) -> str:
    return sp.latex(e, ln_notation=True)


def integral_tex(f, a=None, b=None, var=x) -> str:
    lim = "" if a is None else f"_{{{L(a)}}}^{{{L(b)}}}"
    return rf"\int{lim} {L(f)}\,d{L(var)}"


def plus_c(e) -> str:
    return L(e) + " + C"


def difficulty_score(expr) -> int:
    """Transparent complexity heuristic used by the difficulty classifier."""
    try:
        return int(sp.count_ops(expr, visual=False))
    except Exception:
        return 0
