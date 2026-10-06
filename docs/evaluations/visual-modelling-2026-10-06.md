# Correctable visual situation modelling · 2026-10-06

## What ran

Four actual responses were generated in one fresh native-model context: an initial launch map, a sequential authority correction with problem/option exploration, a separate one-sentence/no-diagram request, and a separate conflicting-authority request. The [complete prompts, outputs, read-file lists and input hashes](visual-modelling-results-2026-10-06.json) are retained. The response generator loaded the working skill manually and was not shown the authored visual examples, tests, prior evaluations, desired answer or scoring rubric. The last two cases reused the context and are not independent samples.

The implementer reviewed the responses after generation. This is a small fictional behavior check, not a blinded human study, reproducible benchmark, automatic skill-discovery test, Microsoft 365 tenant test or workplace-effectiveness result. Exact model build and sampling settings were not recorded. No external communication, private workplace data or actual launch action was involved.

## Observed behavior

- **First understanding check:** produced a compact source-labelled launch sequence, treated the user's account as reported, marked missing final-approval authority and cause/location of the wait, and asked one consequential correction question without adding fixes.
- **Correction and exploration:** retained IDs for existing actors and unaffected relationships, retired the marketing-to-web approval edge, added legal as final approver, and updated both the prose and conditional options. It explicitly excluded transferring legal's decision rights to the coordinator. It also withdrew the earlier implication that the wait was located at marketing's approval step. The response kept the reported delay and missing cutoff separate from three possible explanations, with distinguishing observations. Options included evidence gathering, timing/handoff coordination and leaving the process unchanged. It honored the request for no more questions.
- **No-diagram request:** returned exactly one opening sentence without a model, probing question, source list or measurement appendix.
- **Conflicting authority:** showed both source-labelled ownership claims as contested, did not treat seniority as proof, and kept coordination distinct from approval authority. It marked the written policy, finance account and escalation route unresolved.

The first map's text indentation is less immediately clear than a drawn flowchart, although explicit R1/R2 labels identify the endpoints. The second response is fairly long (multiple requested views plus options); concision and everyday usability still need broader checking. It describes option-to-problem connections in prose rather than assigning a distinct edge ID to every optional direction, which is acceptable for a lightweight view but weaker for fully machine-reconciled models. No such machine model or automatic reconciliation engine is claimed.

## Package and example checks

At the final reviewed working snapshot, `python3 scripts/validate.py` and `python3 -m unittest discover -s tests -v` passed under Python 3.12.14: 111 reviewed files, 32 methods and 63 tests. Four new tests check inclusion/routing of the visual resources, declared node and relationship IDs in the authored Mermaid example, equivalence with the text fallback, retirement of stale edges, and separation of hypotheses/proposals from current relationships. These are static contract checks, not semantic reasoning or visual-rendering tests. The original 59 tests still run, including temporary archive lifecycle tests. No downloadable package was built or delivered for this draft revision.

An initial test run rejected the expanded skill description for exceeding the existing 200-character upload limit. It was shortened to 195 characters and all tests then passed. Only that metadata line changed during response generation; the behavioral instructions were unchanged during those four responses. The raw record preserves the description/read-version qualification. This fix is not claimed to test automatic discovery.

## Rendering and remaining limits

The generated responses use readable text nodes and labelled relationships. The authored example also contains optional Mermaid source with a complete text equivalent. No Mermaid host, SVG/image exporter, Microsoft 365 Copilot renderer, code interpreter or live tenant was operated. Syntax-oriented tests do not establish that a host renders the diagram or that a rendered artifact is accessible. No renderer or new runtime dependency is installed by the skill.

The workflow is an original editorial sensemaking aid, not causal proof, formal risk assessment, psychological assessment, SysML/BPMN conformance or formal organisational validation. Neither a model correction nor a completed handoff diagram establishes that someone accepted a commitment or that an outcome improved. The new examples are original fictional material, not reused proprietary assets.

Useful future checks include longer correction chains, deletion/merge of entities, contradictory new evidence, sparse-context requests, accessibility on actual hosts and user corrections after image export. They remain untested here. Repository CI must be checked on the published commit; a local pass does not itself establish that remote check.

## Separate review

A separate read-only model reviewer found no substantive authority, privacy or causal-proof blocker in the authored guidance and examples, and independently ran the 109-file structural check and all 63 tests before this evaluation record was added. It recommended making withdrawal of downstream inferences explicit when a corrected edge changes their basis. That sentence was added after generation and received static/package revalidation; the recorded correction response already displayed that behavior, but the final wording was not used to regenerate the four responses. This was model review, not a blinded human assessment.
