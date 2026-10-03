# Verification of the prepared extraction

Verified locally on 2026-10-03. The source-checkout checks below made no network requests. An independent installation check downloaded public Python build tools into a disposable environment. No paid API call, commit, push, or remote creation was performed.

The source project's existing Python environment supplied Python 3.11.14 and pytest 9.1.1. All imports of Tersena resolved to this extraction's `src` directory. Bytecode, pytest's cache provider, and automatic third-party pytest plugins were disabled. This first pass tests the source-checkout path. The wheel and generated console-script entry point were checked separately as described below.

From this directory, the following command ran with `SOURCE_PYTHON` pointing to that existing interpreter:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONNOUSERSITE=1 "$SOURCE_PYTHON" -B -m pytest -p no:cacheprovider -q
```

Result: **98 passed in 0.25 seconds**. Tests cover parser edge cases and a bounded process regression for pathological whitespace; normalization; matching and concurrent cache eviction; synthetic rule clauses and scope selection; and complete CLI output. The three CLI tests verify nonempty fixtures, unknown tokens, optional colorants, synthetic rule labeling, and the absence of a legal citation generator.

The following commands also completed successfully with the available system Python:

```sh
python3 -B examples/demo.py 'Glycerin, Demo Material'
PYTHONPATH=src python3 -B -m tersena 'Aqua, Niacinamde, Unknown Example'
```

A separate local verification parsed every Python file with `ast.parse`, confirmed the four unchanged engine modules byte-for-byte against the source, and checked all source hashes in `provenance.json`. The original repository remained clean at `7abf4b377edf3d8f7444701e39db6ccc99ab17db`; `git diff --exit-code` returned zero.

`SHA256SUMS` covers every prepared file except itself. The historical full-corpus benchmark was not rerun. No production data or complete-database claim is represented by these 98 synthetic-input tests.

## Independent installation check

A reviewer built and installed the wheel in an isolated copy and a fresh Python 3.14.8 virtual environment, using setuptools 84.0.0, wheel 0.48.0, and packaging 26.3. Those public build tools were downloaded; the package build and install used no index or dependency resolution. The following commands passed:

```sh
python -m pip wheel --no-build-isolation --no-deps --no-index --wheel-dir dist .
python -m pip install --no-index --no-deps dist/tersena_engine-0.1.0-py3-none-any.whl
tersena-demo 'Glycerin, Demo Material'
python -B -m tersena 'Aqua, Niacinamde, Unknown Example'
```

The last two commands ran from outside the source checkout with no `PYTHONPATH`; the imported package resolved to the fresh environment's `site-packages`. CI is configured to install the package, run pytest, and exercise both demo entry paths. The hosted CI job has not run.
