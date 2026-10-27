"""Math-engine sidecar.

Protocol: one JSON object per line on stdin -> one JSON object per line on stdout.
    request : {"id": <int|str>, "method": <str>, "params": {...}}
    response: {"id": ..., "ok": true, "result": ...} | {"id": ..., "ok": false, "error": {"code", "message"}}

The desktop shell (Rust) owns this process: it enforces per-request timeouts by killing and
restarting the process, so a pathological expression can never hang the UI.

`--http PORT` starts a 127.0.0.1-only HTTP bridge (POST /rpc) used for browser development.
"""
from __future__ import annotations

import json
import random
import sys
import traceback
from collections import OrderedDict

from . import __version__
from . import families  # noqa: F401  (registers templates)
from . import sample_subject  # noqa: F401
from .answer import check
from .core import REGISTRY, RULE_ENGINE_VERSION
from .safe_parse import MathInputError, parse
from .verify import generate, public
from .core import L

_CACHE: OrderedDict = OrderedDict()
CACHE_MAX = 512


def _get(tid: str, seed: int, difficulty: int) -> dict:
    key = (tid, int(seed), int(difficulty))
    if key in _CACHE:
        _CACHE.move_to_end(key)
        return _CACHE[key]
    p = generate(tid, int(seed), int(difficulty))
    _CACHE[key] = p
    if len(_CACHE) > CACHE_MAX:
        _CACHE.popitem(last=False)
    return p


def _templates(subject: str | None = None, section: str | None = None) -> list:
    return [t for t in REGISTRY.values() if (subject is None or t.subject == subject) and (section is None or t.section_id == section)]


def m_ping(_):
    return {"engine": __version__, "rules": RULE_ENGINE_VERSION, "templates": len(REGISTRY)}


def m_list_templates(p):
    return [t.meta() for t in _templates(p.get("subject"), p.get("section"))]


def m_generate(p):
    return public(_get(p["templateId"], p.get("seed", 0), p.get("difficulty", 2)))


def m_generate_for_section(p):
    """Pick a family for the section deterministically from the seed, skipping excluded canonicals."""
    tpls = _templates(p.get("subject"), p["section"])
    if p.get("templateIds"):
        tpls = [t for t in tpls if t.id in set(p["templateIds"])]
    if not tpls:
        raise KeyError(f"no templates for section {p['section']}")
    rng = random.Random(f"{p['section']}|{p.get('seed', 0)}")
    exclude = set(p.get("excludeCanonical", []))
    for _ in range(30):
        t = rng.choice(tpls)
        seed = rng.randrange(10**6)
        prob = _get(t.id, seed, p.get("difficulty", 2))
        if prob["canonical"] not in exclude:
            return public(prob)
    return public(prob)


def m_check(p):
    prob = _get(p["templateId"], p["seed"], p["difficulty"])
    res = check(prob, p.get("answer", ""))
    res["problemId"] = prob["id"]
    return res


def m_reveal(p):
    """Answer + full solution of a problem (the UI requests it only on explicit reveal)."""
    prob = _get(p["templateId"], p["seed"], p["difficulty"])
    return {"answerTex": prob["answerTex"], "steps": prob["steps"]}


def m_preview(p):
    try:
        e = parse(p.get("text", ""))
        return {"ok": True, "latex": L(e)}
    except MathInputError as e:
        return {"ok": False, "error": e.message_th}


def m_exam(p):
    """Build an exam: round-robin over sections, deterministic in seed, no duplicate canonicals."""
    sections = p["sections"]
    count = int(p.get("count", 10))
    if not 1 <= count <= 60:
        raise ValueError("count must be 1..60")
    rng = random.Random(f"exam|{p.get('seed', 0)}|{','.join(sections)}")
    exclude = set(p.get("excludeCanonical", []))
    out, seen = [], set()
    i = 0
    while len(out) < count and i < count * 20:
        sec = sections[i % len(sections)]
        i += 1
        tpls = [t for t in _templates(p.get("subject", "calculus"), sec) if p.get("includeChoice", True) or t.answer_type != "choice"]
        if not tpls:
            continue
        t = rng.choice(tpls)
        d = p.get("difficulty") or rng.choice(list(t.difficulties))
        prob = _get(t.id, rng.randrange(10**6), d)
        if prob["canonical"] in seen or prob["canonical"] in exclude:
            continue
        seen.add(prob["canonical"])
        q = public(prob)
        q.pop("steps"); q.pop("answerTex"); q.pop("hints")
        out.append(q)
    return out


def m_coverage(_):
    secs = {}
    for t in REGISTRY.values():
        s = secs.setdefault(f"{t.subject}:{t.section_id}", {"subject": t.subject, "section": t.section_id, "families": 0, "objectives": set(),
                                                          "visualizations": set(), "answerTypes": set()})
        s["families"] += 1
        s["objectives"].update(t.objectives)
        if t.visualization:
            s["visualizations"].add(t.visualization)
        s["answerTypes"].add(t.answer_type)
    return [{**v, "objectives": sorted(v["objectives"]), "visualizations": sorted(v["visualizations"]), "answerTypes": sorted(v["answerTypes"])}
            for v in secs.values()]


METHODS = {"ping": m_ping, "list_templates": m_list_templates, "generate": m_generate, "generate_for_section": m_generate_for_section,
           "check": m_check, "reveal": m_reveal, "preview": m_preview, "exam": m_exam, "coverage": m_coverage}


def handle(req: dict) -> dict:
    rid = req.get("id")
    try:
        fn = METHODS.get(req.get("method"))
        if fn is None:
            return {"id": rid, "ok": False, "error": {"code": "unknown_method", "message": str(req.get("method"))}}
        params = req.get("params") or {}
        if not isinstance(params, dict):
            raise ValueError("params must be an object")
        return {"id": rid, "ok": True, "result": fn(params)}
    except (KeyError, ValueError, TypeError) as e:
        return {"id": rid, "ok": False, "error": {"code": "bad_request", "message": str(e)}}
    except Exception as e:  # noqa: BLE001
        traceback.print_exc(file=sys.stderr)
        return {"id": rid, "ok": False, "error": {"code": "internal", "message": f"{type(e).__name__}: {e}"}}


def serve_stdio():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    print(json.dumps({"id": None, "ok": True, "result": {"ready": True, **m_ping({})}}), flush=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if len(line) > 64_000:
            resp = {"id": None, "ok": False, "error": {"code": "too_large", "message": "request too large"}}
        else:
            try:
                resp = handle(json.loads(line))
            except json.JSONDecodeError:
                resp = {"id": None, "ok": False, "error": {"code": "bad_json", "message": "invalid JSON"}}
        print(json.dumps(resp, ensure_ascii=False, default=str), flush=True)


def serve_http(port: int):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(BaseHTTPRequestHandler):
        def _cors(self):
            origin = self.headers.get("Origin", "")
            if origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:"):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Headers", "content-type")
                self.send_header("Vary", "Origin")

        def do_OPTIONS(self):
            self.send_response(204); self._cors(); self.end_headers()

        def do_POST(self):
            if self.path != "/rpc":
                self.send_response(404); self.end_headers(); return
            n = int(self.headers.get("Content-Length", "0"))
            if n > 64_000:
                self.send_response(413); self.end_headers(); return
            try:
                resp = handle(json.loads(self.rfile.read(n)))
            except json.JSONDecodeError:
                resp = {"id": None, "ok": False, "error": {"code": "bad_json", "message": "invalid JSON"}}
            body = json.dumps(resp, ensure_ascii=False, default=str).encode()
            self.send_response(200); self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8"); self.end_headers(); self.wfile.write(body)

        def log_message(self, *a):
            pass

    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--http":
        serve_http(int(sys.argv[2]))
    else:
        serve_stdio()


if __name__ == "__main__":
    main()
