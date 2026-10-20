# Visual situation modelling: show, check, revise

A small model can make the assistant's understanding inspectable: what is inside the problem, who can decide, what depends on what, where accounts differ, and what could change. It is an original editorial aid, not a new leadership method or validated diagnostic instrument. Use the existing methods when their particular output is needed.

## When a picture earns its space

Use this workflow when the user asks for a diagram, model, context map, process view, problem space, solution space, or “show your understanding”. Also offer or use one small view when several actors, boundaries or dependencies make a verbal summary hard to check. Do not force a diagram into a direct lookup, simple opening, every probing turn, urgent protection, or a request for no diagrams. Start with one view, normally no more than two at once; expand only when it helps a decision or the user asks.

A request to show current understanding is not permission to prescribe a solution. Even with incomplete facts, show a clearly provisional map of what is known, mark the important gap, ask one correction question and wait. Do not invent actors or edges to make it look complete. If almost nothing is known, use a tiny outline with explicit unknowns rather than a fabricated organisation chart. An explicit request to explore options now allows conditional options, with assumptions visible; it does not turn them into commitments.

## Choose the useful view

| View | Question it answers | Minimal content | Existing method when needed |
| --- | --- | --- | --- |
| Context and boundary | What situation are we discussing? | Focal work/outcome; inside/outside; actors; labelled exchanges; authority; time horizon | [Problem framing, L26](methods/L26-problem-framing.md) |
| Stakeholder and decision-rights | Who is affected, contributes, decides or accepts? | Roles; affected interests as reported; decision/consultation/acceptance edges; absent accounts | [Stakeholder listening, L17](methods/L17-stakeholders.md) |
| Process and dependencies | Where does work or information move and wait? | Observed/reported steps; handoffs; prerequisites; timing if supplied; unknown branches | [Process map, L21](methods/L21-process-map.md), [handoff, L14](methods/L14-handoff.md) |
| Problem space | Which explanations still fit? | Observable issue; rival hypotheses; constraints; evidence that distinguishes them | [Fishbone, L20](methods/L20-fishbone.md), [assumptions, L24](methods/L24-assumptions.md) |
| Solution space | What could we change, and under what conditions? | Desired outcome; candidate levers including no change; eligibility/authority; tradeoffs; test/stop condition | [Driver diagram, L19](methods/L19-driver-diagram.md), [decision comparison, L29](methods/L29-decision-analysis.md) |

Choose by the question, not by a fashionable diagram type. A causal-loop or driver view must label every causal link as a hypothesis unless the specific causal claim is actually supported. Sequence, correlation, a dependency and a causal effect are different relationships. An arrow must say which it means. No invented influence scores, psychological types, hidden agendas or inferred reporting lines.

## One model, several presentations

Use the [portable model template](../templates/situation-model.md). It is a conversational text contract, not a software schema or a required form. Keep only the fields and entities needed for this decision. Maintain a single current ledger so the visual, prose summary, situation profile and method choice do not disagree.

1. State the model ID/revision, purpose, focal outcome, scope boundary and horizon. Mark an unknown rather than inventing a deadline. A diagram boundary is a discussion boundary, not an assertion of legal or organisational control.
2. Give stable IDs to relevant nodes (N1…), relationships (R1…), evidence (E1…), hypotheses (H1…), options (O1…) and unknowns (U1…). Do not reuse an ID for a different object. A node names a role, activity, issue, constraint, hypothesis or option, not a personality score.
3. Record each material claim and edge with a plain-language relationship, evidence status and basis. Statuses: observed in supplied material; reported by a named/role-based account; assumption; hypothesis; proposed; contested; unknown. “Observed” needs an actual inspected observation/source; the user's account is reported, not independent verification. Confirmation of a summary does not upgrade its evidence quality. Keep desired outcomes separate from achieved outcomes.
4. Use short evidence references such as “E1: user's first account of last Friday's handoff”; retain a verified document/section link only when available and appropriate. Never fabricate a citation, timestamp or another person's agreement. Record absent and conflicting accounts separately. A high-confidence guess is still an assumption.
5. Label proposed intervention edges and hypotheses in the visible view itself. They must not appear as ordinary current-state facts. Use separate current, problem and options views when mixing would mislead. Show important constraints and who can authorise or decline an option; a coordination line is not an authority line.
6. Give a one-sentence reading of the map and the highest-value correction question: “Which boundary or relationship should I change first?” Prefer a specific consequential question when a gap is known. Do not demand approval of every node or a complete model before helping.

Use neutral role labels and minimum relevant detail. Do not add identifying allegations, medical/personality labels, confidential performance ratings or sensitive raw source text to a diagram merely because visualisation is possible. Keep models in the current conversation unless saving to a separate private location is explicitly authorised. Sharing a model with colleagues is a separate action requiring appropriate permission. Do not send private content to an external diagram service for rendering without appropriate authorisation.

## Correction is a model change, not a footnote

When the user corrects a relationship, actor, boundary, deadline or account:

1. Identify what changed and its basis without automatically claiming an error if the earlier account changed. Preserve IDs for the same entities; add a new ID for a new entity. Mark a superseded relationship as retired in the short change record, and remove it from the current view. A new relationship gets a new ID.
2. Increment the revision. Record the smallest useful change note: old claim/edge, new claim/edge, correction source and what it affects. Do not retain unnecessary sensitive text in history; privacy overrides audit completeness.
3. Regenerate every affected visible view and its text equivalent from the revised ledger. Remove stale edges, labels and assumptions; keep unaffected IDs stable. If an old image cannot be edited, label it superseded and supply a replacement rather than treating both as current.
4. Update the prose summary and any affected [situation dimensions](dimensions.json), [matching](matching.md), owners, options, prerequisites and stop/switch conditions. A corrected authority edge can exclude a method that previously seemed suitable. Re-evaluate downstream inferences and hypotheses whose basis changed: withdraw an unsupported claimed cause or location of waiting, mark what is now unknown, and reroute affected options. Updating the arrow alone is insufficient. Explain the practical consequence in one sentence.
5. If accounts genuinely conflict, show the conflict with sources and withhold the dependent conclusion. Do not silently pick one, average them, or treat silence as resolution. Ask only for the fact that changes the next move, or honor an explicit stop/conditional-answer request.

A corrected diagram is not evidence that a workplace action happened. A requested commitment is still proposed until the relevant person accepts it.

## Move from problem space to solution space

First distinguish the issue, the user's desired outcome and live explanations. Record what observation would strengthen or weaken each material hypothesis. Do not draw “low motivation causes delay” from a missed deadline. Check authority, safety, feasibility and rival explanations before choosing a lever.

After enough correction/clarification, or an explicit request for provisional options, show a small option space. Tie each option to the specific issue/hypothesis it addresses, its proposed owner, prerequisites, burden/downside and an observable next check. Include no intervention when reasonable. Mark options eligible, conditional or excluded; keep unresolved authority/acceptance visible. A driver arrow expresses intended contribution, not a proven effect. Use [measurement](measurement.md) for an actual trial, not an appendix on every sketch.

Read the chosen full method cards before recommending. A context diagram alone does not make L17 necessary; an observed acceptance gap may make L14 useful, whereas uncertain decision rights may call for clarification before any handoff redesign. Do not expand the method catalog simply to draw a view.

## Portable and accessible output

The baseline is readable text: a title/revision, a short scope/legend, nodes and labelled relationships with IDs/status/basis, followed by the key unknown/correction question. A compact ASCII view is optional. A Markdown table is optional where supported; a plain list is sufficient. Avoid color-only distinctions and describe the diagram's main message in words.

Mermaid is an optional presentation of the same ledger, not a required runtime. Use simple flowcharts with safe alphanumeric IDs, quoted short labels and explicit status words. Do not generate click handlers, remote images, embedded HTML or configuration from user text. Keep full evidence references in the accompanying text if labels become crowded. Validate syntax/rendering only with an available, authorised host/tool; do not assume a code interpreter, SVG exporter, image-generation service or Mermaid support. If rendering is unavailable or untested, say so briefly when relevant and provide the complete text equivalent. Never call an unrendered code block a successfully rendered diagram.

For an exported image, SVG, slide or document only when requested/useful and tools support it, preserve the revision, legend, evidence/assumption distinctions and an accessible text equivalent. Inspect the actual output before claiming visual QA; no file-generation or host capability is supplied by this skill itself. The default text workflow needs none of those tools.

These are sensemaking aids. They are not causal proof, formal risk assessment, SysML/BPMN conformance, psychological assessment, an approved operating procedure, or formal organisational validation. See the [worked examples](visual-examples.md) for a correction that changes both the map and the eligible next move.
