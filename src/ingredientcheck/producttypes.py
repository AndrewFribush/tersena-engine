"""Product-type awareness: map a free-text product description to tags and
decide which annex rules apply to it.

tags_for("rinse-off shampoo") -> {"rinse_off", "hair"}
rule_applies(rule_product_type_text, tags) -> True / False / None (unknown)
"""

from __future__ import annotations

import re

_TAG_PATTERNS: dict[str, str] = {
    "rinse_off": r"rinse[- ]?off|shampoo|cleanser|face wash|body wash|soap|conditioner\b",
    "leave_on": r"leave[- ]?on|cream|lotion|serum|moisturi[sz]er|balm|deodorant|sunscreen|makeup|foundation|lipstick|mascara",
    "hair": r"hair|shampoo|conditioner|scalp|dye",
    "face": r"face|facial|eye|lip|mascara|foundation|serum",
    "body": r"body|hand|foot|deodorant|antiperspirant",
    "lip": r"\blip",
    "eye": r"\beye|mascara|liner",
    "aerosol": r"aerosol|spray|mist",
    "powder": r"\bpowder|dry shampoo",
    "deodorant": r"deodorant|antiperspirant",
    "nail": r"\bnail",
    "oral": r"tooth|oral|mouth",
    "professional": r"professional",
}

_RULE_HINTS: dict[str, str] = {
    "rinse_off": r"rinse[- ]?off",
    "leave_on": r"leave[- ]?on",
    "hair": r"\bhair\b",
    "face": r"\bface\b|facial",
    "body": r"\bbody\b",
    "lip": r"\blip",
    "eye": r"\beye",
    "nail": r"\bnail",
    "oral": r"oral|tooth",
    "professional": r"professional",
}


def tags_for(product_type: str) -> set[str]:
    text = product_type.lower()
    tags = {tag for tag, pat in _TAG_PATTERNS.items() if re.search(pat, text)}
    # rinse-off and leave-on are exclusive; explicit rinse-off wins
    if "rinse_off" in tags:
        tags.discard("leave_on")
    return tags


# Splits a clause into its positive scope and its carved-out exceptions.
# Annex prose writes exclusions as "Other products except body lotion", "Hair
# products other than ...", "excluding ...". Without this split the excluded
# terms read as INCLUDED terms and the clause inverts.
_EXCEPT_RE = re.compile(
    r"\b(?:except|excluding|other than|with the exception of|not to be used (?:in|for|on))\b",
    re.I,
)

_RINSE_AXIS = {"rinse_off", "leave_on"}
_PART_AXIS = {"hair", "face", "body", "lip", "eye", "nail", "oral"}


def _hinted(text: str) -> set[str]:
    return {tag for tag, pat in _RULE_HINTS.items() if re.search(pat, text)}


def rule_applies(rule_text: str, tags: set[str]) -> bool | None:
    """Does an annex rule's product-type clause cover a product with `tags`?

    Returns None when the rule text carries no recognizable product-type
    signal (rule applies generally, or we can't tell) — callers should treat
    None as "possibly applies".
    """
    if not rule_text or not tags:
        return None
    text = rule_text.lower()

    # Split off exception clauses first, so "other products except body
    # lotion" doesn't positively hint body+leave_on. The first exception
    # marker ends the positive scope; everything after it is carve-out text.
    parts = _EXCEPT_RE.split(text, maxsplit=1)
    positive, exception = parts[0], (parts[1] if len(parts) > 1 else "")

    if exception:
        exc_hinted = _hinted(exception)
        # The product is carved out only when it matches the exception on
        # EVERY axis the exception expresses ("except body lotion" excludes a
        # body lotion, not a face serum that merely shares "leave-on").
        expressed = [
            axis for axis in (_RINSE_AXIS, _PART_AXIS) if exc_hinted & axis and tags & axis
        ]
        if expressed and all(exc_hinted & axis & tags for axis in expressed):
            return False

    hinted = _hinted(positive)
    if not hinted:
        # Positive scope is generic ("other products") — with a survived
        # exception check, the clause covers this product generally.
        return True if exception else None
    # Evaluate per axis: rinse behavior and body part must EACH agree when
    # both the rule and the product express them ("leave-on hair" must not
    # cover a leave-on *face* cream).
    for axis in (_RINSE_AXIS, _PART_AXIS):
        rule_side, product_side = hinted & axis, tags & axis
        if rule_side and product_side and not (rule_side & product_side):
            return False
    return True
