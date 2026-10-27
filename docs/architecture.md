# Architecture

UniLearn Studio is a local-first Windows desktop app. Three processes, strict boundaries:

```
┌──────────────── WebView2 (React + TS, Vite) ───────────────┐
│ pages/  Dashboard · Subjects · Lessons · Practice · Exam  │
│         Visualizations · Progress · Notes · Tutor · Settings │
│ components/  Tex (KaTeX) · MathInput · Plot2D (SVG) · Viz3D (three.js, lazy) │
│ packages/visualization-core  safe plot-expression compiler + spec validator │
│ packages/assessment-core     mastery model + recommendations │
│ packages/curriculum-core     subject-package registry & validation │
│ subjects/*  content packages bundled at build time          │
└──────────── typed IPC: math_call · db · claude_* · save_export ────────────┘
┌──────────────── Rust (Tauri 2) ─────────────────────────────┐
│ db.rs       SQLite (rusqlite, bundled): migrations, typed DbOp enum, │
│             backups (VACUUM INTO), export/import, corruption recovery │
│ sidecar.rs  owns the math engine process; per-request timeouts;      │
│             kill + restart on timeout/crash; method allowlist        │
│ claude.rs   optional Claude CLI adapter (discovery, stdin prompt,    │
│             no tools, temp cwd, timeout, cancel, error states)       │
│ save_export sanitized writes to Downloads\UniLearn Studio only        │
└──────────── JSON lines over stdio ───────────────────────────┘
┌──────────────── Math engine (Python + SymPy, PyInstaller onedir) ───┐
│ safe_parse.py  restricted grammar → SymPy (no eval/sympify on input) │
│ core.py        Template contract, seeded Rand, Step, registry        │
│ verify.py      pipeline: schema → reference answer → step checks →   │
│                publish/reject; symbolic first, numeric recorded       │
│ answer.py      grading: equivalence, +C handling, error classes      │
│ families/      129 Calculus families (ch5–ch8) · sample_subject.py   │
│ server.py      stdio JSON-lines protocol (+ localhost HTTP dev bridge) │
└──────────────────────────────────────────────────────────────┘
```

## Key decisions

| Decision | Why |
|---|---|
| Problems are regenerated from `(templateId, version, seed, difficulty)`; the client never holds a trusted answer for grading | Reproducibility and tamper-resistance; the DB stores only generation metadata (`problem_instances`). |
| One long-lived sidecar, killed on timeout | SymPy can hang on adversarial input; process isolation is the only reliable timeout in CPython. |
| Restricted parser instead of `sympify` | `sympify`/`parse_expr` use `eval`. Our grammar allowlists names, limits size/depth/exponents. |
| Plot evaluation in TS uses its own compiler of the same grammar | Interactive sliders need per-frame evaluation; it never grades and never executes code. |
| Content bundled at build time and validated on load | Offline-first; packages are data-only (no executable plugins). |
| Typed `DbOp` serde enum instead of SQL from the UI | Typed IPC contract, input validation in Rust, no SQL injection surface. |
| Webview capability = `core:default` only | No shell/fs/http plugins; every native action is an app command with its own validation. |
| Claude prompt via stdin, `--tools ""`, temp cwd | No shell interpolation, no filesystem/command access for the tutor. |

## Multi-subject plugin contract

A subject package is a directory under `subjects/<id>/` with `manifest.json` (id, semver version, `contentApi`,
`requiredEngines`, `capabilities`, `completeness`, chapters) and `lessons/<section>.json`. `curriculum-core/registry.ts`
validates manifests (schema, semver, API compatibility, engine availability) and each lesson; invalid packages are
reported in the Subjects page instead of crashing. Problem families for a subject register in the engine's
`REGISTRY` with `subject=<id>` (see `sample_subject.py`). Third-party executable plugins are deliberately **not**
supported (no sandbox/trust model yet).

## Data model (SQLite)

`profiles, settings, kv, content_versions, lesson_progress, notes, bookmarks, problem_instances, attempts, exams,
mastery_history, study_sessions, ai_conversations, schema_migrations` — foreign keys on, WAL, indexed by
`(profile_id, section, at)`. Daily backup + pre-import backup (7 kept). Corrupt DB files are moved aside on open.
Note: lessons/templates live in versioned content packages and the engine registry rather than DB tables; the DB
stores user state plus reproducible references.
