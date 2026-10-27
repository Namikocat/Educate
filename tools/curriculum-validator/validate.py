"""Validate a subject content package and generate the coverage manifest + report.

python -I validate.py <subject_dir> [--write]

* Schema checks for every lesson.
* Every worked example with a `verify` block is checked with the restricted parser + SymPy.
* Source page references are injected from curriculum/source/curriculum-map.json (verified pages only).
* Coverage is computed per learning objective: an objective counts as practice-covered only if
  at least one registered problem family declares it.
* Lessons whose examples all verify are marked "machine-validated" (never "reviewed"/"published":
  that requires a human academic reviewer).
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "math-engine"))

import sympy as sp  # noqa: E402

from unilearn_math import families  # noqa: E402,F401
from unilearn_math import sample_subject  # noqa: E402,F401
from unilearn_math.core import REGISTRY  # noqa: E402
from unilearn_math.safe_parse import parse  # noqa: E402
from unilearn_math.verify import d_dx, equal  # noqa: E402

x = sp.Symbol("x")
REQUIRED_KEYS = ["id", "section", "title", "titleEn", "version", "status", "objectives", "prerequisites", "levels",
                 "definitions", "theorems", "formulas", "examples", "misconceptions", "visualizations", "summary", "review"]


def P(s: str):
    return parse(str(s))


def check_example(v: dict) -> tuple[bool, str]:
    kind = v["kind"]
    dom = tuple(v["domain"]) if "domain" in v else None
    if kind == "value":
        ok, m = equal(P(v["expr"]), P(v["answer"]))
    elif kind == "definite":
        ok, m = equal(sp.integrate(P(v["f"]), (x, P(v["a"]), P(v["b"]))), P(v["answer"]))
    elif kind == "antiderivative":
        ok, m = equal(d_dx(P(v["answer"]), x, dom), P(v["f"]), x, dom)
    elif kind == "derivative":
        ok, m = equal(sp.diff(P(v["f"]), x), P(v["answer"]), x, dom)
    elif kind == "limit":
        ok, m = equal(sp.limit(P(v["f"]), x, P(v["at"])), P(v["answer"]))
    elif kind == "improper":
        r = sp.integrate(P(v["f"]), (x, P(v["a"]), P(v["b"])))
        if v["answer"] == "diverges":
            ok, m = (bool(r.has(sp.oo, -sp.oo, sp.zoo, sp.nan)), "symbolic")
        else:
            ok, m = equal(r, P(v["answer"]))
    else:
        return False, f"unknown kind {kind}"
    return ok is not False, m


def main() -> int:
    subj = Path(sys.argv[1])
    write = "--write" in sys.argv
    manifest = json.loads((subj / "manifest.json").read_text("utf-8"))
    cmap_path = subj / "curriculum" / "source" / "curriculum-map.json"
    cmap = {s["section"]: s for s in json.loads(cmap_path.read_text("utf-8"))["sections"]} if cmap_path.exists() else {}
    sections = [s for ch in manifest["chapters"] for s in ch["sections"]]
    tpl_by_sec: dict[str, list] = {}
    for t in REGISTRY.values():
        if t.subject == manifest["id"]:
            tpl_by_sec.setdefault(t.section_id, []).append(t)

    errors, rows = [], []
    for sec in sections:
        f = subj / "lessons" / f"{sec}.json"
        if not f.exists():
            errors.append(f"{sec}: lesson file missing")
            rows.append({"section": sec, "lesson": False})
            continue
        lesson = json.loads(f.read_text("utf-8"))
        miss = [k for k in REQUIRED_KEYS if k not in lesson]
        if miss:
            errors.append(f"{sec}: missing keys {miss}")
        ex_results = []
        for i, ex in enumerate(lesson.get("examples", [])):
            if "verify" not in ex:
                ex_results.append({"example": i, "verified": None, "method": "not-machine-checkable"})
                continue
            try:
                ok, m = check_example(ex["verify"])
            except Exception as e:  # noqa: BLE001
                ok, m = False, f"error: {type(e).__name__}: {e}"
            ex_results.append({"example": i, "verified": ok, "method": m})
            if not ok:
                errors.append(f"{sec}: example {i} ('{ex['title']}') failed verification ({m})")
        src = cmap.get(sec)
        if src and src.get("status") == "verified":
            lesson["source"] = {"printedPages": [src["printed_page"], src["printed_end_page"]], "pdfIndex": src["pdf_index"],
                                "pdfPage": src["pdf_page_number"], "verified": True, "titleInBook": src["title"]}
        objs = [o["id"] for o in lesson.get("objectives", [])]
        tpls = tpl_by_sec.get(sec, [])
        covered = sorted({o for t in tpls for o in t.objectives if o in objs})
        uncovered = [o for o in objs if o not in covered]
        all_ok = all(r["verified"] is not False for r in ex_results) and not miss
        if write:
            lesson["status"] = "machine-validated" if all_ok else "draft"
            lesson["validation"] = {"date": str(date.today()), "examples": ex_results, "humanReview": "pending"}
            f.write_text(json.dumps(lesson, indent=2, ensure_ascii=False) + "\n", "utf-8")
        rows.append({
            "section": sec, "title": lesson.get("titleEn"), "lesson": True, "status": "machine-validated" if all_ok else "draft",
            "examples": len(ex_results), "examplesVerified": sum(1 for r in ex_results if r["verified"]),
            "objectives": len(objs), "objectivesWithPractice": len(covered), "objectivesWithoutPractice": uncovered,
            "families": len(tpls), "familyIds": [t.id for t in tpls],
            "visualizations": sorted({t.visualization for t in tpls if t.visualization} | {v.get("type") for v in lesson.get("visualizations", [])}),
            "sourceVerified": bool(src and src.get("status") == "verified"),
            "printedPages": [src["printed_page"], src["printed_end_page"]] if src else None,
        })

    cov = {"subject": manifest["id"], "version": manifest["version"], "generated": str(date.today()), "sections": rows, "errors": errors,
           "totals": {"sections": len(sections), "lessons": sum(r["lesson"] for r in rows),
                      "machineValidated": sum(r.get("status") == "machine-validated" for r in rows),
                      "families": sum(r.get("families", 0) for r in rows),
                      "objectives": sum(r.get("objectives", 0) for r in rows),
                      "objectivesWithPractice": sum(r.get("objectivesWithPractice", 0) for r in rows),
                      "humanReviewed": 0}}
    (subj / "curriculum" / "coverage-manifest.json").write_text(json.dumps(cov, indent=2, ensure_ascii=False) + "\n", "utf-8")

    md = [f"# Curriculum coverage — {manifest['nameEn']} v{manifest['version']}", "",
          f"_Generated by `tools/curriculum-validator/validate.py` on {cov['generated']}. Do not edit by hand._", "",
          "Status meanings: **machine-validated** = schema OK and every worked example verified symbolically; "
          "**human academic review is pending for all lessons** (no lesson is marked reviewed/published).", "",
          "| Section | Title | Book pp. | Lesson | Examples verified | Families | Objectives with practice | Visualizations |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        pp = f"{r['printedPages'][0]}–{r['printedPages'][1]}" if r.get("printedPages") else "—"
        md.append(f"| {r['section']} | {r.get('title', '')} | {pp} | {r.get('status', 'missing')} | {r.get('examplesVerified', 0)}/{r.get('examples', 0)} | "
                  f"{r.get('families', 0)} | {r.get('objectivesWithPractice', 0)}/{r.get('objectives', 0)} | {', '.join(r.get('visualizations', []))} |")
    t = cov["totals"]
    md += ["", f"**Totals:** {t['lessons']}/{t['sections']} lessons, {t['machineValidated']} machine-validated, {t['families']} problem families, "
           f"{t['objectivesWithPractice']}/{t['objectives']} objectives backed by generated practice, {t['humanReviewed']} human-reviewed.", "",
           "## Objectives without generated practice", ""]
    gaps = [(r["section"], o) for r in rows for o in r.get("objectivesWithoutPractice", [])]
    md += [f"- {s}: `{o}`" for s, o in gaps] or ["- none"]
    md += ["", "## Validation errors", ""] + ([f"- {e}" for e in errors] or ["- none"])
    report = ROOT / "docs" / ("curriculum-coverage.md" if manifest["id"] == "calculus" else f"reports/coverage-{manifest['id']}.md")
    report.write_text("\n".join(md) + "\n", "utf-8")
    print(json.dumps(t), f"errors={len(errors)}")
    for e in errors:
        print("  ", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
