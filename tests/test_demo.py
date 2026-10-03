"""Exercise the public entry point and the synthetic-data boundary."""

import json
from pathlib import Path
import subprocess
import sys

from tersena.fixtures import demo_flags, demo_kb

ROOT = Path(__file__).resolve().parents[1]


def run_demo(*args):
    proc = subprocess.run(
        [sys.executable, "-B", str(ROOT / "examples/demo.py"), *args],
        cwd=ROOT, text=True, capture_output=True, check=True, timeout=15,
    )
    return json.loads(proc.stdout)


def test_demo_matches_and_separates_optional_colorants():
    result = run_demo()
    assert len(result["examples"]) == 5
    examples = result["examples"]
    assert examples[0]["ingredients"][1]["token"] == "1,2-Hexanediol"
    assert examples[1]["ingredients"][1]["method"] == "fuzzy"
    assert examples[1]["ingredients"][2]["method"] == "none"
    assert len(examples[2]["ingredients"]) == 1
    assert len(examples[2]["may_contain"]) == 2
    assert examples[2]["may_contain"][1]["matched_name"] == "CI 77891"


def test_demo_rule_is_explicitly_synthetic_and_preserves_scope():
    result = run_demo("Glycerin, Demo Material")
    entries = result["examples"][0]["ingredients"][1]["illustrative_rules"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["source"].startswith("synthetic:")
    assert "not a regulation" in entry["notice"]
    assert [r["min_pct"] for r in entry["rules"]] == [2.5, 4.0]
    assert [r["applies_to_example_product_type"] for r in entry["rules"]] == [True, False]
    assert "EU Reg." not in json.dumps(result)
    assert "citation" not in json.dumps(result)


def test_fixture_is_nonempty_and_has_no_regulatory_citation_generator():
    kb, flags = demo_kb(), demo_flags()
    assert len(kb.index) == 12
    assert len(flags.entries) == 1
    assert flags.entries[0].annex == "SYNTHETIC"
    assert not hasattr(flags.entries[0], "citation")
    assert not flags.flags_for(kb.lookup("Glycerin")[0])
    assert len(flags.flags_for(kb.lookup("Demo Material")[0])) == 1
