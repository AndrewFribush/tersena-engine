"""Parse annex restriction prose into computable rules.

Annex III-VI cells pair lettered clauses across columns:

    Product Type:       (a) Hair products  (b) Depilatories
    Max concentration:  (a) (i) 8% (ii) 11%  (b) 5%

parse_entry() aligns the clauses and extracts numeric concentration limits,
yielding Rule(scope="a", product_type="Hair products", max_pct=11.0, ...).
Unlettered cells become a single rule. The raw prose is always preserved —
rules are a computable *view*, not a replacement.

EU decimal commas ("2,2%") are handled.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .flags import AnnexEntry

_CLAUSE_RE = re.compile(r"\(([a-z])\)\s")
_PCT_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")


@dataclass
class Rule:
    scope: str  # clause letter, or "" for a single unlettered rule
    product_type: str
    max_pct: float | None  # highest limit in the clause (upper bound)
    all_pcts: tuple[float, ...]
    conditions: str
    # Strictest limit in the clause. When a clause carries sub-cases —
    # "(a)(i) 8% general use (ii) 11% professional use" — the upper bound
    # under-flags: a consumer product is bound by the 8%. Compliance checks
    # must use this, not max_pct.
    min_pct: float | None = None
    # True when the clause text carries a restriction we don't model
    # (age limits, warning-label duties, professional-use-only, bans in
    # specific applications). Callers must not read "no numeric limit" as
    # "unrestricted" — read the raw conditions text.
    unmodeled_conditions: bool = False


_UNMODELED_RE = re.compile(
    r"under \d+ year|not to be used|not for use|professional|must not|"
    r"shall not|prohibited|warning|label|children|mucous membrane",
    re.I,
)


def _split_clauses(text: str) -> dict[str, str]:
    """'(a) Hair products (b) Depilatories' -> {'a': 'Hair products', ...}

    Handles both '(a)' and bare 'a)' clause markers. Roman-numeral sub-cases
    '(i) 8% (ii) 11%' are folded into their parent letter clause: a lone 'i'
    only counts as a clause letter when it follows 'h' in sequence.
    """
    # normalize bare "a) ..." markers to "(a) ..."
    text = re.sub(r"(?<![a-zA-Z0-9(])([a-z])\)", r"(\1)", text)
    parts = _CLAUSE_RE.split(text)
    if len(parts) < 3:
        return {}
    out: dict[str, str] = {}
    prev: str | None = None
    for letter, body in zip(parts[1::2], parts[2::2]):
        if letter == "i" and prev != "h":
            if prev is not None:  # roman-numeral sub-case -> parent clause
                out[prev] = f"{out[prev]} (i) {body.strip()}".strip()
            continue
        if letter in out:  # repeated letter ("For (a) and (b): ..."): append
            out[letter] = f"{out[letter]} {body.strip()}".strip()
            prev = letter
            continue
        out[letter] = body.strip()
        prev = letter
    return out


_MGKG_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*mg/kg")
# "For (a) and (b): ..." and "For (a), (b) and (c): ..." — any clause count
_SHARED_RE = re.compile(
    r"For\s+((?:\([a-z]\)[,\s]*(?:and\s+)?){2,})\s*:?\s*(.+)", re.S | re.I
)
_CLAUSE_LETTER_RE = re.compile(r"\(([a-z])\)")


def _pcts(text: str) -> tuple[float, ...]:
    vals = [float(p.replace(",", ".")) for p in _PCT_RE.findall(text)]
    # mg/kg == ppm; convert so limits stay comparable (100 mg/kg -> 0.01%)
    vals += [float(p.replace(",", ".")) / 10_000 for p in _MGKG_RE.findall(text)]
    return tuple(vals)


def parse_entry(entry: AnnexEntry) -> list[Rule]:
    types = _split_clauses(entry.product_types)
    concs = _split_clauses(entry.max_concentration)

    letters = sorted(set(types) | set(concs))
    if not letters:
        pcts = _pcts(entry.max_concentration)
        if not (entry.product_types or entry.max_concentration):
            return []
        text = f"{entry.product_types} {entry.max_concentration} {entry.warnings}"
        return [
            Rule(
                scope="",
                product_type=entry.product_types,
                max_pct=max(pcts) if pcts else None,
                all_pcts=pcts,
                conditions=entry.max_concentration,
                min_pct=min(pcts) if pcts else None,
                unmodeled_conditions=bool(_UNMODELED_RE.search(text)),
            )
        ]

    # "For (a) and (b): ...limit..." — a condition shared across clauses
    shared_pcts: tuple[float, ...] = ()
    shared_letters: set[str] = set()
    shared_text = ""
    m = _SHARED_RE.search(entry.max_concentration)
    if m:
        shared_letters = set(_CLAUSE_LETTER_RE.findall(m.group(1)))
        shared_text = m.group(2).strip()
        shared_pcts = _pcts(shared_text)

    # lettered product types but a single unlettered limit: applies to all
    fallback = entry.max_concentration if not concs else ""

    rules = []
    for letter in letters:
        conc_text = concs.get(letter, "") or fallback
        pcts = _pcts(conc_text)
        if not pcts and letter in shared_letters and shared_pcts:
            pcts, conc_text = shared_pcts, shared_text
        text = f"{types.get(letter, '')} {conc_text} {entry.warnings}"
        rules.append(
            Rule(
                scope=letter,
                product_type=types.get(letter, ""),
                max_pct=max(pcts) if pcts else None,
                all_pcts=pcts,
                conditions=conc_text,
                min_pct=min(pcts) if pcts else None,
                unmodeled_conditions=bool(_UNMODELED_RE.search(text)),
            )
        )
    return rules
