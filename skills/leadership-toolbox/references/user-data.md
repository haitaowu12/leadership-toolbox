# Optional private context

A blank profile is sufficient. A host may use an explicitly authorised private folder to store goals/preferences in `profile.json` and practice observations in append-only `practice.jsonl`. Keep that folder outside the installed skill and any shared repository. Do not auto-discover other notes, workplace records or personal history.

Use the bundled [state helper](../scripts/state.py) only when the user asks to initialise, validate, migrate or restore data. It requires an explicit `--data-dir`. It does not send data, call APIs or change host settings. Read the [v2 profile schema](../schemas/profile-v2.schema.json) and [v1 practice schema](../schemas/practice-v1.schema.json) for the interchange contract. Schema versions are independent of package versions. Unknown fields are retained.

Commands: `python3 scripts/state.py init --data-dir /your/private-folder`; `validate`, `migrate`, and `rollback` use the same option. Rollback additionally needs `--backup` pointing to the migration backup. Paths here are placeholders to replace, never defaults to an existing personal location.

Migration from profile v1 to v2 adds an empty preferences object while retaining earlier fields and the complete practice file unchanged. Backups contain private data and belong in the same private folder. Rollback is refused if the current profile has changed since migration; reconcile newer changes rather than discarding them. Future unsupported versions fail without mutation. Installing/updating the shared skill never migrates user data automatically.

A practice record identifies method/package versions, prediction, observation, guardrail and review decision. Actual results may remain pending. Preserve declined, stopped and mixed outcomes. Do not mine history into generic cards without a separate explicit contribution and privacy review.
