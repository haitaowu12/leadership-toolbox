# Validation and limits · 2026-10-05

Official skill metadata validation: passed. Local structural validation: 56 reviewed files and 14 method IDs passed. Standard-library functional tests: 14 passed.

## Evidence levels

- Structural checks: skill metadata, JSON, complete catalog, local Markdown targets and an explicit public release allowlist.
- Functional checks: fresh extracted install, replacement/restoration, separate state preservation, v1→v2 migration and guarded rollback; symlink, invalid/unsupported state and misplaced-private-data refusals.
- Model-executed forward evaluation: [eight fresh requests and actual responses](evaluations/forward-2026-10-05.md), generated and executed by an evaluator who did not read author examples or private context. Two pairs vary one consequential fact. The [extension](evaluations/forward-extension-2026-10-05.md) adds seven executions; 15 written cases passed their applicable textual inspection with no demonstrated routing/safety defect. Lookup-format and specialist-source boundaries were clarified. The [eight-area challenge coverage](evaluations/challenge-coverage.md) records what was exercised and exact-prompt/configuration gaps.

The evaluator both produced and assessed responses, so this is not blinded scoring or an independent replication. The report retains all cases and limitations rather than presenting a percentage as a success probability. A separate model generation is not human field evidence.

## Tested-host boundary

The standard-library helpers and package operate in isolated Mac filesystem folders using Python 3.13.5, including a fresh release extraction and actual install/state/update CLI invocations. Live host discovery/activation, other assistant hosts, actual conversations and lasting workplace improvements have not been tested. No UI/website was created or deployed.

Source and licence decisions incorporate separately supplied public research and primary-source checks. External URLs are references, not bundled content; local-link checks do not certify every external site’s future availability. The Mac in-app browser was unavailable for a separate final live link audit. No provider assessment instrument, image or article is bundled.

## Reproduce

From repository root: `python3 scripts/validate.py`, `python3 -m unittest discover -s tests -v`, `python3 scripts/build_release.py`. The official skill-creator validator may use its own development dependency (PyYAML); consuming this skill does not. Run results and commit identifiers accompany the draft PR.

No human effectiveness, universal host compatibility or complete legal clearance is claimed. Review and merge/release approval remain with the owner.
