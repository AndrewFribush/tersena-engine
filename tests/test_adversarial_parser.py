"""Adversarial / edge-case tests for parser.parse_label.

These pin down real current behavior on hostile label text: nested and
unbalanced parentheses, "may contain (+/-)" variants, bare percentages,
unicode, locant commas, pathological whitespace, mixed delimiters.
"""

import multiprocessing
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tersena.parser import parse_label


# --- nested / unbalanced parentheses --------------------------------------


def test_nested_parentheses_single_token():
    p = parse_label("Water (Aqua (purified)), Glycerin")
    assert p.tokens == ["Water (Aqua (purified))", "Glycerin"]


def test_comma_inside_brackets_not_split():
    p = parse_label("Aqua, Polymer [a, b, c], Glycerin")
    assert p.tokens == ["Aqua", "Polymer [a, b, c]", "Glycerin"]


def test_unbalanced_open_paren_swallows_rest():
    # Depth never returns to 0, so the comma stays inside the token.
    # Documented current behavior: data is preserved, not dropped.
    p = parse_label("Aqua, (unclosed paren, Glycerin")
    assert p.tokens == ["Aqua", "(unclosed paren, Glycerin"]


def test_unbalanced_close_paren_clamps_to_zero():
    # A stray ")" must not push depth negative and disable splitting.
    p = parse_label("Aqua, deep) close, Glycerin")
    assert p.tokens == ["Aqua", "deep) close", "Glycerin"]


def test_botanical_parenthetical_survives():
    p = parse_label("Aqua, Butyrospermum Parkii (Shea) Butter, Glycerin")
    assert p.tokens[1] == "Butyrospermum Parkii (Shea) Butter"


# --- may contain (+/-) variants -------------------------------------------


def test_may_contain_plusminus_colon():
    p = parse_label("Aqua, Mica, May Contain (+/-): CI 77491, CI 77891")
    assert p.tokens == ["Aqua", "Mica"]
    assert p.may_contain == ["CI 77491", "CI 77891"]


def test_bare_plusminus_no_may_contain_words():
    p = parse_label("Aqua, Mica (+/-) CI 77891, CI 77491")
    assert p.tokens == ["Aqua", "Mica"]
    assert p.may_contain == ["CI 77891", "CI 77491"]


def test_french_peut_contenir():
    p = parse_label("Eau, Mica, Peut Contenir: CI 77491")
    assert p.tokens == ["Eau", "Mica"]
    assert p.may_contain == ["CI 77491"]


def test_may_contain_uppercase_no_colon():
    p = parse_label("AQUA, MICA MAY CONTAIN CI 77891")
    assert p.tokens == ["AQUA", "MICA"]
    assert p.may_contain == ["CI 77891"]


def test_may_contain_at_start_leaves_empty_tokens():
    p = parse_label("May contain (+/-): CI 77891, CI 77491")
    assert p.tokens == []
    assert p.may_contain == ["CI 77891", "CI 77491"]


# --- percentages -----------------------------------------------------------


def test_bare_trailing_percentage_stripped():
    p = parse_label("Niacinamide 10%")
    assert p.tokens == ["Niacinamide"]


def test_bare_percentage_with_space_and_comparators():
    p = parse_label("Aqua, Vitamin C 15 %, Niacinamide <1%, Retinol >0.5%")
    assert p.tokens == ["Aqua", "Vitamin C", "Niacinamide", "Retinol"]


def test_parenthesized_percentage_with_decimal_comma():
    p = parse_label("Aqua, Retinol (<0,3%), Glycerin")
    assert p.tokens == ["Aqua", "Retinol", "Glycerin"]


def test_internal_percentage_preserved():
    # Only a TRAILING percentage is an annotation; one inside a name stays.
    p = parse_label("Aqua, Alcohol 96% Denat, Glycerin")
    assert p.tokens == ["Aqua", "Alcohol 96% Denat", "Glycerin"]


# --- unicode, accents, footnotes ------------------------------------------


def test_accented_prefix_and_names():
    p = parse_label("Ingrédients: Eau, Glycérine")
    assert p.tokens == ["Eau", "Glycérine"]


def test_footnote_daggers_stripped():
    p = parse_label("Aloe Vera†, Glycerin‡, Panthenol*")
    assert p.tokens == ["Aloe Vera", "Glycerin", "Panthenol"]


def test_footnote_legend_removed():
    p = parse_label("Aqua, Glycerin*, *from organic sources, Panthenol")
    assert p.tokens == ["Aqua", "Glycerin", "Panthenol"]


def test_certified_organic_legend_removed():
    p = parse_label("Aloe Barbadensis Leaf Juice*, Glycerin, *certified organic")
    assert p.tokens == ["Aloe Barbadensis Leaf Juice", "Glycerin"]


def test_html_entities_double_unescaped():
    p = parse_label("Aqua&amp;quot;, Glycerin")
    assert "Glycerin" in p.tokens


# --- locant commas in chemical names --------------------------------------


def test_locant_comma_not_split():
    p = parse_label("Aqua, 1,2-Hexanediol, Glycerin")
    assert p.tokens == ["Aqua", "1,2-Hexanediol", "Glycerin"]


def test_locant_comma_mid_name():
    p = parse_label("Toluene-2,5-Diamine, Aqua")
    assert p.tokens == ["Toluene-2,5-Diamine", "Aqua"]


def test_locant_at_label_start():
    p = parse_label("1,2-Hexanediol")
    assert p.tokens == ["1,2-Hexanediol"]


def test_digit_comma_space_digit_still_splits():
    # "CI 77891, 2-Hexanediol": the space after the comma means it's a list
    # separator, not a locant.
    p = parse_label("CI 77891, 2-Hexanediol")
    assert p.tokens == ["CI 77891", "2-Hexanediol"]


# --- empty / degenerate input ---------------------------------------------


def test_empty_label():
    p = parse_label("")
    assert p.tokens == [] and p.may_contain == []


def test_whitespace_only_label():
    p = parse_label("   \n\t  \r  ")
    assert p.tokens == [] and p.may_contain == []


def test_separators_only():
    p = parse_label(",,,;;;··•")
    assert p.tokens == []


def test_footnote_star_only():
    p = parse_label("*")
    assert p.tokens == []


def test_absurdly_long_single_token_survives():
    tok = "X" * 10_000
    p = parse_label(tok + ", Glycerin")
    assert p.tokens == [tok, "Glycerin"]


# --- mixed delimiters ------------------------------------------------------


def test_semicolons_and_newlines():
    p = parse_label("Aqua;\nGlycerin;\r\nPanthenol")
    assert p.tokens == ["Aqua", "Glycerin", "Panthenol"]


def test_middots_and_bullets():
    p = parse_label("Aqua • Glycerin · Panthenol ● Mica")
    assert p.tokens == ["Aqua", "Glycerin", "Panthenol", "Mica"]


def test_mixed_comma_semicolon():
    p = parse_label("Aqua, Glycerin; Panthenol")
    assert p.tokens == ["Aqua", "Glycerin", "Panthenol"]


# --- trailing periods, prefixes, misc -------------------------------------


def test_trailing_period_stripped():
    p = parse_label("Aqua, Glycerin.")
    assert p.tokens == ["Aqua", "Glycerin"]


def test_alcohol_denat_loses_trailing_period():
    # Current behavior: the token-final "." of "Alcohol Denat." is stripped
    # along with sentence periods. The matcher layer must absorb this.
    p = parse_label("Aqua, Alcohol Denat., Glycerin")
    assert p.tokens == ["Aqua", "Alcohol Denat", "Glycerin"]


def test_inci_and_composition_prefixes():
    assert parse_label("INCI: Aqua, Glycerin").tokens == ["Aqua", "Glycerin"]
    assert parse_label("Composition. Aqua, Glycerin").tokens == ["Aqua", "Glycerin"]


def test_leading_and_variants():
    p = parse_label("Aqua, and Glycerin, et Panthenol, und Tocopherol")
    assert p.tokens == ["Aqua", "Glycerin", "Panthenol", "Tocopherol"]


def test_duplicates_preserved_verbatim():
    # The parser must not dedupe or case-fold — that's downstream's decision.
    p = parse_label("Aqua, Aqua, Glycerin, glycerin")
    assert p.tokens == ["Aqua", "Aqua", "Glycerin", "glycerin"]


def test_double_quotes_replaced():
    p = parse_label('Aqua, "Glycerin", Panthenol')
    assert p.tokens == ["Aqua", "Glycerin", "Panthenol"]


# --- regex backtracking blowup (fixed: linear reverse scan) ----------------


def _parse_padded(q):
    parse_label("Aqua" + " " * 2000)
    q.put(True)


def test_no_catastrophic_backtracking_on_whitespace():
    ctx = multiprocessing.get_context("spawn")
    q = ctx.Queue()
    proc = ctx.Process(target=_parse_padded, args=(q,))
    proc.start()
    proc.join(timeout=3)
    try:
        assert not proc.is_alive(), "parse_label still running after 3s on 2000 trailing spaces"
    finally:
        if proc.is_alive():
            proc.terminate()
            proc.join()
