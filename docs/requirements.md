# Requirements (condensed from the master specification v1.0)

The full specification was supplied in chat (it is not stored as `MASTER_PROMPT.md` in the repo). Binding requirements:

1. **Offline-first.** Lessons, problem generation, grading, step solutions, visualizations, progress and exams work with no network.
2. **Deterministic, verified problems.** No AI per question; every instance reproducible from template id + version + seed + difficulty (+ rule version) and verified symbolically (numeric only as a labelled fallback).
3. **Structured step solutions** (rule, Thai explanation, before/after, assumptions, verification), revealable one at a time, with hints and comparison to the student's attempt.
4. **Initial scope:** the 20 exam sections 5.1–5.6, 6.1–6.4, 7.1–7.3, 7.5, 8.1–8.5, 8.8 of *Thomas' Calculus* 14e, Thai explanations with English terms, three explanation depths, original wording (no reproduction of copyrighted text/figures), verified page references.
5. **Targets:** ≥5 families/section, ≥100 families, ≥10,000 unique reproducible instances — counted honestly after canonical de-duplication.
6. **Multi-subject plugin contract** (data-driven, versioned, validated; no untrusted executable plugins) + a small, clearly-labelled second-subject example.
7. **Security:** restricted math grammar, no eval, size/complexity limits, process timeouts, typed IPC, minimal Tauri capabilities, path-safe exports, untrusted AI/textbook data.
8. **Optional Claude CLI tutor:** discovery, availability states, non-interactive JSON, timeout/cancel, no tools, minimal consented context, AI output marked unverified, never replaces verified answers.
9. **Windows 10/11 x64 installer** bundling the math runtime; no Python/Node/Rust needed by students; persistent user data dir; checksums.
10. **Honest reporting:** nothing marked complete, tested or validated unless it was.

Modes: Learn, Guided Practice, Free Practice, Exam Simulation, Weakness Review, Interactive Visualization, optional AI Tutor.
