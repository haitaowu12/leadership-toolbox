# Explainable method matching

This is an editorial decision aid, not a validated assessment, personality classifier, prediction engine or measurement of leadership quality. Use the [dimension anchors](dimensions.json), [catalog profiles](catalog.json) and full cards together. Public evidence for a method does not validate this matching rubric.

## Keep five things separate

1. **Gates:** safety, coercion/retaliation, authority, privacy, required expertise, essential consent and non-negotiable obligations.
2. **Situation:** observed facts and the eight mixed-type dimensions. Time is a duration, knowledge and alignment are categories, and only consequence and reversibility use anchored ordinal levels.
3. **Method affordances:** job/output, requirements, preparation and session time, compatible contexts, cautions and stop conditions.
4. **User priorities:** which tradeoffs matter in this case. Speed, participation, assurance, learning and burden can conflict.
5. **After-action observations:** output, later outcome and balancing harm. These never retroactively prove a universal method ranking.

Unknown, not applicable and conflicting evidence are different. Every important value needs a basis and whose account it represents. A missing value is never zero, average, good news or a failure.

## Step 1: Gate the proposed action

For each candidate, mark requirements **met**, **unmet** or **unknown** using the actual proposed action. Preparing a decision request may be authorised when committing the organisation is not. A failed gate cannot be offset by a high fit elsewhere.

- **Eligible:** mandatory requirements are supported for this bounded action.
- **Conditional:** a consequential requirement is unknown or a manageable prerequisite remains. Name what must be established and by whom before action.
- **Excluded:** a requirement fails, the card's contraindication applies, or the intended use is outside the toolbox's scope.

Immediate danger and serious allegations route to the established protection/qualified process; do not let a lengthy interview delay it. “No leadership method yet” and “no intervention” are valid selections. Do not require artificial ratings for specialist deferrals.

## Step 2: Make a short candidate set

Start from the immediate job in [catalog](catalog.md), not from a favourite framework. Use three to five plausible cards when needed, then compare the strongest two or three. Read their full cards before recommending action. The structured profiles identify relevant dimensions and cautions, not statistical suitability or all possible uses.

A profile's fit list means “this context makes the stated job plausible”; caution means “inspect this limitation”. Neither overrules the card's prerequisites. Dimensions omitted from a profile are not assumed safe or irrelevant to global gates.

## Step 3: Compare visibly

For each serious candidate, record:

| Criterion | Allowed judgment | Required explanation |
|---|---|---|
| Gate status | Eligible / conditional / excluded | Requirement and supporting or missing fact |
| Job and output fit | Direct / partial / mismatch / unknown | How its concrete output addresses the desired change |
| Context fit | Supported / mixed / mismatch / unknown | Relevant dimension values and the mechanism connecting them to the card |
| Feasibility | Feasible / depends / infeasible / unknown | Actual authority, participants, access, expertise, time and resources |
| Burden and downside | Plain description, locally estimated | Preparation, meeting effort, downstream work and possible harm |
| Evidence boundary | Source type and application limit | Distinguish source guidance, research, editorial transfer and local experience |

These labels are ordinal conversational judgments where applicable, not calibrated intervals. Do not add, average, multiply or convert them into a percentage, universal “best method” score or probability of success. Do not treat source prestige or number of citations as proof of fit. A longer method may be justified by assurance; lower effort is not automatically better.

If the user asks for “a metric”, explain the relevant anchored profile and comparison rather than invent an unsupported scalar. Natural-unit decision criteria for a particular decision (L29) are separate from scoring leadership methods.

## Step 4: Select, challenge, and test sensitivity

Recommend one primary next move and the strongest alternative. State:
- The few facts doing the most work in the choice
- The consequential unknowns
- A plausible fact that would reverse the choice
- Why the alternative is not first now
- What the selected method will produce, and what it cannot decide

Test whether reasonable disagreement about one uncertain value changes the shortlist. If yes, ask the smallest useful question or make the advice conditional. Do not resolve ties by pretending certainty. A reversible preparatory step can be recommended before committing action.

## Step 5: Combine only with a reason

A sequence is useful when one method produces a prerequisite for the next. Specify an exit condition and owner between them. Examples: capacity tradeoff → delegation after time is released; evidence check → feedback after the episode is established; process map → bounded test after a bottleneck and recovery plan are agreed. Do not stack three workshops to solve a ten-minute issue.

## Minimal situation record

Use [situation template](../templates/situation-profile.md) only when a reusable record helps. Values have a status (grounded/provisional/contested/unknown/not_applicable), evidence and account owner. Do not imply external verification from the user's account. Corrected values supersede earlier values while retaining relevant uncertainty. Use the separate optional [schema](../schemas/situation-v1.schema.json) for machine interchange; no file is required to use the skill.

## Evaluate the matcher, not people

Test it with paired situations that change one fact: capacity, authority, recovery, willingness or an excluded risk. Check whether the recommendation appropriately changes, whether unknowns stay unknown, and how much interviewing was required. Compare against a simpler goal-and-constraints baseline. Neither agreement with an evaluator nor faster replies establish real-world effectiveness.
