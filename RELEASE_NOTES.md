# v0.1.0

Initial standalone release: read-only symlink boundary, broken-target and special-file preflight. Root-relative text/JSON reports, conservative UNKNOWN status and 10,000-entry default cap. No copy/repair features.

Requires Python 3.10+. Run the single-file asset with `python3 copyboundary /path/to/project`. Exit codes: 0 no flagged risk, 1 review, 2 unknown. Read README safety and limitations before use. No successful-user-outcome claim; fixtures and local smoke tests establish implementation behavior only.
