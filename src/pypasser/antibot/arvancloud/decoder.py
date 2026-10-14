"""Pure-Python JSFuck decoder for the ArvanCloud ``values()`` challenge.

An ArvanCloud challenge page hides two cookie values inside a JSFuck
expression: the ``__arcsjs`` and ``__arcsjsc`` cookie bodies. The browser
would run ``eval()`` on them; this module evaluates the same grammar without
a JS engine.

Grammar (everything V8 can build from ``[]``, ``+`` and ``!``):

``[<bools>]+[]``
    Decimal string — ``[!+[]+!+[]]+[]`` is ``"2"`` (one ``!`` per unit).
``(!![]+[])[N]``
    Index into ``"true"``.
``(![]+[])[N]``
    Index into ``"false"``.
``([][[]]+[])[N]``
    Index into ``"undefined"``.
``([]['fill']+'')[N]``
    Index into ``"function fill() { [native code] }"``.
``([]['entries']()+'')[N]``
    Index into ``"[object Array Iterator]"``.
``([]+[])['constructor']['fromCharCode'](N)``
    ``String.fromCharCode(N)``.
``"+A+B..."``
    Concatenation of the terms above; a plain quoted string is itself.

A bare ``[N]+[]`` group is *not* an index — it only follows a ``+`` (as a
standalone term). Index brackets always follow a ``)`` or ``]`` (the source
being indexed), which is why the merge step below uses a lookbehind.
"""

from __future__ import annotations

import re

# String sources produced by coercing JS primitives to strings.
STR_SOURCES = {
    "TRUE": "true",
    "FALSE": "false",
    "UNDEF": "undefined",  # [][[]] + []
    "FILL": "function fill() { [native code] }",
    "ENTRIES": "[object Array Iterator]",
}

# A number token: ``+[]`` (0), ``!+[]`` (1), ``+!+[]`` (1) ... value = the
# number of ``!``. Plain digits count too (the grammar emits them rarely).
_TOK = r"(?:(?:\+!?|!))?\+\[\]"
_NUM = rf"(?:{_TOK}|\d)+"


def _num(expr: str) -> int:
    """Evaluate a JSFuck number expression."""
    if not re.fullmatch(_NUM, expr):
        raise ValueError(f"not a JSFuck number: {expr!r}")
    if "!" in expr:
        return expr.count("!")
    if expr.isdigit():
        return int(expr)
    return 0


def _split_terms(expr: str) -> list[str]:
    """Split a concatenation expression on top-level ``+`` signs."""
    parts: list[str] = []
    cur = ""
    depth = 0
    in_str = False
    i = 0
    while i < len(expr):
        ch = expr[i]
        if in_str:
            cur += ch
            if ch == "\\":
                cur += expr[i + 1]
                i += 2
                continue
            if ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            cur += ch
            i += 1
            continue
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "+" and depth == 0:
            parts.append(cur)
            cur = ""
            i += 1
            continue
        cur += ch
        i += 1
    if cur:
        parts.append(cur)
    return parts


def _term(term: str) -> str:
    """Evaluate one concatenation term."""
    t = term.strip().replace(" ", "")
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        return t[1:-1]
    # [<bools>]+[] -> decimal string
    m = re.fullmatch(rf"\[({_NUM})\]\+\[]", t)
    if m:
        return str(_num(m.group(1)))
    # (!![]+[])[N] -> "true"[N]
    m = re.fullmatch(rf"\(!!\[\]\+\[\]\)\[({_NUM})\]", t)
    if m:
        return STR_SOURCES["TRUE"][_num(m.group(1))]
    # (![]+[])[N] -> "false"[N]
    m = re.fullmatch(rf"\(!\[\]\+\[\]\)\[({_NUM})\]", t)
    if m:
        return STR_SOURCES["FALSE"][_num(m.group(1))]
    # ([][[]]+[])[N] -> "undefined"[N]
    m = re.fullmatch(r"\(\[\]\[\[\]\]\+\[\]\)\[(%s)\]" % _NUM, t)
    if m:
        return STR_SOURCES["UNDEF"][_num(m.group(1))]
    # ([]['fill']+'')[N]
    m = re.fullmatch(rf"\(\[\]\['fill'\]\+''\)\[({_NUM})\]", t)
    if m:
        return STR_SOURCES["FILL"][_num(m.group(1))]
    # ([]['entries']()+'')[N]
    m = re.fullmatch(rf"\(\[\]\['entries'\]\(\)\+''\)\[({_NUM})\]", t)
    if m:
        return STR_SOURCES["ENTRIES"][_num(m.group(1))]
    # ([]+[])['constructor']['fromCharCode'](N)
    m = re.fullmatch(rf"\(\[\]\+\[\]\)\['constructor'\]\['fromCharCode'\]\(({_NUM})\)", t)
    if m:
        return chr(_num(m.group(1)))
    raise ValueError(f"unknown JSFuck term: {t!r}")


_MERGE = re.compile(rf"(?<![\)\]])\[({_NUM})\]\+\[]")


def decode_eval(expr: str) -> str:
    """Decode one ``eval("...")`` argument to its string value."""
    e = expr.strip()
    if e.startswith('"') and e.endswith('"'):
        inner = e[1:-1]
        if not any(ch in inner for ch in "[()+"):
            return inner.replace('\\"', '"')
    e = _MERGE.sub(lambda m: '"' + str(_num(m.group(1))) + '"', e)
    return "".join(_term(t) for t in _split_terms(e))


def extract_values(js: str) -> tuple[str, str]:
    """Extract ``(value_v1, value)`` from a ``values()`` function body.

    Returns
    -------
    tuple of str
        The decoded ``value_v1`` (``__arcsjs`` cookie) and ``value``
        (``__arcsjsc`` cookie) expressions.

    Raises
    ------
    ValueError
        If the function or its two ``eval`` arguments are missing.
    """
    m = re.search(r"function\s+values\s*\(\s*\)\s*\{", js)
    if not m:
        raise ValueError("values() not found")
    body = js[m.start():]
    evals = re.findall(r"eval\(\"((?:[^\"\\]|\\.)*)\"\)", body)
    if len(evals) != 2:
        raise ValueError(f"expected 2 eval arguments, got {len(evals)}")
    return decode_eval(evals[0]), decode_eval(evals[1])
