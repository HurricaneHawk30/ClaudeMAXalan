"""Safe evaluator for single-variable algebraic expressions.

Never uses eval/exec/compile on user input: the text is tokenised by hand,
turned into Python syntax, parsed with ``ast.parse`` and walked with a strict
node whitelist.  See docs/ARCHITECTURE.md section 2.4.
"""
from __future__ import annotations

import ast
import math

MAX_CHARS = 200
MAX_NODES = 200
MAX_EXPONENT = 10
POINTS = (-2.3, -1.1, 0.7, 1.9, 3.4, 5.6)

_SUPERSCRIPT = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁻": "-", "⁺": "+",
}
_PI = repr(math.pi)


class ExprError(ValueError):
    """The expression is not a valid, safe algebraic expression."""


# ------------------------------------------------------------ tokeniser

def _tokenise(s: str, var: str) -> list[tuple[str, str]]:
    """Return tokens (kind, text); kinds: NUM VAR PI OP LP RP."""
    toks: list[tuple[str, str]] = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
        elif c in "0123456789" or (c == "." and i + 1 < n and s[i + 1].isdigit()):
            j = i
            seen_dot = False
            while j < n and (s[j] in "0123456789" or (s[j] == "." and not seen_dot)):
                if s[j] == ".":
                    seen_dot = True
                j += 1
            toks.append(("NUM", s[i:j]))
            i = j
        elif c in _SUPERSCRIPT:
            j = i
            digits = ""
            while j < n and s[j] in _SUPERSCRIPT:
                digits += _SUPERSCRIPT[s[j]]
                j += 1
            if not digits.lstrip("+-").isdigit():
                raise ExprError("bad superscript")
            toks.append(("OP", "**"))
            toks.append(("LP", "("))
            toks.append(("NUM", digits))
            toks.append(("RP", ")"))
            i = j
        elif c == "π":
            toks.append(("PI", _PI))
            i += 1
        elif c.isascii() and c.isalpha():
            if s[i:i + 2].lower() == "pi" and var.lower() != "p":
                toks.append(("PI", _PI))
                i += 2
            elif c == var:
                toks.append(("VAR", c))
                i += 1
            else:
                raise ExprError(f"unknown name {c!r}")
        elif c in "+-*/":
            if c == "*" and i + 1 < n and s[i + 1] == "*":
                toks.append(("OP", "**"))
                i += 2
            else:
                toks.append(("OP", c))
                i += 1
        elif c == "^":
            toks.append(("OP", "**"))
            i += 1
        elif c == "−" or c == "–":
            toks.append(("OP", "-"))
            i += 1
        elif c in "×·⋅∙":
            toks.append(("OP", "*"))
            i += 1
        elif c == "÷":
            toks.append(("OP", "/"))
            i += 1
        elif c == "(":
            toks.append(("LP", "("))
            i += 1
        elif c == ")":
            toks.append(("RP", ")"))
            i += 1
        else:
            raise ExprError(f"unexpected character {c!r}")
    return toks


def _preprocess(s: str, var: str) -> str:
    if not isinstance(s, str):
        raise ExprError("expression must be text")
    if len(s) > MAX_CHARS:
        raise ExprError("expression too long")
    if not isinstance(var, str) or len(var) != 1 or not var.isalpha() or not var.isascii():
        raise ExprError("bad variable")
    toks = _tokenise(s, var)
    if not toks:
        raise ExprError("empty expression")
    if len(toks) > 2 * MAX_NODES:
        raise ExprError("expression too complex")
    out: list[str] = []
    prev: str | None = None
    for kind, text in toks:
        if prev is not None:
            implicit = False
            if prev in ("NUM", "VAR", "PI", "RP") and kind in ("VAR", "PI", "LP"):
                implicit = True
            elif prev == "RP" and kind == "NUM":
                implicit = True
            if implicit:
                out.append("*")
        out.append(text)
        prev = kind
    return "".join(out)


# --------------------------------------------------------------- parsing

_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
_UNOPS = (ast.UAdd, ast.USub)


def _check_tree(tree: ast.Expression, var: str) -> None:
    count = 0
    for node in ast.walk(tree):
        count += 1
        if count > MAX_NODES:
            raise ExprError("expression too complex")
        if isinstance(node, (ast.Expression, ast.Load)):
            continue
        if isinstance(node, ast.BinOp):
            if not isinstance(node.op, _BINOPS):
                raise ExprError("operator not allowed")
        elif isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, _UNOPS):
                raise ExprError("operator not allowed")
        elif isinstance(node, _BINOPS + _UNOPS):
            continue
        elif isinstance(node, ast.Constant):
            if type(node.value) not in (int, float):
                raise ExprError("constant not allowed")
        elif isinstance(node, ast.Name):
            if node.id != var:
                raise ExprError(f"unknown name {node.id!r}")
        else:
            raise ExprError(f"{type(node).__name__} not allowed")


def parse(s: str, var: str = "x") -> ast.Expression:
    src = _preprocess(s, var)
    try:
        tree = ast.parse(src, mode="eval")
    except (SyntaxError, ValueError, RecursionError, MemoryError) as e:
        raise ExprError("cannot parse expression") from e
    _check_tree(tree, var)
    # every exponent must be a constant with |e| <= MAX_EXPONENT
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            if _has_name(node.right):
                raise ExprError("exponent must be a constant")
            if abs(_eval(node.right, {}, None)) > MAX_EXPONENT:
                raise ExprError("exponent too large")
    return tree


# ------------------------------------------------------------ evaluation

def _eval(node: ast.AST, env: dict, var: str | None) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body, env, var)
    if isinstance(node, ast.Constant):
        try:
            return float(node.value)
        except OverflowError as e:
            raise ExprError("number too large") from e
    if isinstance(node, ast.Name):
        if node.id in env:
            return float(env[node.id])
        raise ExprError(f"unknown name {node.id!r}")
    if isinstance(node, ast.UnaryOp):
        v = _eval(node.operand, env, var)
        return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.BinOp):
        op = node.op
        if isinstance(op, ast.Pow):
            e = _eval(node.right, {}, None) if not _has_name(node.right) else None
            if e is None:
                raise ExprError("exponent must be a constant")
            if abs(e) > MAX_EXPONENT:
                raise ExprError("exponent too large")
            a = _eval(node.left, env, var)
            try:
                r = a ** e
            except (ZeroDivisionError, OverflowError) as ex:
                raise ExprError("arithmetic error") from ex
            if isinstance(r, complex):
                raise ExprError("complex result")
            return _finite(r)
        a = _eval(node.left, env, var)
        b = _eval(node.right, env, var)
        try:
            if isinstance(op, ast.Add):
                return _finite(a + b)
            if isinstance(op, ast.Sub):
                return _finite(a - b)
            if isinstance(op, ast.Mult):
                return _finite(a * b)
            if isinstance(op, ast.Div):
                return _finite(a / b)
        except (ZeroDivisionError, OverflowError) as ex:
            raise ExprError("arithmetic error") from ex
    raise ExprError("node not allowed")


def _has_name(node: ast.AST) -> bool:
    return any(isinstance(n, ast.Name) for n in ast.walk(node))


def _finite(v: float) -> float:
    if math.isnan(v) or math.isinf(v):
        raise ExprError("arithmetic error")
    return v


def evaluate(tree: ast.Expression, env: dict[str, float]) -> float:
    try:
        return _eval(tree, env, None)
    except RecursionError as e:
        raise ExprError("expression too deep") from e


# ----------------------------------------------------------- equivalence

def _values(tree: ast.Expression, var: str) -> list[float | None]:
    res: list[float | None] = []
    for p in POINTS:
        try:
            res.append(evaluate(tree, {var: p}))
        except ExprError:
            res.append(None)
    return res


def equivalent(a: str, b: str, var: str = "x") -> bool | None:
    try:
        ta, tb = parse(a, var), parse(b, var)
    except ExprError:
        return None
    va, vb = _values(ta, var), _values(tb, var)
    valid = 0
    for x, y in zip(va, vb):
        if x is None or y is None:
            continue
        valid += 1
        if abs(x - y) > 1e-6 * max(1.0, abs(x), abs(y)):
            return False
    return valid >= 3


# ------------------------------------------------------------- structure

def _contains_var(node: ast.AST, var: str) -> bool:
    return any(isinstance(n, ast.Name) and n.id == var for n in ast.walk(node))


def _is_sum_with_var(node: ast.AST, var: str) -> bool:
    return (isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub))
            and _contains_var(node, var))


def is_expanded(s: str, var: str = "x") -> bool:
    tree = parse(s, var)
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Pow)):
            if _is_sum_with_var(node.left, var) or _is_sum_with_var(node.right, var):
                return False
    return True


def _factors(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        return _factors(node.left) + _factors(node.right)
    return [node]


def is_factorised(s: str, var: str = "x") -> bool:
    node = parse(s, var).body
    while isinstance(node, ast.UnaryOp):
        node = node.operand
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        factors = _factors(node)
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
        factors = [node]
    else:
        return False
    for f in factors:
        while isinstance(f, ast.UnaryOp):
            f = f.operand
        if isinstance(f, ast.BinOp) and isinstance(f.op, ast.Pow):
            f = f.left
        if _is_sum_with_var(f, var):
            return True
    return False
