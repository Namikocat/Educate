"""Restricted mathematical grammar for untrusted input.

Never uses eval/exec/sympify on user text. A hand-written tokenizer and recursive-descent
parser build SymPy objects only from an allowlist of functions, constants and variables,
with hard limits on length, token count, nesting depth and exponent size.

Grammar (precedence low -> high):
    expr   := term (('+' | '-') term)*
    term   := unary (('*' | '/') unary | <implicit> unary)*
    unary  := ('+' | '-') unary | power
    power  := atom ('^' unary)?            right-associative
    atom   := NUMBER | NAME | FUNC call | '(' expr ')' | '|' expr '|'
    call   := FUNC ['^' atom] ( '(' args ')' | power )
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import sympy as sp

MAX_CHARS = 400
MAX_TOKENS = 250
MAX_DEPTH = 40
MAX_INT_EXPONENT = 200
MAX_NUMBER_DIGITS = 30


class MathInputError(ValueError):
    """Input rejected by the restricted grammar. `message_th` is shown to students."""

    def __init__(self, message: str, message_th: str | None = None):
        super().__init__(message)
        self.message_th = message_th or message


x, y, t, u, v, k, n, theta, C = sp.symbols("x y t u v k n theta C")

VARIABLES = {"x": x, "y": y, "t": t, "u": u, "v": v, "k": k, "n": n, "theta": theta, "C": C}
CONSTANTS = {"pi": sp.pi, "e": sp.E, "E": sp.E, "oo": sp.oo, "inf": sp.oo, "infinity": sp.oo}


def _log(*args):
    if len(args) == 1:
        return sp.log(args[0])
    if len(args) == 2:  # log(base, value)
        return sp.log(args[1], args[0])
    raise MathInputError("log takes 1 or 2 arguments", "log รับอาร์กิวเมนต์ 1 หรือ 2 ตัว")


FUNCTIONS = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "sec": sp.sec, "csc": sp.csc, "cot": sp.cot,
    "arcsin": sp.asin, "asin": sp.asin, "arccos": sp.acos, "acos": sp.acos,
    "arctan": sp.atan, "atan": sp.atan, "arcsec": sp.asec, "asec": sp.asec,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "ln": sp.log, "log": _log, "exp": sp.exp, "sqrt": sp.sqrt, "abs": sp.Abs, "Abs": sp.Abs,
}
ARITY = {"log": (1, 2)}

_NAMES = sorted(list(VARIABLES) + list(CONSTANTS) + list(FUNCTIONS), key=len, reverse=True)

UNICODE = {"π": "pi", "∞": "oo", "θ": "theta", "√": "sqrt", "·": "*", "×": "*", "−": "-", "–": "-",
           "÷": "/", "²": "^2", "³": "^3", "⁻¹": "^(-1)", "**": "^", " ": " "}

_TOKEN = re.compile(r"\s*(?:(\d+(?:\.\d+)?|\.\d+)|([A-Za-z]+)|(\^|[-+*/(),|]))")


@dataclass
class Tok:
    kind: str  # num, name, func, op
    text: str


def tokenize(src: str) -> list[Tok]:
    if len(src) > MAX_CHARS:
        raise MathInputError("input too long", f"คำตอบยาวเกิน {MAX_CHARS} ตัวอักษร")
    for a, b in UNICODE.items():
        src = src.replace(a, b)
    out: list[Tok] = []
    pos = 0
    src = src.strip()
    while pos < len(src):
        m = _TOKEN.match(src, pos)
        if not m or m.end() == pos:
            raise MathInputError(f"unexpected character {src[pos]!r}", f"มีอักขระที่ไม่รองรับ: '{src[pos]}'")
        pos = m.end()
        num, word, op = m.groups()
        if num:
            if len(num.replace(".", "")) > MAX_NUMBER_DIGITS:
                raise MathInputError("number too long", "ตัวเลขยาวเกินไป")
            out.append(Tok("num", num))
        elif word:
            out.extend(_split_word(word))
        elif op:
            out.append(Tok("op", op))
        if len(out) > MAX_TOKENS:
            raise MathInputError("expression too complex", "นิพจน์ซับซ้อนเกินไป")
    return out


def _split_word(word: str) -> list[Tok]:
    """Split letter runs into allowlisted names greedily: 'xsinx' -> x, sin, x."""
    toks, i = [], 0
    while i < len(word):
        for name in _NAMES:
            if word.startswith(name, i):
                toks.append(Tok("func" if name in FUNCTIONS else "name", name))
                i += len(name)
                break
        else:
            raise MathInputError(f"unknown name in {word!r}", f"ไม่รู้จักชื่อ '{word}' (ใช้ได้เช่น x, sin, ln, sqrt, pi, e)")
    return toks


class _Parser:
    def __init__(self, toks: list[Tok]):
        self.t, self.i, self.depth, self.abs_depth = toks, 0, 0, 0

    def peek(self) -> Tok | None:
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self, text: str | None = None) -> Tok:
        tok = self.peek()
        if tok is None or (text is not None and tok.text != text):
            want = text or "more input"
            raise MathInputError(f"expected {want}", "รูปแบบนิพจน์ไม่สมบูรณ์ (ตรวจวงเล็บหรือเครื่องหมาย)")
        self.i += 1
        return tok

    def enter(self):
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise MathInputError("nesting too deep", "ซ้อนวงเล็บลึกเกินไป")

    def leave(self):
        self.depth -= 1

    def expr(self):
        self.enter()
        val = self.term()
        while (tok := self.peek()) and tok.text in "+-" and tok.kind == "op":
            self.i += 1
            rhs = self.term()
            val = val + rhs if tok.text == "+" else val - rhs
        self.leave()
        return val

    def _starts_atom(self, tok: Tok | None) -> bool:
        if tok is None:
            return False
        if tok.kind in ("num", "name", "func"):
            return True
        if tok.text == "(":
            return True
        return tok.text == "|" and self.abs_depth == 0

    def term(self):
        val = self.unary()
        while True:
            tok = self.peek()
            if tok and tok.kind == "op" and tok.text in "*/":
                self.i += 1
                rhs = self.unary()
                if tok.text == "*":
                    val = val * rhs
                else:
                    if rhs == 0:
                        raise MathInputError("division by zero", "หารด้วยศูนย์")
                    val = val / rhs
            elif self._starts_atom(tok):
                val = val * self.power()
            else:
                return val

    def unary(self):
        tok = self.peek()
        if tok and tok.kind == "op" and tok.text in "+-":
            self.i += 1
            self.enter()
            v = self.unary()
            self.leave()
            return -v if tok.text == "-" else v
        return self.power()

    def power(self):
        base = self.atom()
        tok = self.peek()
        if tok and tok.text == "^":
            self.i += 1
            self.enter()
            ex = self.unary()
            self.leave()
            return _safe_pow(base, ex)
        return base

    def atom(self):
        tok = self.take()
        if tok.kind == "num":
            return sp.Rational(tok.text)
        if tok.kind == "name":
            return VARIABLES.get(tok.text, CONSTANTS.get(tok.text))
        if tok.kind == "func":
            return self.call(tok.text)
        if tok.text == "(":
            val = self.expr()
            self.take(")")
            return val
        if tok.text == "|":
            self.abs_depth += 1
            val = self.expr()
            self.take("|")
            self.abs_depth -= 1
            return sp.Abs(val)
        raise MathInputError(f"unexpected {tok.text!r}", f"ไม่คาดว่าจะพบ '{tok.text}' ตรงนี้")

    def call(self, name: str):
        fn = FUNCTIONS[name]
        exponent = None
        if (tok := self.peek()) and tok.text == "^":  # sin^2(x)
            self.i += 1
            exponent = self.atom() if self.peek() and self.peek().text != "-" else self.unary()
        self.enter()
        if (tok := self.peek()) and tok.text == "(":
            self.i += 1
            args = [self.expr()]
            while (tok := self.peek()) and tok.text == ",":
                self.i += 1
                args.append(self.expr())
            self.take(")")
        else:  # sin x, ln x^2
            args = [self.power()]
        self.leave()
        lo, hi = ARITY.get(name, (1, 1))
        if not lo <= len(args) <= hi:
            raise MathInputError(f"{name} arity", f"ฟังก์ชัน {name} ใช้อาร์กิวเมนต์ไม่ถูกจำนวน")
        val = fn(*args)
        return _safe_pow(val, exponent) if exponent is not None else val


def _safe_pow(base, ex):
    if ex.is_Number and abs(ex) > MAX_INT_EXPONENT:
        raise MathInputError("exponent too large", "เลขชี้กำลังใหญ่เกินไป")
    if base.is_Number and ex.is_Number and abs(base) > 10**6 and abs(ex) > 4:
        raise MathInputError("number too large", "ผลลัพธ์ใหญ่เกินไป")
    if base == 0 and ex.is_Number and ex.is_negative:
        raise MathInputError("0 to negative power", "0 ยกกำลังลบไม่นิยาม")
    return sp.Pow(base, ex)


def parse(src: str) -> sp.Expr:
    """Parse untrusted text into a SymPy expression using the restricted grammar."""
    if not isinstance(src, str) or not src.strip():
        raise MathInputError("empty input", "กรุณาใส่คำตอบ")
    toks = tokenize(src)
    p = _Parser(toks)
    val = p.expr()
    if p.peek() is not None:
        raise MathInputError(f"unexpected {p.peek().text!r}", f"มีส่วนเกินที่อ่านไม่ได้: '{p.peek().text}'")
    if sp.count_ops(val) > 400:
        raise MathInputError("expression too complex", "นิพจน์ซับซ้อนเกินไป")
    return val
