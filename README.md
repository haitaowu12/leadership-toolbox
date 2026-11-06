# Leadership Toolbox

Practical help for your next conversation, decision, handoff or team improvement. A portable skill with 32 methods, an original public-source knowledge library and no mandatory API or service.

## Start here

- **Use it in a cloud assistant:** [download the single-skill ZIP and upload it](docs/installation.md#cloud-upload-without-a-local-install). Claude web is the documented non-Codex route; its live activation has not been tested here.
- **Use another skill host:** [install the complete folder](docs/installation.md#install-the-complete-folder) in that host's documented directory.
- **Read without installing:** open the [skill entrypoint](skills/leadership-toolbox/SKILL.md), [method catalog](skills/leadership-toolbox/references/catalog.md), or [worked examples](docs/quick-start.md). An assistant with repository-reading tools can load the entrypoint and its linked files manually. This does not register a skill automatically.

Try: “Use leadership-toolbox. Help me prepare for a missed-deadline conversation. Keep it short.”

Questions come first when a missing fact could change the advice, even without asking to be challenged. An explicit quick answer or method lookup stays direct.

For deeper help: “Use leadership-toolbox. Grill me about our recurring handoff problems. Challenge my explanation before choosing a method.”

To make understanding visible: “Show your current understanding as a small context diagram. Mark assumptions and unknowns so I can correct it before we explore options.” See the [visual examples](skills/leadership-toolbox/references/visual-examples.md).

For a lookup: “Explain GROW, its practical limits, and what the evidence actually supports.”

## What you get

- 32 distinct methods with steps, words to try, examples, prerequisites, guardrails and sources
- Adaptive probing by default for unclear situations, with explicit quick-answer and direct-lookup routes
- Correctable situation models: context, stakeholders/authority, process/dependencies, problem hypotheses and conditional options, with a portable text fallback
- A practical method wiki as the first link; primary evidence and sector limits when the claim needs them
- Eight situation dimensions for explainable comparisons, without scoring people or predicting success percentages
- Four knowledge topics that distinguish plausible explanations and guide what to observe next
- 25 paper/review records, 10 scoped book/preview records, and an evidence/gap map for every method
- Templates and optional private records, kept outside the shared skill
- Standard-library install/update/restore helpers, reproducible archives, checksums and read-only CI

## What is verified

See [validation](docs/validation.md) for exact revisions, automated package checks and matched model-output comparisons. File/installation checks and fictional model tests do not prove leadership effectiveness. Reading scopes and remaining gaps are explicit; book metadata is further reading, not evidence.

[Installation](docs/installation.md) · [Examples](docs/quick-start.md) · [Knowledge library](skills/leadership-toolbox/references/knowledge/README.md) · [Sources](skills/leadership-toolbox/references/sources.md) · [All docs](docs/index.md)

## Reuse and boundaries

Original project material is MIT except explicitly marked CC BY-SA 4.0 adaptations. See [LICENSE](LICENSE) and [notices](THIRD_PARTY_NOTICES.md). Linked articles, books and instruments retain their own rights. No endorsement by their authors is implied.

The skill cannot create authority or consent. It does not send messages, make staffing decisions, resolve serious allegations or replace qualified processes. Personal profiles are optional and are never required to begin.

Version: 0.2.1. No website, background service or paid API is required.

## Public method browser

https://leadership-toolbox.web.app/ provides the reviewed method catalogue and skill/library downloads. `python3 scripts/build_pages.py` generates `build/pages/` from the authoritative catalogue and reviewed archive allowlist. Hosting publication does not change host activation or human outcome evidence.

Built by [Tony Wu](https://haitaowu12.github.io/tony-wu-home/) · [More projects](https://haitaowu12.github.io/tony-wu-home/#work).

## Firebase Hosting

[Open the published project](https://leadership-toolbox.web.app/). Firebase Hosting is the primary destination for future releases. Run `python3 scripts/validate.py` and `python3 -m unittest discover -s tests -v`, then `python3 scripts/build_pages.py`. Publish only the reviewed `build/pages/` catalogue and archives.

```sh
firebase deploy --only hosting --project tony-wu-projects
```

The repository configuration selects the site and public output directory. Hosting uses the no-cost Spark plan. The `Firebase Hosting` workflow publishes successful `main` builds once its Google federation connection is configured. Existing hosts remain available.

### Automatic Firebase publication

`.github/workflows/firebase-hosting.yml` runs the project checks and packages its public output on pull requests and pushes to `main`. Only a successful `main` build publishes to Firebase. Deployment uses the checked artifact, skips superseded commits and keeps the current live release when checks fail.

The one-time Google connection requires the repository variables `FIREBASE_WORKLOAD_IDENTITY_PROVIDER` and `FIREBASE_DEPLOY_SERVICE_ACCOUNT`. Authentication uses short-lived GitHub identity tokens. A manual run from `main` can retry publication after a connection failure. Find the build and deployment result under **Actions → Firebase Hosting**.
