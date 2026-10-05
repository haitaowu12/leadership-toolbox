# Validation and limits · 0.2.0 draft

## Current expansion

This version expands the catalog to 32 methods, adds adaptive quick/deep interviewing, eight mixed-type context dimensions, explicit matching profiles and metric contracts, and removes the fixed 14-method implementation limit. It also moves installer staging/backups outside the immediate discovery root and adds regression coverage.

At the time of this draft commit, the new 31-test suite and structural checks are authored but not yet executed for this revision. A pinned, read-only GitHub Actions workflow runs validation, tests and archive construction; an existing workflow file is not a passing run. Exact executed results will be recorded after the remote commit is checked. No local computer or assistant-host activation is claimed for this expansion.

## Historical 0.1.0 evidence

The earlier package snapshot at [c11e9f8](https://github.com/haitaowu12/leadership-toolbox/commit/c11e9f80154542ba3bdcdccdd6b86cf801f984ee) recorded 56 reviewed files, 14 methods and 14 passing functional tests in an isolated Mac filesystem using Python 3.13.5. Those results do not validate the later expansion.

The [eight-case report](evaluations/forward-2026-10-05.md) and [seven-case extension](evaluations/forward-extension-2026-10-05.md) retain 15 model-generated prompt/response executions. The evaluator also assessed its outputs, so these are not blinded independent scoring or human research. [Challenge coverage](evaluations/challenge-coverage.md) records gaps. These reports are historical artifacts; exact generating model/settings and pre-generation package hashes were not retained in a reproducible manifest. Their presence in c11e9f8 identifies the published snapshot, not proof of the exact model input bytes. Do not imply stronger provenance.

## Sources and rights

Public primary-source review supports method descriptions, source types and reuse cautions. The source register identifies bounded claims and editorial transfers. External URLs can change; structural local-link checks do not certify every current page, asset or licence. No provider assessment instrument, article, image or proprietary template is bundled. Source review is not comprehensive legal clearance.

## Reproduce

From repository root: `python3 scripts/validate.py`, `python3 -m unittest discover -s tests -v`, `python3 scripts/build_release.py`. Tests use only the standard library. The source/privacy scan is heuristic plus an explicit allowlist; it cannot identify every possible confidential sentence. A later fix does not remove earlier Git history.

A structural pass does not establish method effectiveness, correct matching in all situations, universal host compatibility or safe deployment in regulated work. Workplace outcomes, live discovery across hosts, accessibility of actual platforms and the new interview's empirical usefulness remain unvalidated. Owner review is required before merge or release; no site/service is deployed.
