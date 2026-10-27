"""Deterministic textbook ingestion: metadata, TOC parsing, printed-page -> PDF-index mapping.

Usage:
    python -I import_textbook.py <pdf> <out_dir> [--sections 5.1,5.2,...]

Outputs (in out_dir):
    source-record.json     filename, sha256, page count, PDF metadata, identification evidence
    toc.json               every "N.M Title page" entry parsed from the printed contents pages
    curriculum-map.json    required sections with printed page, verified PDF index, evidence, status

Nothing is guessed silently: a section whose PDF page cannot be confirmed is marked
"needs_manual_review" with the reason.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import pymupdf

REQUIRED = ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "6.1", "6.2", "6.3", "6.4",
            "7.1", "7.2", "7.3", "7.5", "8.1", "8.2", "8.3", "8.4", "8.5", "8.8"]

TOC_LINE = re.compile(r"^(\d{1,2})\.(\d{1,2})\s*$")
PAGE_NUM = re.compile(r"^(.*?)\s+(\d{1,4})\s*$")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("�", "'")).strip()


def find_contents_pages(doc: pymupdf.Document, scan: int = 30) -> list[int]:
    pages = []
    for i in range(min(scan, doc.page_count)):
        t = doc[i].get_text()
        if re.search(r"^\s*(Contents|iii)\s*$", t, re.M) and len(re.findall(r"^\d{1,2}\.\d{1,2}\s*$", t, re.M)) >= 3:
            pages.append(i)
    return pages


def parse_toc(doc: pymupdf.Document, pages: list[int]) -> list[dict]:
    """Contents lines come as: '5.1' / 'Area and Estimating with Finite Sums 284'."""
    entries = []
    for p in pages:
        lines = [clean(l) for l in doc[p].get_text().splitlines()]
        lines = [l for l in lines if l]
        for i, line in enumerate(lines):
            m = TOC_LINE.match(line)
            if not m or i + 1 >= len(lines):
                continue
            nxt = lines[i + 1]
            # title may wrap onto the following line before the page number
            mm = PAGE_NUM.match(nxt) or (PAGE_NUM.match(nxt + " " + lines[i + 2]) if i + 2 < len(lines) else None)
            if mm:
                entries.append({"section": f"{m.group(1)}.{m.group(2)}", "title": mm.group(1).strip(),
                                "printed_page": int(mm.group(2)), "contents_pdf_index": p})
    seen, out = set(), []
    for e in entries:
        if e["section"] not in seen:
            seen.add(e["section"]); out.append(e)
    return out


def page_has_header(doc: pymupdf.Document, idx: int, printed: int) -> bool:
    lines = [clean(l) for l in doc[idx].get_text().splitlines()[:6] + doc[idx].get_text().splitlines()[-4:]]
    return str(printed) in lines or any(l.startswith(f"{printed} ") or l.endswith(f" {printed}") for l in lines)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9.]+", " ", clean(s).lower()).strip()


def locate(doc: pymupdf.Document, entry: dict, skip: set[int]) -> dict:
    """Find the PDF index whose header/footer carries the printed page number, then confirm
    the section heading text occurs on that page (sections often begin mid-page)."""
    sec, title, printed = entry["section"], entry["title"], entry["printed_page"]
    key = norm(f"{sec} {title}")[:28]
    rec = {**entry, "pdf_index": None, "pdf_page_number": None, "offset": None, "evidence": [], "status": "needs_manual_review"}
    for i in range(printed, min(doc.page_count, printed + 80)):
        if i in skip or not page_has_header(doc, i, printed):
            continue
        rec.update(pdf_index=i, pdf_page_number=i + 1, offset=i - printed)
        rec["evidence"].append(f"printed page number {printed} found in header/footer of PDF index {i}")
        if key in norm(doc[i].get_text()):
            rec["status"] = "verified"
            rec["evidence"].append(f"section heading '{sec} {title[:30]}' found in page body")
        else:
            rec["status"] = "page_only"
            rec["evidence"].append("heading text not matched on page; manual review")
        return rec
    rec["evidence"].append("no page carries the printed page number in its header/footer")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("out_dir")
    ap.add_argument("--sections", default=",".join(REQUIRED))
    a = ap.parse_args()
    pdf, out = Path(a.pdf), Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf)

    first = clean(" ".join(doc[i].get_text() for i in range(min(4, doc.page_count))))
    ident = {
        "title_match": "CALCULUS" in first.upper() and "THOMAS" in first.upper(),
        "edition_match": "FOURTEENTH EDITION" in first.upper(),
        "authors_found": [n for n in ["THOMAS", "HASS", "HEIL", "WEIR"] if n in first.upper()],
    }
    isbn = sorted(set(re.findall(r"ISBN[- ]?(?:1[03])?:?\s*([\d-]{10,17})", clean(" ".join(doc[i].get_text() for i in range(min(6, doc.page_count)))))))
    source = {"filename": pdf.name, "sha256": sha256(pdf), "bytes": pdf.stat().st_size, "page_count": doc.page_count,
              "pdf_metadata": {k: v for k, v in doc.metadata.items() if v}, "isbn": isbn, "identification": ident,
              "book": "Thomas' Calculus, 14th Edition (Thomas, Hass, Heil, Weir)"}

    cpages = find_contents_pages(doc)
    toc = parse_toc(doc, cpages)
    (out / "toc.json").write_text(json.dumps({"contents_pdf_indices": cpages, "entries": toc}, indent=2, ensure_ascii=False), "utf-8")

    by = {e["section"]: e for e in toc}
    wanted = a.sections.split(",")
    results = []
    for s in wanted:
        if s not in by:
            results.append({"section": s, "status": "missing_from_toc", "evidence": ["not found in contents pages"]}); continue
        r = locate(doc, by[s], set(cpages))
        # end page = page before next TOC entry's start
        nxt = next((e for e in toc if toc.index(e) == toc.index(by[s]) + 1), None)
        r["printed_end_page"] = nxt["printed_page"] - 1 if nxt else None
        results.append(r)
    source["contents_pdf_indices"] = cpages
    (out / "source-record.json").write_text(json.dumps(source, indent=2, ensure_ascii=False), "utf-8")
    (out / "curriculum-map.json").write_text(json.dumps({"source_sha256": source["sha256"], "sections": results}, indent=2, ensure_ascii=False), "utf-8")
    bad = [r["section"] for r in results if r["status"] != "verified"]
    print(f"toc entries: {len(toc)}; required: {len(wanted)}; verified: {len(wanted) - len(bad)}; review: {bad}")
    return 0 if not bad else 2


if __name__ == "__main__":
    sys.exit(main())
