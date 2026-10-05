# Install, update and restore · 0.2.0

## Cloud upload without a local install

A single-skill ZIP is provided separately from the full source archive. Claude web is a currently documented cloud-host route; no Claude upload or live activation was executed in this project. Host/account policy can still block upload.

1. Open a successful direct-head run under [GitHub Actions](https://github.com/haitaowu12/leadership-toolbox/actions/workflows/validate.yml). Confirm its commit is the revision you reviewed. Under Artifacts, download `leadership-toolbox-<full commit SHA>`.
2. Extract that outer Actions download. Keep `leadership-toolbox-0.2.0.zip` for source review. The file to upload is **`leadership-toolbox-skill-0.2.0.zip`**, containing `leadership-toolbox/SKILL.md` and all references, templates, scripts, schemas and notices.
3. In Claude web, enable Code execution and file creation under Settings → Capabilities. Organization settings and your role must permit custom skills.
4. Go to Customize → Skills → + → Create skill → Upload a skill. Choose the single-skill ZIP and enable it.
5. Start a new chat: “Use leadership-toolbox. Explain GROW using the bundled L02 card, include an underlying source link and one practical limitation.”
6. Check the host's skill/file-use evidence for version 0.2.0 and the referenced card. Then try the [quick and probing examples](quick-start.md). A plausible answer or successful upload alone does not prove activation.

These steps were checked against current [Claude use guidance](https://support.claude.com/en/articles/12512180-use-skills-in-claude), [custom-skill requirements](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills), and [cloud execution guidance](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude) on 2026-10-05. This route needs no API key, Python on your computer or Codex task. Cloud networking and persistent private state are not guaranteed. Enabled account skills may also sync to separately used Claude Code on the same account; consult the host's current controls.

[GitHub artifact downloads](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts) require sign-in/read access and expire after 30 days here. They are checked builds, not published GitHub Releases. Use the source route below when an artifact is unavailable.

## Obtain and verify source

Open the [repository](https://github.com/haitaowu12/leadership-toolbox), choose the reviewed main revision, then Code → Download ZIP and extract it. Or use Git:

`git clone https://github.com/haitaowu12/leadership-toolbox.git`

Enter the repository and record `git rev-parse HEAD`. A branch can advance; keep the exact revision you reviewed. While a change is under review, [PR #1](https://github.com/haitaowu12/leadership-toolbox/pull/1) identifies the proposed branch rather than implying it is already on main.

From the source root, with Python 3.10+:

- `python3 scripts/validate.py`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/build_release.py`

The builder creates both ZIPs and `dist/SHA256SUMS`. The source ZIP includes a reviewed-file manifest; the skill ZIP has its own skill-relative manifest. Repeat builds are byte-identical in the tested runtime; cross-Python/zlib byte identity is not promised. Checksums verify bytes, not source authenticity, privacy or effectiveness. A GitHub source download has no generated manifest until you build it.

## Install the complete folder

For a filesystem-based host, follow its current documented discovery path. Run:

`python3 scripts/install.py --dest /your/host/skills/leadership-toolbox`

Replace the placeholder with an explicit destination. The helper uses Python's standard library. Manual installation is also supported: copy the entire `skills/leadership-toolbox` folder. Reading the skill requires no Python. Hosts that cannot discover skills can read the entrypoint and linked files manually; that is manual use, not registration.

Verify that the host discovers the intended name/version once and can read a reference. File copy does not establish host activation. This project has not tested every host, operating system or UI.

## Update and restore

Install the new complete package to the same destination; do not overlay a partial folder. The helper validates incoming baseline files, catalog references and local Markdown dependencies, stages the incoming package, retains the previous skill, then replaces it. A damaged existing installation can be repaired after safety checks; its outgoing bytes are retained, but an incomplete backup is not accepted as a restore source. It rejects symlinks, unsafe referenced paths, known private-state names and environment files. This is a bounded completeness/privacy check, not a full security audit.

Backups and staging are outside the immediate discovery directory. For destination `/your/host/skills/leadership-toolbox`, the default is `/your/host/.leadership-toolbox-backups`. If another discovery root includes that location, use `--backup-dir /your/separate-package-backups`, outside every discovery root and on the same filesystem. The helper cannot inspect all host configurations.

Use the exact printed backup path to restore:

`python3 scripts/install.py --dest /your/host/skills/leadership-toolbox --restore /your/host/.leadership-toolbox-backups/.leadership-toolbox.backup-REPLACE`

For a custom backup location, pass the same `--backup-dir`. The restored package is copied and the version it replaces is also retained. External private state is untouched; see [personal data](personal-data.md) for separate migration and schema compatibility.

Caught replacement failures restore the old package where possible. The two renames are not crash-atomic: a process/power failure between them may leave the destination absent and the complete previous version in the backup directory. Inspect the printed/configured backup directory and restore a reviewed backup. Do not delete it while recovering. Legacy adjacent backups can be restore sources but new backups are never created there.

## Verification boundary

[Validation](validation.md) records package checks and model-output tests separately. Clean archive installation, update and restore in CI do not establish cloud-account upload, host discovery, every operating system, or workplace benefit. No installation grants permission to message people, change obligations or collect private records.
