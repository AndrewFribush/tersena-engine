"""Match parsed label tokens to CosIng records.

Strategy ladder (first hit wins):
  1. exact       — normalized token is in the index
  2. paren       — strip parenthetical(s): "Butyrospermum Parkii (Shea) Butter"
                   -> "Butyrospermum Parkii Butter"; also try the parenthetical
                   content alone: "Iron Oxides (CI 77491)" -> "CI 77491"
  3. slash       — split on "/" and match parts ("Aqua/Water/Eau"); only used
                   when the full token missed, since "/" is legal inside INCI
                   names ("Acrylates/C10-30 Alkyl Acrylate Crosspolymer")
  4. fuzzy       — conservative edit-distance match for typos/OCR noise
"""

from __future__ import annotations

import re
from bisect import bisect_left
from dataclasses import dataclass
from difflib import SequenceMatcher

from .kb import KB, Record, norm

_PAREN_RE = re.compile(r"\(([^()]*)\)")


@dataclass
class Match:
    raw: str
    method: str  # exact | paren | slash | fuzzy | none
    records: list[Record]
    matched_name: str = ""
    score: float = 1.0


class Matcher:
    def __init__(self, kb: KB, fuzzy_cutoff: float = 0.90):
        self.kb = kb
        self.fuzzy_cutoff = fuzzy_cutoff
        self._cache: dict[str, Match] = {}
        # First-letter buckets keep fuzzy search tractable over ~34K keys.
        self._buckets: dict[str, list[str]] = {}
        for key in kb.index:
            if key:
                self._buckets.setdefault(key[0], []).append(key)
        self._sorted_keys = sorted(kb.index)

    # Cache keys come from user input, so an unbounded dict is a memory leak
    # on a long-lived process fed random strings. Bound it and drop oldest.
    _CACHE_MAX = 50_000

    def match(self, token: str) -> Match:
        key = norm(token)
        # Single .get() instead of membership-check-then-read: concurrent
        # requests (FastAPI threadpool) share this Matcher, and another
        # thread's eviction between the two steps raised KeyError.
        cached = self._cache.get(key)
        if cached is not None:
            return Match(token, cached.method, cached.records, cached.matched_name, cached.score)
        m = self._match_uncached(token, key)
        if len(self._cache) >= self._CACHE_MAX:
            # pop(..., None): the key may already be gone if another thread
            # is evicting the same snapshot concurrently.
            for stale in list(self._cache)[: self._CACHE_MAX // 10]:
                self._cache.pop(stale, None)
        self._cache[key] = m
        return m

    def match_all(self, tokens: list[str]) -> list[Match]:
        return [self.match(t) for t in tokens]

    def _match_uncached(self, token: str, key: str) -> Match:
        # OCR confusion in colorant indices: "CL 77891" -> "CI 77891"
        key = re.sub(r"^CL(?=\s*\d)", "CI", key)
        recs = self.kb.index.get(key)
        if recs:
            return Match(token, "exact", recs, recs[0].inci_name)

        # Parenthetical variants
        no_paren = norm(_PAREN_RE.sub(" ", key))
        if no_paren != key:
            recs = self.kb.index.get(no_paren)
            if recs:
                return Match(token, "paren", recs, recs[0].inci_name)
            for inner in _PAREN_RE.findall(key):
                recs = self.kb.index.get(norm(inner))
                if recs:
                    return Match(token, "paren", recs, recs[0].inci_name)

        # Slash alternatives — collect all parts that resolve
        if "/" in key:
            found: list[Record] = []
            names = []
            for part in key.split("/"):
                part_recs = self.kb.index.get(norm(part))
                if part_recs:
                    for r in part_recs:
                        if r not in found:
                            found.append(r)
                    names.append(part_recs[0].inci_name)
            if found:
                return Match(token, "slash", found, " / ".join(dict.fromkeys(names)))

        # Genus-species prefix: labels often write the bare botanical name
        # ("Aloe Barbadensis") where CosIng only lists part-specific entries
        # ("ALOE BARBADENSIS LEAF JUICE", ...). Resolve to the shortest
        # extension — the most generic form — at reduced confidence.
        # Multi-word only, so bare "SODIUM" can't swallow every sodium salt.
        if len(key.split()) >= 2:
            prefix = key + " "
            i = bisect_left(self._sorted_keys, prefix)
            cands = []
            while i < len(self._sorted_keys) and self._sorted_keys[i].startswith(prefix):
                cands.append(self._sorted_keys[i])
                i += 1
                if len(cands) > 25:
                    break
            if cands:
                best = min(cands, key=len)
                recs = self.kb.index[best]
                return Match(token, "prefix", recs, recs[0].inci_name, 0.8)

        # Fuzzy — conservative, and only for tokens long enough to be
        # distinctive. Tried on both the raw key and its paren-stripped
        # variant ("Butyrospermum Parki (Shea) Butter" fuzzes as
        # "BUTYROSPERMUM PARKI BUTTER", which is 1 edit from the real name).
        variants = [key] if no_paren == key else [key, no_paren]
        for var in variants:
            if len(var) < 6:
                continue
            best_key, best_score = "", 0.0
            for cand in self._buckets.get(var[0], []):
                if abs(len(cand) - len(var)) > 3:
                    continue
                score = SequenceMatcher(None, var, cand).ratio()
                if score > best_score:
                    best_key, best_score = cand, score
            if best_score >= self.fuzzy_cutoff:
                recs = self.kb.index[best_key]
                return Match(token, "fuzzy", recs, recs[0].inci_name, best_score)

        return Match(token, "none", [], "", 0.0)
