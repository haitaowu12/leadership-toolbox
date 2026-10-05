# Private profile and practice history

The shared core contains schemas and blank templates, not user data. Use a separate private folder outside the installed skill and any Git checkout. A blank v2 profile (`schema_version: 2`, empty `goals` and `preferences`) works. No profile is required to ask for help.

From the installed skill, run `python3 scripts/state.py init --data-dir /your/private-folder`. The helper creates a private profile and empty history without overwriting existing data. `validate` checks the bundled interchange contract and duplicate practice IDs. Keep minimal, de-identified records; access to this directory is your host/OS responsibility.

Use `migrate` with the same explicit directory for a v1→v2 profile update. It adds empty preferences, retains goals and unknown/custom fields, saves a byte-preserving backup plus a hash receipt, and leaves `practice.jsonl` unchanged. Unsupported versions or conflicting fields fail without mutation. Package versions and state schema versions are separate.

Use `rollback --backup /your/private-folder/backups/profile-v1-REPLACE.json` only for the matching migration. The helper refuses if the current profile differs from the migrated result or the backup changed. Preserve and reconcile newer edits rather than forcing data loss. Practice history remains unchanged. Backups contain private data; never commit/upload them with the package.

No data is sent to a service. Installing the shared package does not initialise, inspect or migrate private history. Read the [bundled guidance](../skills/leadership-toolbox/references/user-data.md), [profile schema](../skills/leadership-toolbox/schemas/profile-v2.schema.json) and [practice schema](../skills/leadership-toolbox/schemas/practice-v1.schema.json) when using machine-readable records.
