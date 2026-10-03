"""Original normalization regressions, without production-KB fixtures."""

from tersena.kb import norm


def test_norm_precomposed_accents():
    assert norm("Glycérin") == "GLYCERIN"


def test_norm_combining_accents():
    # 'e' + U+0301 combining acute — same visual string, different codepoints
    assert norm("Glycérin") == "GLYCERIN"


def test_norm_en_and_em_dashes():
    assert norm("1,2–Hexanediol") == "1,2-HEXANEDIOL"  # en dash
    assert norm("A—B") == "A-B"


def test_norm_curly_apostrophe():
    assert norm("D’Orange") == "D'ORANGE"


def test_norm_footnote_symbols_removed():
    assert norm("GLYCERIN*") == "GLYCERIN"
    assert norm("ALOE VERA†") == "ALOE VERA"  # dagger
    assert norm("PANTHENOL‡") == "PANTHENOL"


def test_norm_superscript_footnotes_removed():
    # Superscript footnote marks are stripped BEFORE NFKD (which would
    # otherwise turn them into plain digits).
    assert norm("GLYCERIN¹") == "GLYCERIN"
    assert norm("AQUA²³") == "AQUA"


def test_norm_plain_digits_preserved():
    # Plain digits are load-bearing: name+digit is often a different
    # substance ("POLYQUATERNIUM-1" vs "POLYQUATERNIUM-10").
    assert norm("POLYQUATERNIUM-1") == "POLYQUATERNIUM-1"
    assert norm("CI 77891") == "CI 77891"


def test_norm_whitespace_collapse():
    assert norm("  aqua \t\n glycerin  ") == "AQUA GLYCERIN"


def test_norm_trailing_punctuation_stripped():
    assert norm("AQUA.") == "AQUA"
    assert norm("AQUA ;,") == "AQUA"


def test_norm_empty_and_punctuation_only():
    assert norm("") == ""
    assert norm(" .,;: ") == ""


def test_norm_idempotent():
    once = norm("Glycérin*†  – test’s")
    assert norm(once) == once
