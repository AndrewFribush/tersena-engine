# Source and extraction

This showcase derives from Andrew Fribush's private Tersena (`ingredientcheck`) repository at commit `7abf4b377edf3d8f7444701e39db6ccc99ab17db`. `provenance.json` records SHA-256 hashes of the source files inspected during extraction. `SHA256SUMS` identifies this prepared copy's files; it is not a signature or a permission grant.

`parser.py`, `matcher.py`, `rules.py`, and `producttypes.py` are byte-identical to their source counterparts. Their comments describe the original domain; the demo supplies only synthetic fixtures.

`kb.py` retains the source's `norm`, `_TRUNCATED_RE`, `Record`, and `KB`, with their required imports. It omits all aliases, taxonomy, compact-index loading, and raw-data loading. `flags.py` retains the original `AnnexEntry` dataclass fields, `_CAS_RE`, and `FlagIndex.flags_for`. It omits file loading, statutory meanings, allergen/exception properties, and the regulatory citation generator. Callers construct both indexes explicitly.

The parser test files are copied intact. Normalization tests are selected unchanged from `test_adversarial_kb.py`. Matcher tests use the new fixture; four tests requiring production aliases/taxonomy are omitted, and the cache regression's unused CAS field is empty. Synthetic rule and product-type tests are selected from `test_adversarial_rules.py`; their entry category changes from `III` to `SYNTHETIC`. The real-corpus fixture and two corpus invariant checks are omitted, avoiding empty-input passes. No remaining acceptance assertion is relaxed to accommodate an algorithm change.

The fixture, demo CLI, example launcher, CLI-boundary tests, packaging, and showcase documentation are new extraction scaffolding. Fixture records use familiar names solely to exercise grammar; metadata is empty, and no third-party database rows were copied. `DEMO MATERIAL` and all demonstrated rules are invented. The CLI emits synthetic identifiers and does not emit legal citations. The original regulatory properties are unavailable in this extraction.

The historical evaluation paragraph summarizes only aggregate counts from the original `data/eval_report.md`, whose hash is recorded. That report was not copied, and its underlying Open Beauty Facts data, unmatched-label examples, and mixed-source knowledge base were not extracted. This is attribution for a historical observation, not a freshly reproduced result.

No production data, customer catalogs, retailer lists, credentials, deployments, source-repository history, or private operations documents are included. Source availability does not grant an open-source license; see NOTICE.
