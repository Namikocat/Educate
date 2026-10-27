# Problem engine

Source: `services/math-engine/unilearn_math/`.

## Template contract (`core.py`)

```python
@template("calc.8.2.poly_exp", "8.2", "Integration by Parts: พหุนาม × เอกซ์โพเนนเชียล",
          objectives=["8.2.parts", "8.2.choose_u", "8.2.verify"],
          params={"a": (-4, 4), "p": (-5, 5), "c": (1, 4)},   # parameter schema, enforced after sampling
          answer_type="antiderivative", difficulties=(1, 2, 3), viz=None, errors=[...], version="1.0.0")
def ibp_poly_exp(r: Rand, d: int) -> Built: ...
```

`Built` carries: Thai statement, display LaTeX, answer (SymPy or choice id), an **independent** reference
computation (`verify`), structured `Step`s (rule id, Thai explanation, before/after, assumptions, check), hints,
domain for numeric checks, visualization spec, optional canonical key.

## Pipeline (`verify.generate`)

1. `Rand(seed_key(template, version, seed, difficulty, rule_version) + attempt)` — deterministic.
2. Generator may raise `Reject` (degenerate parameters) → deterministic resample (≤40 tries).
3. Sampled params validated against the declared schema (violations fail loudly in tests).
4. Reference answer computed independently: `integrate`, `diff`, `limit`, `summation`, or a witness/choice function.
5. Answer compared to reference: `simplify` → `trigsimp/expand_log` → high-precision numeric agreement at 10
   points of the declared domain. `|g|` is replaced by `±g` only where the sign is constant on that domain.
6. Every step's `check` (`eq`, `deriv`, predicate) is verified; any failure **rejects** the template instance.
7. Publish with `verification.answer ∈ {symbolic, numeric, exact}` and per-step methods. Numeric-only agreement
   is reported as such, never as a proof.

## Answer checking (`answer.py`)

Untrusted text → `safe_parse.parse` (allowlist, ≤400 chars, ≤250 tokens, depth ≤40, |integer exponent| ≤200) →
type-specific grading: antiderivatives by differentiating the student's answer (any constant accepted, missing
`+C` flagged), expressions by equivalence, improper integrals accept “diverges/ลู่ออก”, choices by id. Error
classes: `sign_error`, `coefficient_error`, `constant_offset`, `differentiated_instead`.

## Numbers (measured — see `docs/reports/benchmark-report.json`)

* 129 Calculus families (5–8 per section) + 2 sample-subject families.
* 120 seeds × each difficulty → 45,840 generations, **14,047 unique instances** after canonical de-duplication
  (key = template id + statement + display), **0 failures**.
* Generation latency: mean 31 ms, p95 97 ms, max 609 ms (pipeline incl. verification, Python 3.14, this machine).
* Answer verification methods across the same 45,840 generations: 43,813 symbolic, 1,303 exact, 724 numeric-only.

Some families have intentionally small parameter spaces (e.g. `calc.6.4.surface_about_y`: 2 instances) because
widening them would require non-elementary or unpedagogical integrals; they are still counted honestly.
