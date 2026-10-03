"""Hand-authored test identities and invented rules, never a regulatory database.

Familiar ingredient names exercise text grammar only. Metadata is empty;
the fictional DEMO MATERIAL carries the only example rule.
"""

from .flags import AnnexEntry, FlagIndex
from .kb import KB, Record, norm


def demo_kb() -> KB:
    names = (
        "AQUA", "WATER", "GLYCERIN", "NIACINAMIDE", "1,2-HEXANEDIOL",
        "ACRYLATES/C10-30 ALKYL ACRYLATE CROSSPOLYMER",
        "BUTYROSPERMUM PARKII BUTTER", "CI 77491", "CI 77891", "MICA",
        "ALOE BARBADENSIS LEAF JUICE", "DEMO MATERIAL",
    )
    kb = KB()
    for i, name in enumerate(names, 1):
        record = Record(
            substance_id=f"fixture-{i}", inci_name=name,
            item_type="synthetic fixture", status="illustrative", cas_no="",
            description="", functions=(), restrictions=(),
        )
        kb.index[norm(name)] = [record]
    return kb


def demo_flags() -> FlagIndex:
    entry = AnnexEntry(
        annex="SYNTHETIC", ref_no="illustrative-clause-example",
        chemical_name="Fictional demo material", glossary_name="DEMO MATERIAL",
        cas_numbers=(),
        product_types="(a) Face products (b) Hair products",
        max_concentration="(a) 2,5% (b) (i) 4% (ii) 7%",
        warnings="Illustrative only; not a regulation or a safety assessment.",
        identified_ingredients=("DEMO MATERIAL",), cmr="", update_date="",
    )
    return FlagIndex(entries=[entry], by_name={"DEMO MATERIAL": [entry]})


EXAMPLE_LABELS = (
    "Aqua, 1,2-Hexanediol, Butyrospermum Parkii (Shea) Butter",
    "Aqua/Water/Eau, Niacinamde, Unknown Example",
    "Mica, May contain (+/-): CI 77491, CL 77891",
    "Aloe Barbadensis, Acrylates/C10-30 Alkyl Acrylate Crosspolymer",
    "Glycerin, Demo Material",
)
