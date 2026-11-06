# Working in Leadership Toolbox

Keep the shared core generic. Do not commit real participant stories, profiles, practice logs, confidential examples, credentials or local machine paths. Use explicit public sources and original explanations; retain required attribution and per-file licence boundaries.

Preserve stable method IDs and schema versions. Change methods through a draft PR, update the changelog and source notes, and state whether validation is structural, model-executed or observed in human use. Tests cannot establish leadership effectiveness.

Run `python3 scripts/validate.py` and `python3 -m unittest discover -s tests -v` before proposing a release. Build archives with `python3 scripts/build_release.py`; its reviewed allowlist excludes local data and repository history. Do not merge or deploy without the owner's approval.

## Publication

Firebase Hosting is the primary destination for future public releases: https://leadership-toolbox.web.app/. Run `python3 scripts/validate.py` and `python3 -m unittest discover -s tests -v`, then `python3 scripts/build_pages.py`. Publish only the reviewed `build/pages/` catalogue and archives.

Deploy from the repository root with `firebase deploy --only hosting --project tony-wu-projects`. The checked-in `firebase.json` pins this site and its public output. Keep the shared project on the no-cost Spark plan. The `Firebase Hosting` workflow publishes successful `main` revisions after checks; pull requests do not deploy. Google federation and repository variables must be configured before it is active; retain the existing hosts unless their retirement is requested. Exercise the main journey and any worker, download or nested page on the published address.
