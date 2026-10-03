"""Original synthetic rule and scope tests; no corpus-wide claims."""

from tersena.flags import AnnexEntry
from tersena.producttypes import rule_applies, tags_for
from tersena.rules import parse_entry


def entry(product_types="", max_concentration="", warnings=""):
    return AnnexEntry(
        annex="SYNTHETIC",
        ref_no="TEST",
        chemical_name="test chemical",
        glossary_name="TEST SUBSTANCE",
        cas_numbers=(),
        product_types=product_types,
        max_concentration=max_concentration,
        warnings=warnings,
        identified_ingredients=(),
        cmr="",
        update_date="",
    )


def test_roman_subcases_expose_strictest_as_min_pct():
    rules = parse_entry(
        entry("(a) Hair products (b) Depilatories", "(a) (i) 8% (ii) 11% (b) 5%")
    )
    by = {r.scope: r for r in rules}
    assert by["a"].max_pct == 11.0
    assert by["a"].min_pct == 8.0  # the binding limit for consumer products
    assert by["a"].all_pcts == (8.0, 11.0)
    assert by["b"].min_pct == by["b"].max_pct == 5.0


def test_single_limit_min_equals_max():
    rules = parse_entry(entry("Hair dye", "2,5%"))
    assert len(rules) == 1
    assert rules[0].max_pct == rules[0].min_pct == 2.5


def test_no_numeric_limit_yields_none_pcts():
    rules = parse_entry(entry("Not in aerosol dispensers", "Rinse-off use only"))
    assert rules[0].max_pct is None and rules[0].min_pct is None
    assert rules[0].all_pcts == ()


def test_mixed_pct_and_mgkg_min_is_strictest():
    rules = parse_entry(entry("x", "0.5% (100 mg/kg free formaldehyde)"))
    assert rules[0].max_pct == 0.5
    assert rules[0].min_pct == 0.01  # 100 mg/kg == 0.01%
    assert rules[0].all_pcts == (0.5, 0.01)


def test_mgkg_only_converted_to_pct():
    rules = parse_entry(entry("All products", "100 mg/kg"))
    assert rules[0].max_pct == 0.01


def test_children_warning_flags_unmodeled():
    rules = parse_entry(
        entry("Hair dye", "2%", "Not to be used for children under 3 years of age")
    )
    assert rules[0].unmodeled_conditions is True


def test_professional_clause_flags_only_that_clause():
    rules = parse_entry(
        entry("(a) General use (b) Professional use", "(a) 2% (b) 6%")
    )
    by = {r.scope: r for r in rules}
    assert by["a"].unmodeled_conditions is False
    assert by["b"].unmodeled_conditions is True


def test_must_not_and_mucous_membrane_flag_unmodeled():
    r1 = parse_entry(entry("Oral products", "1%", "Must not be used on mucous membranes"))
    assert r1[0].unmodeled_conditions is True
    r2 = parse_entry(entry("Nail products", "Shall not exceed trace amounts"))
    assert r2[0].unmodeled_conditions is True


def test_plain_limit_not_flagged_unmodeled():
    rules = parse_entry(entry("Rinse-off hair products", "3%"))
    assert rules[0].unmodeled_conditions is False


def test_empty_entry_yields_no_rules():
    assert parse_entry(entry("", "")) == []


def test_shared_limit_across_clauses():
    rules = parse_entry(entry("(a) Face products (b) Body products", "For (a) and (b): 0.5%"))
    assert {r.scope for r in rules} == {"a", "b"}
    assert all(r.max_pct == 0.5 for r in rules)


def test_unlettered_limit_applies_to_all_lettered_types():
    rules = parse_entry(entry("(a) Face products (b) Body products", "3%"))
    assert {r.scope for r in rules} == {"a", "b"}
    assert all(r.max_pct == 3.0 and r.min_pct == 3.0 for r in rules)


def test_bare_letter_markers_normalized():
    rules = parse_entry(entry("a) Face products b) Body products", "a) 1% b) 2%"))
    by = {r.scope: r for r in rules}
    assert by["a"].max_pct == 1.0 and by["b"].max_pct == 2.0


def test_raw_conditions_text_preserved():
    rules = parse_entry(entry("Hair dye", "2% after mixing under oxidative conditions"))
    assert "after mixing" in rules[0].conditions


def test_leave_on_hair_rule_excludes_face_cream():
    tags = tags_for("leave-on face cream")
    assert rule_applies("Leave-on hair products", tags) is False


def test_rinse_off_rule_excludes_leave_on_product():
    tags = tags_for("leave-on face cream")
    assert rule_applies("Rinse-off products", tags) is False


def test_matching_axes_apply():
    tags = tags_for("rinse-off shampoo")
    assert rule_applies("Rinse-off hair products", tags) is True


def test_no_tags_returns_none():
    assert rule_applies("Hair products", set()) is None


def test_no_recognizable_hint_returns_none():
    tags = tags_for("leave-on face cream")
    assert rule_applies("All cosmetic products", tags) is None


def test_rinse_off_wins_over_leave_on_in_tags():
    # "shampoo" implies rinse_off; "conditioner" text also matches leave_on
    # patterns via nothing — explicit rinse-off must win when both fire.
    tags = tags_for("rinse-off leave-on hybrid cream shampoo")
    assert "rinse_off" in tags and "leave_on" not in tags
