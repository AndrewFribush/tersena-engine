# Tersena engine

A runnable extraction of the parser, matcher, and restriction-rule parser behind [Tersena](https://tersena.com), Andrew Fribush's cosmetic ingredient intelligence project. It shows how the engine handles chemical commas, botanical parentheses, OCR errors, optional colorants, and ambiguous product scopes.

The four engine modules are unchanged from the source project. The knowledge-base types use an explicit miniature fixture; production loaders, datasets, API, and commerce integrations are excluded. Every example label is invented. Every rule is synthetic and illustrative, with no regulatory or safety meaning.

## Run offline

Python 3.11 or newer is sufficient; the demo has no third-party runtime dependencies or network calls.

```sh
python3 -B examples/demo.py
python3 -B examples/demo.py "Aqua, Niacinamde, Unknown Example"
PYTHONPATH=src python3 -B -m tersena "Glycerin, Demo Material"
```

The first command prints five examples as JSON. Output retains the matching method, unmatched tokens, optional colorants, and an algorithm score. That score is not a probability of correctness. The fictional `DEMO MATERIAL` illustrates lettered clauses, decimal commas, minimum and maximum sub-limits, and a product-type scope check against an example face cream. Its source identifier begins `synthetic:`.

## What to inspect

- `src/tersena/parser.py`: split ingredient lists while preserving commas inside chemical names and parentheses; avoid catastrophic regex backtracking.
- `src/tersena/matcher.py`: exact, parenthetical, slash, prefix, and fuzzy matching, with bounded cache eviction.
- `src/tersena/rules.py`: extract structured limits while retaining conditions and flagging language the parser does not model.
- `src/tersena/producttypes.py`: apply product-type hints and exclusions, returning unknown when the text is insufficient.
- `tests/`: extracted behavioral regressions plus a CLI check for the synthetic-data boundary.

## Evidence and limits

The original project recorded a historical evaluation on 15,594 [Open Beauty Facts](https://world.openbeautyfacts.org/) labels with at least three parsed tokens: 264,982 of 301,804 tokens matched (87.80%); 7,042 labels fully matched (45.2%). Those are coverage counts from its full knowledge base, not independently adjudicated accuracy, held-out validation, or results reproduced by this extraction. The snapshot hashes needed for a fully reproducible corpus benchmark are not in that report. This demo makes no comparable coverage claim.

The miniature fixture contains 12 identities and one invented rule. It omits production aliases and taxonomy, so many ordinary ingredients remain unmatched. Prefix and fuzzy matches are heuristic; they can select the wrong identity. Parsing a limit or failing to find a flag does not establish product compliance or safety. The original parser also preserves an unclosed parenthesis as one remaining token. These boundaries are visible in the tests and output.

## Checks

With pytest already available in the selected Python environment:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -p no:cacheprovider -q
```

Tests run entirely on synthetic inputs. No full-database invariant tests are included. See [PROVENANCE.md](PROVENANCE.md) for the exact extraction changes and [VERIFICATION.md](VERIFICATION.md) for commands actually run on this prepared copy.

Copyright 2026 Andrew Fribush. All rights reserved; no open-source license is granted. See [NOTICE](NOTICE).
