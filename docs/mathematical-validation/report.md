# Mathematical validation report

Date: 2026-10-26 · Engine 1.0.0 · Rules 1.0.0 · SymPy 1.14.0 · Python 3.14.5

## Method

* **Generated problems:** every instance passes `verify.generate` — schema check, independent reference answer
  (SymPy `integrate` / `diff` / `limit` / `summation`, or an explicit witness/choice function), equality of the
  family's answer to that reference, and verification of every step that carries a check. Failures raise and are
  never published.
* **Equality:** `simplify(a − b) == 0`, then `trigsimp` + `expand_log`; otherwise agreement to 1e‑9 relative at 10
  random rational points of the declared domain with 30-digit evaluation → labelled `numeric`. Any disagreement →
  rejected. `|g|` is replaced by `±g` only when `g` has constant sign at 9 sample points of the domain.
* **Indefinite integrals:** verified by differentiating the answer and comparing to the integrand on the domain.
* **Definite / improper integrals:** compared to SymPy's exact value; divergence asserted when SymPy returns ±∞/zoo
  or (interior singularities) by splitting at the singular point.
* **L'Hôpital:** each family checks that the form is indeterminate before differentiation
  (`lhopital.check`), and `calc.7.5.lh_not_applicable` tests that the rule is *not* applied.
* **Lesson worked examples:** all 58 worked examples across the 20 lessons carry machine-checkable `verify` blocks;
  `tools/curriculum-validator/validate.py` re-checks them on every run (all pass).

## Results

| Check | Result |
|---|---|
| pytest (unit, regression for all 131 families, property-based, protocol) | **187 passed** |
| Benchmark sweep, 120 seeds × difficulty | 45,840 generated, **0 failures**, 14,047 unique |
| Answer verification methods (same sweep) | 43,813 symbolic · 1,303 exact · 724 numeric-only |
| Lesson examples | 58/58 verified (see `subjects/calculus/curriculum/coverage-manifest.json`) |

## Known limits

* Numeric-only agreement (724 of 45,840 answers ≈ 1.6% in the 120-seed sweep) is strong evidence, not a proof;
  those instances are labelled `numeric` in the UI. Per-family counts are in `docs/reports/benchmark-report.json`.
* Step checks verify algebraic equivalence of each transformation, not the pedagogical quality of the Thai text.
* **No human mathematician has reviewed the lessons or step texts yet** — all lessons are `machine-validated`, review pending.
