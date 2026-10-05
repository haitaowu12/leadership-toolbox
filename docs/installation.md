# Install, update and restore · 0.2.0

## Obtain reviewed source

This draft is available in [PR #1](https://github.com/haitaowu12/leadership-toolbox/pull/1), on [feat/standalone-leadership-skill](https://github.com/haitaowu12/leadership-toolbox/tree/feat/standalone-leadership-skill). It does not promise a published release archive. Inspect the PR and its checks before installing. Record the exact commit you reviewed; a branch can advance.

To obtain that branch with Git:

`git clone --branch feat/standalone-leadership-skill --single-branch https://github.com/haitaowu12/leadership-toolbox.git`

Then enter the repository and run `git rev-parse HEAD` to record the source revision. Alternatively, open the verified branch page and use GitHub's Code → Download ZIP, then extract it. A GitHub source ZIP has no generated release manifest yet.

From the source root run `python3 scripts/validate.py`, `python3 -m unittest discover -s tests -v`, and `python3 scripts/build_release.py`. The last command creates `dist/leadership-toolbox-0.2.0.zip` with only reviewed paths from `RELEASE_FILES.txt` and a SHA-256 manifest. Validate the extracted archive before installation. Checksums establish byte integrity, not privacy, source accuracy or real-world effectiveness.

## Install the complete folder

Run `python3 scripts/install.py --dest /your/host/skills/leadership-toolbox`, replacing the placeholder with the host's documented skill directory. The helper needs Python 3.10+ and only the standard library. Manual installation is also supported: copy the entire `skills/leadership-toolbox` folder, including references, templates, schemas, scripts and notices. Reading the skill itself requires no Python.

Use your host's current documented discovery path. Host-neutral means no mandatory provider, connector or hardcoded personal path; it does not mean every host was tested. After installation, verify that the host discovers the intended name/version once and can load a referenced card. If the host does not support discovery, give it the entrypoint and relevant references manually. Do not claim activation from a successful file copy alone.

## Updates and backup location

Install the new complete package to the same explicit destination; never overlay a partial folder. The helper checks and stages the incoming package, moves the previous complete skill to a unique backup, then replaces it. It refuses symlinks and misplaced private profile/history. Separately stored user state is untouched; migration is an independent explicit action in [personal data](personal-data.md).

Staging and retained backups are outside the destination's discovery directory. The default is a sibling `.leadership-toolbox-backups` directory: for destination `/your/host/skills/leadership-toolbox`, use `/your/host/.leadership-toolbox-backups`. If that location falls inside another discovery root configured by your host, supply `--backup-dir /your/separate-package-backups` outside every discovery root, on the same filesystem. The installer cannot inspect all host configurations. Cross-filesystem rename failure is surfaced rather than silently replacing data.

## Restore

Use the exact backup path printed by the helper:

`python3 scripts/install.py --dest /your/host/skills/leadership-toolbox --restore /your/host/.leadership-toolbox-backups/.leadership-toolbox.backup-REPLACE`

For a custom location, pass the same `--backup-dir` when restoring. Restoration copies a complete backup and preserves the replaced version as another backup; it does not roll back practice history. Review schema compatibility before using an older helper. Legacy adjacent backups are accepted as restore sources but no new ones are created there. Move any legacy backups outside discovery after review; do not assume hidden folders are ignored by every host.

## Verification boundary

[Validation](validation.md) records exact revision/check evidence. Filesystem and archive tests cannot establish every host's discovery semantics, accessibility or workplace effectiveness. No installation, update or source download grants permission for external actions.
