# Testing

| Layer | Command | What it covers |
|---|---|---|
| Math engine (pytest + hypothesis) | `cd services/math-engine && .venv\Scripts\python -X utf8 -m pytest -q` | parser accept/reject (incl. injection attempts), equivalence, +C / ln|x| handling, divergence words, ≥5 families per section, **regression for every family** (6 seeds × each difficulty: steps verified, reference answer accepted when typed as a student), reproducibility, difficulty effect, property-based random (template, seed, difficulty), sidecar protocol & exam de-duplication |
| Content | `python tools/curriculum-validator/validate.py subjects/calculus --write` | lesson schema, every worked example re-verified with SymPy, page refs injected from the verified curriculum map, objective coverage |
| Benchmark | `python tools/problem-benchmark/benchmark.py 120 docs/reports/benchmark-report.json` | failure sweep, unique instance count, latency |
| Frontend (vitest) | `cd apps/desktop && npx vitest run` | plot compiler allow/deny, spec validation, Riemann/Simpson numerics, mastery model, package registry compatibility |
| Rust (cargo test) | `cd apps/desktop/src-tauri && cargo test` | migrations idempotent, attempts/progress/notes/bookmarks, export→import round trip, input validation, corrupt-DB recovery, base64, Claude prompt/error classification |
| E2E (manual, recorded) | browser pane against the HTTP dev bridge, and the installed app | onboarding → lesson → 5.5 substitution problem → wrong answer (sign-error feedback) → correct answer (missing +C note) → verified steps; 3D cross-section volume readout |

Latest results are recorded in `docs/implementation-status.md`. Symbolic-inconclusive comparisons fall back to
high-precision numeric agreement, which is labelled `numeric` everywhere (never claimed as proof).
