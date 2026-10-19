# Assignment-selection issue 3

## Goal
Fix integer distance precision and open a draft PR without merging or changing Propstore pins/source.

## State
Separate worktree/branch fix/integer-distance-issue-3, based on published d855496. Global instructions and repo source/tests/CI read; no local AGENTS.md/CLAUDE.md found. Focused dependency fixes and regression tests explicitly authorized by parent delegation.

## Smallest change and decision
About four source lines: subtract int/int endpoints exactly, then convert the difference to the existing float distance type. Preserve float/numeric-coercion/categorical behavior for all other input pairs. About forty regression-test lines cover adjacent signed-64-bit integers and SIGMA's unique majority winner. No new metric policy or broader numeric redesign.

## Next step
The new tests failed in all six cases before the change (four unit-distance cases and two SIGMA winner cases). After the four-line source fix, the same command passed all six in 0.49s:

`uv run --no-project --offline --python C:/Users/Q/code/assignment-selection/.venv/Scripts/python.exe python -B -m pytest -p no:cacheprovider tests/test_integer_distances.py -q`

PYTHONPATH selected this worktree's src; UV_CACHE_DIR selected its isolated cache. No dependencies installed. Full suite and typing will run in PR CI.

Q separately approved the citation-only edit to issue #3. Replaced only the Propstore solve-owner line anchor 265 with 236, fetched the issue, and verified exact body equality with that one substitution.

Published draft PR https://github.com/ctoth/assignment-selection/pull/4 at source commit 175d32533dc233cb25969154b9f8ca383a996294. Fetched the PR and verified its draft status and exact head. CI run 39339378017 passed all typing/test jobs on Python 3.11, 3.12, and 3.13. No merge or ready transition performed. This final note update records that outcome; verify the note-only final head before handoff.
