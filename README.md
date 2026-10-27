# UniLearn Studio

Offline-first university learning desktop app for Windows 10/11 x64. First subject: **Calculus — integrals and
applications** (20 exam sections of *Thomas' Calculus*, 14th ed.), Thai explanations with English terminology.

* 20 original Thai lessons (three explanation depths, definitions, theorems, formulas, worked examples that are
  re-verified with SymPy, misconceptions, interactive 2D/3D visualizations, verified textbook page references)
* 129 procedurally generated, symbolically verified problem families (≥5 per section) — 14,047 unique instances
  measured, structured step-by-step solutions, hints, answer equivalence checking
* Guided / free / weakness-review practice, timed exam simulation (chapter presets + full final), progress analytics
* Optional AI tutor through the locally installed Claude Code CLI — never required, never replaces verified answers
* Multi-subject package architecture (plus a small, clearly-labelled linear-algebra example)

Install: run `release/UniLearn Studio_1.0.0_x64-setup.exe` (or the `.msi`). Students do not need Python, Node or Rust.

| Doc | |
|---|---|
| `docs/implementation-status.md` | what is done, measured numbers, known limitations |
| `docs/curriculum-coverage.md` | per-section coverage (generated) |
| `docs/architecture.md` · `docs/problem-engine.md` | design |
| `docs/testing.md` · `docs/mathematical-validation/report.md` | quality |
| `docs/build-and-release.md` · `docs/user-guide/README.md` · `docs/development/CONTRIBUTING.md` | how-to |

Textbook content is used only as a private-study reference for curriculum alignment; lessons and exercises are original.
