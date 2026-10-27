"""Grade untrusted student answers against a regenerated (trusted) problem instance."""
from __future__ import annotations

import sympy as sp

from .safe_parse import MathInputError, parse, C
from .verify import DIVERGES, d_dx, equal

DIVERGE_WORDS = {"diverges", "diverge", "divergent", "ลู่ออก", "dne", "divergence"}
CONVERGE_WORDS = {"converges", "converge", "convergent", "ลู่เข้า"}


def _classify(user, ref, var, domain) -> str | None:
    """Recognise common error patterns (deterministic, explainable)."""
    try:
        if equal(user, -ref, var, domain)[0] is not False:
            return "sign_error"
        ratio = sp.simplify(user / ref)
        if ratio.is_number and ratio != 1:
            return "coefficient_error"
        if (user - ref).is_number:
            return "constant_offset"
    except Exception:
        pass
    return None


ERROR_TH = {
    "sign_error": "คำตอบมีเครื่องหมายตรงข้ามกับคำตอบที่ถูกต้อง ตรวจเครื่องหมายลบในแต่ละขั้นอีกครั้ง",
    "coefficient_error": "รูปแบบถูกแล้ว แต่ค่าสัมประสิทธิ์ (ตัวคูณคงที่) ไม่ถูกต้อง",
    "constant_offset": "ต่างจากคำตอบด้วยค่าคงที่ ตรวจการแทนค่าขอบเขตหรือค่าคงที่อีกครั้ง",
    "differentiated_instead": "ดูเหมือนจะหาอนุพันธ์แทนการหาปฏิยานุพันธ์ (antiderivative)",
    "missing_constant": "ถูกต้อง แต่อย่าลืมเขียน + C สำหรับอินทิกรัลไม่จำกัดเขต",
}


def check(problem: dict, text: str) -> dict:
    b = problem["_built"]
    var = b.var
    ans_type = b.answer_type
    raw = (text or "").strip()
    norm = raw.lower()

    if ans_type == "choice":
        ok = raw == b.answer
        return {"correct": ok, "method": "exact", "feedback": None if ok else "ยังไม่ถูกต้อง ลองทบทวนเงื่อนไขของโจทย์"}

    if ans_type == "improper" and (norm in DIVERGE_WORDS or norm in CONVERGE_WORDS):
        if norm in CONVERGE_WORDS:
            return {"correct": False, "method": "exact", "feedback": "ถ้าอินทิกรัลลู่เข้า ให้ใส่ค่าของอินทิกรัล"}
        ok = b.answer == DIVERGES
        return {"correct": ok, "method": "exact", "feedback": None if ok else "อินทิกรัลนี้ลู่เข้า ลองคำนวณลิมิตอีกครั้ง"}

    try:
        user = parse(raw)
    except MathInputError as e:
        return {"correct": False, "parseError": e.message_th, "method": "parse"}

    allowed = {var, C}
    extra = user.free_symbols - allowed
    if extra:
        return {"correct": False, "parseError": f"มีตัวแปรที่ไม่เกี่ยวข้อง: {', '.join(map(str, extra))}", "method": "parse"}

    if ans_type == "antiderivative":
        has_c = C in user.free_symbols
        u0 = user.subs(C, 0)
        integrand = b.verify[1]
        ok, method = equal(d_dx(u0, var, b.domain), integrand, var, b.domain)
        if ok is not False:
            return {"correct": True, "method": method, "feedback": None if has_c else ERROR_TH["missing_constant"],
                    "missingConstant": not has_c}
        err = None
        if equal(u0, integrand, var, b.domain)[0] is not False or equal(u0, sp.diff(integrand, var), var, b.domain)[0] is not False:
            err = "differentiated_instead"
        else:
            err = _classify(d_dx(u0, var, b.domain), integrand, var, b.domain)
        return {"correct": False, "method": method, "errorType": err, "feedback": ERROR_TH.get(err, "ยังไม่ถูกต้อง ลองตรวจสอบโดยหาอนุพันธ์ของคำตอบ")}

    if isinstance(b.answer, str):  # improper integral that diverges, student typed a number
        return {"correct": False, "method": "exact", "feedback": "อินทิกรัลนี้ลู่ออก (diverges) ลองตรวจลิมิตอีกครั้ง"}
    if user.has(C):
        return {"correct": False, "parseError": "โจทย์นี้ไม่ต้องมีค่าคงที่ C", "method": "parse"}
    ok, method = equal(user, b.answer, var, b.domain)
    if ok is not False:
        return {"correct": True, "method": method}
    err = _classify(user, b.answer, var, b.domain)
    return {"correct": False, "method": method, "errorType": err, "feedback": ERROR_TH.get(err, "ยังไม่ถูกต้อง ลองดูคำใบ้หรือขั้นตอนถัดไป")}
