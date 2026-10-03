# Development history

The standalone public repository began with an October 3, 2026 snapshot. It also contains 2 filtered development commits from August 11 and August 25, 2026. Their author and committer dates come from the original repository; they describe development dates, not earlier public releases.

The retained history covers four complete modules (`parser.py`, `matcher.py`, `rules.py`, and `producttypes.py`) and the two original parser test files. One commit introduces them; the other records the original package rename and updated test imports. The source has no intervening changes to those modules. The smaller `kb.py` and `flags.py` extracts, synthetic fixtures, demo, packaging, and other adapted tests belong to the October 3 public snapshot.

Historical file contents and the original package rename are preserved. Commit messages describe the retained changes; unrelated operational instructions are omitted.

Each imported commit changes a retained file. Commits outside that scope and merges with no additional retained changes are omitted. Original author and committer identities and timestamps are preserved. Filtering changes commit IDs; [history-map.json](history-map.json) maps every retained source commit to its imported counterpart.

The import joins the historical branch to the existing public history with an October 3 merge. Existing public commits and the current code remain intact. Older snapshots may depend on parts of the original application that are outside this extraction; they were inspected as history, not built or tested as standalone packages.

[Browse the imported history](https://github.com/AndrewFribush/tersena-engine/commits/0faaf660622425601b534af9484da9f84d77c477). The extraction provenance describes the current runnable package.
