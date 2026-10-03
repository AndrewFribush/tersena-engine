"""Extracted normalization and record types; callers provide an explicit KB."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


def norm(s: str) -> str:
    """Normalize a name for index lookup: casefold, strip accents/footnote
    marks, unify dashes and whitespace."""
    # Footnote junk must be stripped BEFORE NFKD: NFKD converts superscript
    # digits (¹²³) to plain digits, after which they are indistinguishable
    # from real digits in names ("POLYQUATERNIUM-1", "CI 77891", ...). Only
    # true superscript characters are stripped here — never plain digits,
    # since name+digit is frequently a different real substance.
    for junk in ("*", "†", "‡", "⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"):
        s = s.replace(junk, "")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper()
    s = s.replace("–", "-").replace("—", "-").replace("’", "'")
    s = " ".join(s.split())
    return s.strip(" .,;:")


_TRUNCATED_RE = re.compile(
    r"conforms?\s+(generally\s+)?to\s+the\s+(general\s+)?formula[:.]?\s*$", re.I
)


@dataclass
class Record:
    substance_id: str
    inci_name: str
    item_type: str
    status: str
    cas_no: str
    description: str
    functions: tuple[str, ...]
    restrictions: tuple[str, ...]

    @property
    def description_truncated(self) -> bool:
        """CosIng renders structural formulas as images; the text export cuts
        off at "...conforms to the formula". Flag it so consumers don't
        present a dangling sentence as the full description."""
        return bool(_TRUNCATED_RE.search(self.description or ""))


@dataclass
class KB:
    index: dict[str, list[Record]] = field(default_factory=dict)

    def lookup(self, name: str) -> list[Record]:
        return self.index.get(norm(name), [])

    def __len__(self) -> int:
        return sum(len(v) for v in self.index.values())
