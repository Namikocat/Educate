# Implementation status — 2026-10-26

## Source material
* Textbook: `textbooks/incoming/thomas-calculus-14e.pdf` (copied from Downloads; 3 copies there had different hashes but identical 1,212 pages; the un-numbered one was used), SHA-256 `acc49c2c…574c`.
* All 20 required sections located and **verified** (printed page found in header + heading text on the page). PDF index = printed page + 18 for every section. See `subjects/calculus/curriculum/source/curriculum-map.json`.

## Done and verified
| Area | State | Evidence |
|---|---|---|
| Textbook importer (metadata, TOC, page mapping) | done | 60 TOC entries, 20/20 verified |
| Math engine: restricted parser, pipeline, grading, stdio + dev HTTP server | done | pytest 187 passed |
| Problem families | 129 calculus (5–8 per section) + 2 sample | regression test per family |
| Unique instances | **14,047** (target 10,000) | benchmark 45,840 generations, 0 failures |
| Lessons | 20/20, Thai, 3 depths, 58/58 worked examples verified with SymPy | `docs/curriculum-coverage.md` |
| Objective coverage by generated practice | 99/106 | gaps listed in coverage doc |
| React UI: all 11 pages, practice/guided/weak modes, exams with timer + autosave, progress, notes, bookmarks, search, shortcuts, themes, focus mode | done | tsc clean, vitest 8 passed, browser E2E of 5.5 flow |
| 2D (SVG) + 3D (three.js) visualizations | done | 15 gallery items + per-problem specs |
| Rust shell: SQLite migrations/backup/export/import/corruption handling, sidecar timeouts, Claude adapter, safe export | done | cargo test 6 passed |
| Windows installers | **built**: `release/UniLearn Studio_1.0.0_x64-setup.exe` (30 MB), `…_x64_en-US.msi` (37 MB), `SHA256SUMS.txt` | NSIS installed silently outside the repo, app launched, bundled engine started, DB migrated, uninstall clean |

## 2026-10-27 update
* AI Tutor answers now render as safe Markdown (headings, lists, tables, code, quotes, inline/display math; no raw HTML). Claude is instructed to answer in Markdown.
* Tutor history: saved locally in `ai_conversations` (toggle "บันทึกประวัติไว้ในเครื่อง", default on), searchable sidebar, delete one / clear all, "ถามต่อจากคำตอบนี้" follow-ups (previous answer sent as context). Included in data export.
* Tests: Rust 7 passed, vitest 10 passed, tsc clean. Released as v1.0.1. Rendering checked in the browser with a seeded history entry; a live Claude call from the installed app is still untested.

## Not done / limitations (honest)
* **No human academic review** of any lesson or step text — all `machine-validated`.
* Installed-app UI was not clicked through (no desktop automation available); UI flows were tested in the browser against the same engine.
* Claude tutor: CLI invocation verified manually (`claude -p --output-format json --tools ""`), but not exercised from inside the installed app.
* Math input is a text field with palette + live rendered preview, not MathLive.
* shadcn/ui and TanStack Query were not used (own small components; zustand for state).
* Objectives without practice: 5.3.definition, 5.3.integrability, 5.6.symmetry, 6.3.smooth, 6.4.vs_volume, 7.1.reflection, 7.3.exp.
* Some families have tiny parameter spaces (e.g. 6.2 section has only 53 unique instances).
* DB-corruption notice is recorded but not yet shown in the UI; NSIS Thai UI strings untranslated (Tauri warning).
* Installer is unsigned (SmartScreen will warn).
* Answers in ~1.6% of generated problems are verified numerically only (labelled).
* `git` is not initialised.

## Resume
Rebuild everything: `powershell -File scripts/build-release.ps1`.
