# CLAUDE.md — UniLearn Studio

Offline-first Windows learning app (Tauri 2 + React/TS + Python/SymPy sidecar). Initial subject: Calculus, 20 exam
sections of *Thomas' Calculus* 14e (5.1–5.6, 6.1–6.4, 7.1–7.3, 7.5, 8.1–8.5, 8.8), Thai explanations with English terms.
The full master specification was pasted in chat (not stored as a file); its binding points are in `docs/requirements.md`.

**Live status, numbers and open issues: `docs/implementation-status.md`. Update it after every work session.**

## Where things are
* `services/math-engine/unilearn_math/` — `safe_parse.py` (restricted grammar; never eval/sympify user text),
  `core.py` (template contract, seeded `Rand`, `Step`), `verify.py` (verification pipeline), `answer.py` (grading),
  `families/ch5..ch8.py` (129 families), `sample_subject.py`, `server.py` (stdio JSON lines; `--http 8765` dev bridge).
* `apps/desktop/src/` — pages, components (`VizView`, `Plot2D`, lazy `Viz3D`, `MathInput`, `Tex`), `lib/backend.ts`
  (Tauri IPC vs browser dev fallback). `apps/desktop/src-tauri/src/` — `db.rs`, `sidecar.rs`, `claude.rs`, `lib.rs`.
* `packages/{visualization,assessment,curriculum}-core/src` — shared TS (plot compiler, mastery, package registry).
* `subjects/calculus/` — `manifest.json`, `lessons/*.json`, `curriculum/source/` (verified page map from the PDF),
  `curriculum/coverage-manifest.json` (generated). `subjects/sample-subject/` — clearly-labelled example only.
* `tools/` — `textbook-importer/import_textbook.py`, `curriculum-validator/validate.py`, `problem-benchmark/benchmark.py`.

## Commands (Git Bash paths; PowerShell equivalents in docs/build-and-release.md)
```
services/math-engine/.venv/Scripts/python -X utf8 -m pytest -q          # (cwd services/math-engine) 187 tests
services/math-engine/.venv/Scripts/python -X utf8 tools/curriculum-validator/validate.py subjects/calculus --write
services/math-engine/.venv/Scripts/python -X utf8 tools/problem-benchmark/benchmark.py 120 docs/reports/benchmark-report.json
cd apps/desktop && npx tsc --noEmit && npx vitest run
cd apps/desktop/src-tauri && ~/.cargo/bin/cargo test
cd apps/desktop && PATH="$HOME/.cargo/bin:$PATH" npx tauri build        # needs build/math-engine/unilearn-math (PyInstaller)
powershell -File scripts/build-release.ps1                              # everything, incl. checksums
```
Python scripts that read untrusted files use `-I`; use `-X utf8` for Thai output on this console.

## Rules for future work
* New problem families: independent `verify` reference + step `check`s; the regression test covers every family
  automatically. Re-run the validator and benchmark; never hand-edit generated reports.
* Lessons stay `machine-validated` until a human reviews them; never mark `reviewed`/`published` automatically.
* Original Thai wording only — do not copy textbook passages, figures, or exercise banks.
* Claude CLI stays optional: no learning/grading/visualization path may depend on it.
* The webview has only `core:default`; add native features as typed Rust commands with input validation.
* `git` is not initialised in this folder (user has not asked for commits).
