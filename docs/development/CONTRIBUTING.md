# Developer guide

## Layout

```
apps/desktop/            React + TS UI (src/), Tauri 2 shell (src-tauri/), vitest tests (tests/)
packages/                visualization-core · assessment-core · curriculum-core (TS, imported via Vite aliases)
services/math-engine/    Python engine (unilearn_math/), pytest suite (tests/), engine_main.py (PyInstaller entry)
subjects/<id>/           content packages: manifest.json, lessons/*.json, curriculum/
tools/                   textbook-importer · curriculum-validator · problem-benchmark
scripts/                 build-release.ps1
docs/                    architecture, requirements, coverage (generated), problem engine, testing, release, status
```

## Run in development

```powershell
cd apps\desktop; npm ci; $env:PATH="$env:USERPROFILE\.cargo\bin;$env:PATH"; npx tauri dev
```

UI-only work in a browser: start the engine bridge `services\math-engine\.venv\Scripts\python -X utf8 -m unilearn_math.server --http 8765`
(binds 127.0.0.1 only) and `npm run dev` in `apps/desktop`; the UI uses localStorage instead of SQLite in this mode.

## Adding a problem family

1. Add a generator in `unilearn_math/families/chN.py` decorated with `@template(...)` — declare every sampled
   parameter in `params`, the learning objective ids it practices, answer type, visualization type.
2. Provide an **independent** `verify` reference (don't reuse your own answer expression), and give every
   transformation step a `check` where one exists.
3. Run `pytest` (the regression test automatically covers every registered family) and the benchmark.
4. Re-run the curriculum validator so the coverage report picks up the new objectives.

## Adding a subject

Create `subjects/<id>/manifest.json` (`contentApi: 1`, semver, `completeness`), lessons, and optionally families
with `subject="<id>"`. See `subjects/sample-subject` and `unilearn_math/sample_subject.py`.

## Rules

* Never pass user text to `eval`, `exec`, `sympify` or `parse_expr`; use `safe_parse.parse`.
* Never mark content `reviewed`/`published` without a human academic reviewer.
* Don't report numbers you didn't measure; regenerate `docs/reports/*` instead.
