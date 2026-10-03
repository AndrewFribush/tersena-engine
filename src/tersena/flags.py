"""Extracted rule record and join index; no loaders or regulatory citation generator.

All demo entries are synthetic. The original AnnexEntry field shape is retained
for parse_entry compatibility; no field grants these fixtures regulatory meaning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .kb import Record, norm

_CAS_RE = re.compile(r"\b\d{2,7}-\d{2}-\d\b")


@dataclass
class AnnexEntry:
    annex: str
    ref_no: str
    chemical_name: str
    glossary_name: str
    cas_numbers: tuple[str, ...]
    product_types: str
    max_concentration: str
    warnings: str
    identified_ingredients: tuple[str, ...]
    cmr: str
    update_date: str


@dataclass
class FlagIndex:
    entries: list[AnnexEntry] = field(default_factory=list)
    by_cas: dict[str, list[AnnexEntry]] = field(default_factory=dict)
    by_name: dict[str, list[AnnexEntry]] = field(default_factory=dict)

    def flags_for(self, record: Record) -> list[AnnexEntry]:
        found: list[AnnexEntry] = []
        for cas in _CAS_RE.findall(record.cas_no or ""):
            for e in self.by_cas.get(cas, []):
                if e not in found:
                    found.append(e)
        for e in self.by_name.get(norm(record.inci_name), []):
            if e not in found:
                found.append(e)
        return found
