# Matched first-turn comparison · 2026-10-05

## What happened

Two fresh generator contexts answered the same four fictional situations in both concise and probing modes, yielding eight responses per arm. One used ordinary assistant judgment without the package; the other manually loaded Leadership Toolbox and 25 runtime files. Two separate reviewers assessed anonymous X/Y pairs whose label order varied by pair without seeing the arm identities, repository or each other's reviews.

Both reviewers found no clear safety blocker. They preferred the skill response's explicit follow-through in the missed-deadline case and its separation of cue, action and result in the no-opportunity habit case. Other differences were smaller or disputed. The no-skill baseline also handled the core safety and no-intervention choices well. This is a narrow text comparison, not evidence that the skill improves people's leadership or generally outperforms a capable assistant.

## Reproducible record

- [Predeclared cases, controls and criteria](completion-protocol.json)
- [Prompt-only generator input](completion-inputs.json)
- [Complete responses, read ledgers, anonymous packet, arm mapping and both reviews](completion-results.json)
- Runtime revision: [d35d4f25](https://github.com/haitaowu12/leadership-toolbox/commit/d35d4f25c6ec17e299d86da241f8b7afdccb7bfa)
- All 25 recorded runtime blob hashes were checked against [f8dd69e9](https://github.com/haitaowu12/leadership-toolbox/commit/f8dd69e996d0db47ae448c7ff8bfbee799c67cd0); none changed. The whole skill subtree is caadb55bf4ae2de7b819c10470733cde133dbae1.
- Requested settings: inherited model and xhigh reasoning for both generators/reviewers. Effective runtime model identity/settings were not independently verified.

An earlier pilot exposed the reviewer checklist to generators. It was discarded before scoring. Fresh scored contexts received only prompts/mode controls, plus the runtime library for the skill arm. The original prompts and criteria were fixed before those generations. No generated answer was edited before review.

## Case-level findings

| Situation | Observed comparison |
|---|---|
| Two missed deadlines, presumed low ownership | Both rejected the unsupported attribution. Both reviewers favored the skill's explicit next-episode review; neither established that a blockage or skill deficit existed. |
| Help-seeking cue never occurred | Both treated the plan as untested and rejected arbitrary escalation. Both reviewers favored the skill's separate observations of cue, attempt and resumed progress, with an unknown baseline. |
| Successful handoffs, proposed extra process | Both allowed no added intervention. One reviewer favored the skill's concrete revisit triggers; the other judged complementary strengths and tied them. |
| Reported retaliation after a safety concern | Both paused the group exercise, addressed immediate risk and deferred to an appropriate protected/authorized process. Both reviewers tied them in each mode. |

Every output met its assigned 160-word concise or 110-word probing ceiling by whitespace count. All probing outputs had three numbered items. One baseline response contained four interrogative sentences: one reviewer counted numbered groups and the other enforced the question limit literally. The second interpretation is supported by the preserved text; the output was not repaired afterward.

Reviewers did not reward citations or jargon, and did not independently verify the three cited research-scope claims. Their full criterion judgments, including partial ratings and disagreements, remain available in the result record.

## What this does and does not establish

This run demonstrates manual loading of the runtime references and useful, bounded first-turn behavior in these cases. It exercises assumptions, opportunity-aware observation, a no-intervention route, mode controls and a serious-risk boundary.

It does not test automatic installation/discovery in Claude or another host, varied model families, repeated stochastic runs, the separate contribution of the knowledge library, all 32 methods, long conversations, accessibility or real workplace outcomes. Cases within each arm shared a context; order was not randomized. Arm identities were withheld from reviewers, but style/citations could reveal the likely condition. These are model reviewers, not human participants or independent clinical/legal adjudicators.

The next empirical question is whether willing users find the advice feasible and useful with acceptable burden. That remains untested; no scores, percentages or research effect sizes in this package predict that result.
