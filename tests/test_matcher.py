"""Original matcher checks against the explicit synthetic fixture KB."""

import threading
import pytest
from tersena.kb import KB, Record
from tersena.matcher import Matcher
from tersena.fixtures import demo_kb


@pytest.fixture(scope="module")
def matcher():
    return Matcher(demo_kb())


def test_exact(matcher):
    m = matcher.match("GLYCERIN")
    assert m.method == "exact"
    assert m.records[0].inci_name == "GLYCERIN"


def test_case_and_accents(matcher):
    assert matcher.match("glycérin").method in ("exact", "fuzzy")
    assert matcher.match("Aqua").method == "exact"


def test_water_resolves(matcher):
    # CosIng carries both WATER and AQUA as separate active records; either is
    # a correct match here — canonicalizing them is the normalization layer's job.
    m = matcher.match("Water")
    assert m.method == "exact"
    assert m.records[0].inci_name in ("AQUA", "WATER")


def test_slash_trilingual(matcher):
    m = matcher.match("Aqua/Water/Eau")
    assert m.method in ("exact", "slash")
    assert any(r.inci_name == "AQUA" for r in m.records)


def test_slash_inside_real_inci_name(matcher):
    m = matcher.match("Acrylates/C10-30 Alkyl Acrylate Crosspolymer")
    assert m.method == "exact"


def test_botanical_parenthetical(matcher):
    m = matcher.match("Butyrospermum Parkii (Shea) Butter")
    assert m.method in ("exact", "paren")
    assert "BUTYROSPERMUM PARKII" in m.records[0].inci_name


def test_colorant_parenthetical(matcher):
    m = matcher.match("Iron Oxides (CI 77491)")
    assert m.method in ("exact", "paren")


def test_fuzzy_typo(matcher):
    m = matcher.match("Niacinamde")  # missing 'i'
    assert m.method == "fuzzy"
    assert m.records[0].inci_name == "NIACINAMIDE"


def test_garbage_unmatched(matcher):
    assert matcher.match("xqzzt blorf").method == "none"


def test_cl_ocr_colorant(matcher):
    m = matcher.match("CL 77891")
    assert m.records and m.records[0].inci_name == "CI 77891"


def test_fuzzy_on_paren_stripped(matcher):
    m = matcher.match("Butyrospermum Parki (Shea) Butter")  # missing 'i'
    assert m.method == "fuzzy"
    assert m.records[0].inci_name == "BUTYROSPERMUM PARKII BUTTER"


def test_genus_species_prefix(matcher):
    m = matcher.match("Aloe Barbadensis")
    assert m.method == "prefix"
    assert m.records[0].inci_name.startswith("ALOE BARBADENSIS")


def test_prefix_not_single_word(matcher):
    # bare "Sodium" must NOT resolve to some arbitrary sodium salt
    assert matcher.match("Sodium").method == "none"


def test_cache_eviction_thread_safe(monkeypatch):
    # Regression: concurrent requests in FastAPI's threadpool share one
    # Matcher; eviction between a membership check and the read raised an
    # uncaught KeyError -> HTTP 500. Hammer a tiny cache from 8 threads
    # and assert nothing raises.
    kb = KB()
    kb.index["GLYCERIN"] = [
        Record(substance_id="s1", inci_name="GLYCERIN", item_type="chem",
               status="Active", cas_no="", description="",
               functions=(), restrictions=())
    ]
    m = Matcher(kb)
    monkeypatch.setattr(Matcher, "_CACHE_MAX", 20)
    errors: list[Exception] = []

    def worker(seed: int) -> None:
        try:
            for i in range(2000):
                m.match(f"token {seed} {i % 37}")  # unique misses fill the cache
                m.match("GLYCERIN")  # hot key read while others evict
        except Exception as e:  # noqa: BLE001 — any exception is the bug
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert not errors, f"cache race raised: {errors[:3]}"
