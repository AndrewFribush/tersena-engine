"""Parse raw ingredient-label text into candidate INCI tokens.

Real labels are messy: footnote asterisks, percentage annotations,
"May contain (+/-):" blocks for colorants, "Ingredients:" prefixes,
comma splits that must not fire inside parentheses
("Acrylates/C10-30 Alkyl Acrylate Crosspolymer" and
"Butyrospermum Parkii (Shea) Butter" are single ingredients).
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

_PREFIX_RE = re.compile(r"^\s*(ingredients?|inci|composition|ingr[ée]dients?)\s*[:.]?\s*", re.I)
_MAY_CONTAIN_RE = re.compile(
    r"(?:\bmay contain\b|\bpeut contenir\b)\s*(?:[\(\[]\s*\+\s*/?\s*-\s*[\)\]]?)?\s*[:.]?"
    r"|[\(\[]\s*\+\s*/?\s*-\s*[\)\]]?\s*[:.]?",
    re.I,
)
_PCT_RE = re.compile(r"\(\s*[<>]?\s*[\d.,]+\s*%\s*\)")
_FOOTNOTE_LEGEND_RE = re.compile(r"[*†‡]+\s*[=:]?\s*(certified|organic|natural|from|issu|biologique|ingredient[s]? from)[^,;]*", re.I)
_LEADING_AND_RE = re.compile(r"^(and|et|und)\s+", re.I)

_SEPARATORS = ",;·•●"  # comma, semicolon, middot, bullets


@dataclass
class ParsedLabel:
    tokens: list[str] = field(default_factory=list)
    may_contain: list[str] = field(default_factory=list)


def _split_top_level(text: str) -> list[str]:
    """Split on separators, but never inside () or [], and never between two
    digits with no space — "1,2-Hexanediol" and "Toluene-2,5-Diamine" are
    single ingredients, not lists."""
    parts, buf, depth = [], [], 0
    for i, ch in enumerate(text):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch in _SEPARATORS and depth == 0:
            prev = text[i - 1] if i else ""
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if ch == "," and prev.isdigit() and nxt.isdigit():
                buf.append(ch)
                continue
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return parts


def _strip_bare_pct(tok: str) -> str:
    """Strip a bare trailing percentage annotation: "Niacinamide 10%",
    "Vitamin C 15 %", "Retinol < 0.5%". Anchored to the token end so a
    percentage inside a name ("Alcohol 96% Denat") is left alone.

    Implemented as a linear reverse scan, equivalent to the regex
    r"\\s+[<>]?\\s*[\\d.,]+\\s*%\\s*$" — which backtracked catastrophically
    on long whitespace runs (a 20K mostly-whitespace label hung the API
    for minutes)."""
    t = tok.rstrip()
    if not t.endswith("%"):
        return tok
    j = len(t) - 2
    while j >= 0 and t[j].isspace():  # \s* between number and %
        j -= 1
    num_end = j
    while j >= 0 and t[j] in "0123456789.,":  # [\d.,]+
        j -= 1
    if j == num_end:  # no number before the %
        return tok
    ws_end = j
    while j >= 0 and t[j].isspace():  # whitespace before the number
        j -= 1
    had_ws = j != ws_end
    if j >= 0 and t[j] in "<>":  # optional comparator, needs \s+ before it
        j -= 1
        if j < 0 or not t[j].isspace():
            return tok
        while j >= 0 and t[j].isspace():
            j -= 1
    elif not had_ws:
        # No separating whitespace: the token IS the percentage ("10%")
        # or the % is glued to the name — not a trailing annotation.
        return tok
    return t[: j + 1]


def _clean_token(tok: str) -> str:
    tok = _PCT_RE.sub("", tok)
    tok = _strip_bare_pct(tok)
    tok = tok.strip().strip(".")
    tok = _LEADING_AND_RE.sub("", tok)
    tok = tok.strip()
    # Footnote markers glued to names: "Glycerin*", "Aloe Vera†"
    tok = tok.strip("*†‡ ")
    return tok


def parse_label(text: str) -> ParsedLabel:
    text = html.unescape(html.unescape(text))  # twice: OBF data has &amp;quot;
    text = text.replace('"', " ").replace("\n", " ").replace("\r", " ")
    text = _PREFIX_RE.sub("", text)
    text = _FOOTNOTE_LEGEND_RE.sub("", text)

    segments = _MAY_CONTAIN_RE.split(text, maxsplit=1)
    main, may = segments[0], segments[1] if len(segments) > 1 else ""

    parsed = ParsedLabel()
    for raw in _split_top_level(main):
        tok = _clean_token(raw)
        if tok:
            parsed.tokens.append(tok)
    for raw in _split_top_level(may):
        tok = _clean_token(raw)
        if tok:
            parsed.may_contain.append(tok)
    return parsed
