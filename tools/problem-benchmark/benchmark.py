"""Generate many seeded instances per family; report unique (canonical, de-duplicated) instances,
failures and timing. Usage: python benchmark.py [seeds_per_difficulty] [out.json] [prefix]"""
from __future__ import annotations

import json
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "math-engine"))

from unilearn_math import families  # noqa: E402,F401
from unilearn_math.core import REGISTRY  # noqa: E402
from unilearn_math.verify import generate  # noqa: E402


def main() -> int:
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("benchmark-report.json")
    prefix = sys.argv[3] if len(sys.argv) > 3 else ""
    per_family, per_section, failures, times = {}, defaultdict(lambda: {"families": 0, "unique": 0}), [], []
    for tid, tpl in REGISTRY.items():
        if not tid.startswith(prefix):
            continue
        keys, n, verif = set(), 0, defaultdict(int)
        for dlev in tpl.difficulties:
            for s in range(seeds):
                t0 = time.perf_counter()
                try:
                    p = generate(tid, s, dlev)
                except Exception as e:  # recorded, never hidden
                    failures.append({"template": tid, "seed": s, "difficulty": dlev, "error": f"{type(e).__name__}: {str(e)[:200]}"})
                    continue
                times.append(time.perf_counter() - t0)
                keys.add(p["canonical"])
                verif[p["verification"]["answer"]] += 1
                n += 1
        per_family[tid] = {"section": tpl.section_id, "generated": n, "unique": len(keys), "answerVerification": dict(verif)}
        per_section[tpl.section_id]["families"] += 1
        per_section[tpl.section_id]["unique"] += len(keys)
        print(f"{tid:48s} gen={n:4d} unique={len(keys):4d} {dict(verif)}", flush=True)
    report = {
        "seedsPerDifficulty": seeds, "families": len(per_family), "uniqueInstances": sum(f["unique"] for f in per_family.values()),
        "generated": sum(f["generated"] for f in per_family.values()), "failures": failures,
        "timing": {"meanMs": round(1000 * statistics.mean(times), 1) if times else None,
                   "p95Ms": round(1000 * sorted(times)[int(0.95 * len(times))], 1) if times else None,
                   "maxMs": round(1000 * max(times), 1) if times else None},
        "sections": dict(sorted(per_section.items())), "perFamily": per_family,
    }
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), "utf-8")
    print(f"families={report['families']} unique={report['uniqueInstances']} failures={len(failures)} timing={report['timing']}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
