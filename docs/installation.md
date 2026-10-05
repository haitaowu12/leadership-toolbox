# Install, update and roll back · 0.1.0

## Complete package

Download the archive from the reviewed PR/release, extract it and inspect `RELEASE_MANIFEST.json` and licence notices. From the extracted root, run `python3 scripts/validate.py`. The archive contains only paths in `RELEASE_FILES.txt`; it excludes repository history and private user data. The generated checksum manifest is for byte-integrity checks, not evidence of privacy or content quality.

Run `python3 scripts/install.py --dest /your/host/skills/leadership-toolbox`, replacing the placeholder with your host's documented local skill directory. The helper requires Python 3.10+ and uses only the standard library. Manual installation is also supported: copy the entire `skills/leadership-toolbox` folder, including references, templates, schemas, scripts and notices. Reading the skill needs no Python or runtime service.

For Codex, a user-level skill directory is commonly `~/.codex/skills/leadership-toolbox`; confirm your configured host path rather than assuming every host uses it. Hosts with `SKILL.md` discovery should discover the name/description; reload as required by that host. Other assistants can read the file manually. Host-neutral means no mandatory connector, provider or absolute path, not that every host was tested.

## Update

Install the reviewed new complete package using the same explicit destination. The helper stages the incoming folder and moves the old skill to a unique adjacent backup before replacing it. It refuses symlinks and private profile/history inside the old package; move misplaced data to a private location rather than losing it. Never overlay a partial folder onto an older version.

Updates replace only the shared skill. Your separately stored profile and practice history are untouched; migration is an explicit independent action described in [personal data](personal-data.md).

## Restore the earlier skill

Use the previous path printed by the helper: `python3 scripts/install.py --dest /your/host/skills/leadership-toolbox --restore /your/host/skills/.leadership-toolbox.backup-REPLACE`. The restore stages a complete backup and preserves the replaced skill as another backup. It does not roll back practice records. Review/reconcile profile schema compatibility before using an older helper.

## Tested boundary

Fresh extraction, standard-library helper execution, complete folder replacement/restoration, local links and preservation of separate user state are tested in isolated local folders. Live host discovery/restart, non-Codex hosts, platform-specific access controls and human effectiveness are not certified by those tests. See [validation](validation.md).
