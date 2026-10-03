"""Offline demo: python -m tersena ["ingredient label"]."""

from dataclasses import asdict
import json
import sys

from .fixtures import EXAMPLE_LABELS, demo_flags, demo_kb
from .matcher import Matcher
from .parser import parse_label
from .producttypes import rule_applies, tags_for
from .rules import parse_entry


def main() -> None:
    labels = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else EXAMPLE_LABELS
    matcher, flags = Matcher(demo_kb()), demo_flags()
    product_type = "leave-on face cream"

    def matches(tokens):
        output = []
        for match in matcher.match_all(tokens):
            item = {
                "token": match.raw, "method": match.method,
                "matched_name": match.matched_name,
                "match_score": match.score,
                "illustrative_rules": [],
            }
            for record in match.records:
                for entry in flags.flags_for(record):
                    item["illustrative_rules"].append({
                        "source": f"synthetic:{entry.ref_no}",
                        "notice": "Invented example, not a regulation.",
                        "rules": [
                            {**asdict(rule), "applies_to_example_product_type":
                             rule_applies(rule.product_type, tags_for(product_type))}
                            for rule in parse_entry(entry)
                        ],
                    })
            output.append(item)
        return output

    result = []
    for label in labels:
        parsed = parse_label(label)
        result.append({
            "label": label, "ingredients": matches(parsed.tokens),
            "may_contain": matches(parsed.may_contain),
        })
    print(json.dumps({
        "notice": "Synthetic fixtures only. No regulatory or safety conclusions.",
        "example_product_type": product_type,
        "match_score_note": "Algorithm score, not a probability of correctness.",
        "examples": result,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
