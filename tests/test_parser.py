import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ingredientcheck.parser import parse_label


def test_basic_split():
    p = parse_label("Aqua, Glycerin, Niacinamide")
    assert p.tokens == ["Aqua", "Glycerin", "Niacinamide"]


def test_prefix_stripped():
    p = parse_label("Ingredients: Aqua, Glycerin.")
    assert p.tokens == ["Aqua", "Glycerin"]


def test_comma_inside_parens_not_split():
    p = parse_label("Aqua, C12-15 Alkyl Benzoate, Polyester-7 (1,3-propanediol)")
    assert len(p.tokens) == 3
    assert p.tokens[2] == "Polyester-7 (1,3-propanediol)"


def test_may_contain_block():
    p = parse_label("Aqua, Mica, May Contain (+/-): CI 77491, CI 77891")
    assert p.tokens == ["Aqua", "Mica"]
    assert p.may_contain == ["CI 77491", "CI 77891"]


def test_footnote_markers_stripped():
    p = parse_label("Aloe Barbadensis Leaf Juice*, Glycerin†, *certified organic")
    assert p.tokens == ["Aloe Barbadensis Leaf Juice", "Glycerin"]


def test_percentages_removed():
    p = parse_label("Aqua, Niacinamide (10%), Zinc PCA (1%)")
    assert p.tokens == ["Aqua", "Niacinamide", "Zinc PCA"]


def test_leading_and():
    p = parse_label("Aqua, Glycerin, and Citric Acid")
    assert p.tokens == ["Aqua", "Glycerin", "Citric Acid"]


def test_semicolon_and_newlines():
    p = parse_label("Aqua;\nGlycerin;\nPanthenol")
    assert p.tokens == ["Aqua", "Glycerin", "Panthenol"]


def test_chemical_comma_not_split():
    p = parse_label("Aqua, 1,2-Hexanediol, Toluene-2,5-Diamine, Glycerin")
    assert p.tokens == ["Aqua", "1,2-Hexanediol", "Toluene-2,5-Diamine", "Glycerin"]


def test_html_entities():
    p = parse_label("Aqua&amp;quot;, Glycerin&gt;, Panthenol")
    assert "Glycerin" in [t.strip('>",') for t in p.tokens]


def test_bracket_may_contain():
    p = parse_label("Aqua, Mica [+/- CI 77891, CI 77491]")
    assert p.tokens[:2] == ["Aqua", "Mica"]
    # the point of the test: the colorants land in may_contain, not tokens
    assert [t.strip("[] ") for t in p.may_contain] == ["CI 77891", "CI 77491"]


def test_bare_trailing_percentage():
    p = parse_label("Aqua, Niacinamide 10%, Ascorbic Acid 15 %, Glycerin")
    assert p.tokens == ["Aqua", "Niacinamide", "Ascorbic Acid", "Glycerin"]
