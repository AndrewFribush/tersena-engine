# Tersena engine

Cosmetic ingredient lists look easy to parse until a comma turns out to be part of an ingredient. I built the engine behind [Tersena](https://tersena.com) to handle the less cooperative cases: chemical names, botanical parentheses, OCR errors, optional colorants, and restrictions whose meaning depends on the product.

Tersena is my cosmetic ingredient intelligence project. This repository contains its parser, matcher, and restriction-rule parser in a runnable extraction. The four engine modules are unchanged from the source project; the knowledge-base types use a hand-authored synthetic fixture. Production loaders, datasets, API, and commerce integrations are excluded.

## Where the work is

- `src/tersena/parser.py` splits ingredient lists while preserving commas inside chemical names and parentheses, with a regression check for catastrophic regex backtracking.
- `src/tersena/matcher.py` tries exact, parenthetical, slash, prefix, and fuzzy matches. Its cache has bounded eviction, including under concurrent access.
- `src/tersena/rules.py` extracts structured limits, keeps the attached conditions, and flags language the parser does not model.
- `src/tersena/producttypes.py` applies product-type hints and exclusions. It returns unknown when the text is insufficient.
- `tests/` contains the extracted behavioral regressions and CLI checks for the synthetic-data boundary.

The prepared extraction passed 98 tests on synthetic inputs, covering pathological whitespace, normalization, matching, concurrent cache eviction, rule clauses, scope selection, and CLI output. The wheel was also built and installed in a fresh environment; both the console-script and module entry points ran successfully. [VERIFICATION.md](VERIFICATION.md) records the environments and commands actually run.

## Run offline

Python 3.11 or newer is sufficient; the demo has no third-party runtime dependencies or network calls.

```sh
python3 -B examples/demo.py
python3 -B examples/demo.py "Aqua, Niacinamde, Unknown Example"
PYTHONPATH=src python3 -B -m tersena "Glycerin, Demo Material"
```

The first command prints five examples as JSON. Output retains the matching method, unmatched tokens, optional colorants, and an algorithm score. That score is not a probability of correctness. The fictional `DEMO MATERIAL` illustrates lettered clauses, decimal commas, minimum and maximum sub-limits, and a product-type scope check against an example face cream. Its source identifier begins `synthetic:`.

## Checks

With pytest already available in the selected Python environment:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -p no:cacheprovider -q
```

## What the numbers mean

The original project recorded a historical evaluation on 15,594 [Open Beauty Facts](https://world.openbeautyfacts.org/) labels with at least three parsed tokens: 264,982 of 301,804 tokens matched (87.80%); 7,042 labels fully matched (45.2%). These are coverage counts from the full knowledge base, not independently adjudicated accuracy or held-out validation. The report lacks the snapshot hashes needed to reproduce the corpus benchmark, and this extraction does not reproduce those results or make a comparable coverage claim.

The demo fixture has 12 identities and one invented rule. It omits production aliases and taxonomy, so many ordinary ingredients remain unmatched. Every example label is invented; every rule is synthetic and illustrative, with no regulatory or safety meaning. Full-database invariant tests are excluded.

Prefix and fuzzy matches are heuristic and can select the wrong identity. Parsing a limit or failing to find a flag does not establish product compliance or safety. The parser also preserves an unclosed parenthesis as one remaining token. The tests and output leave these awkward cases visible.

See [PROVENANCE.md](PROVENANCE.md) for the exact extraction changes.

Copyright 2026 Andrew Fribush. All rights reserved; no open-source license is granted. See [NOTICE](NOTICE).

[Development history](HISTORY.md) preserves the original changes to the extracted modules and parser tests.
