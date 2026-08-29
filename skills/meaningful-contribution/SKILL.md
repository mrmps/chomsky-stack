---
name: meaningful-contribution
description: Require software changes to be demonstrated, not merely generated. Use when implementing, fixing, refactoring, reviewing, or preparing a pull request for code, configuration, migrations, build tooling, or other behavior-affecting repository changes—especially agent-generated changes that need manual verification, automated regression coverage, edge-case testing, honest naming and types, and concise evidence for reviewers.
---

# Meaningful Contribution

Treat the deliverable as a change plus credible evidence that it works. Match the depth of proof to the change's risk, and never claim checks that were not run.

## Establish the proof contract

Before editing:

1. State the user-visible or system-visible behavior that must change.
2. Identify the narrowest way to observe that behavior.
3. List the important failure modes and non-happy paths.
4. Find the repository's own instructions and existing test patterns.
5. Choose the evidence required for completion.

For a bug fix, reproduce the failure before changing code whenever feasible. For a feature, define concrete acceptance examples. For a refactor, define the behavior and interfaces that must remain unchanged.

## Build the smallest coherent change

- Prefer the smallest change that fully satisfies the proof contract.
- Keep names, types, and abstractions truthful. A name is a contract; rename or redesign anything that requires “it says X, but really means Y” to understand it.
- State expected inputs, outputs, state transitions, and behavior for invalid or unexpected inputs.
- Fit the repository's established domain model and patterns. Do not introduce a competing abstraction without a clear need.
- Read every changed line in context after generation. Remove accidental complexity, dead branches, broad casts, and unrelated cleanup.

## Prove behavior in layers

Use the applicable layers below. Do not substitute static inspection for runtime evidence when runtime behavior changed.

### 1. Observe it directly

Exercise the changed path manually or through the smallest representative command. Confirm the actual output, UI state, side effect, or failure behavior.

For UI work, inspect each affected viewport and interaction state. For APIs or jobs, exercise realistic input and inspect the response plus relevant persisted or emitted state.

### 2. Add automated regression coverage

Encode the observed behavior in the narrowest stable test that would catch a regression. Prefer behavior assertions over implementation details.

For a bug fix, prove the test is meaningful by seeing it fail before the fix, or by temporarily reverting or neutralizing the relevant fix and seeing it fail, when safe and practical. Restore the working change afterward.

### 3. Test the edges

Cover the most consequential deviations from the happy path, such as:

- Empty, missing, malformed, duplicate, or boundary inputs
- Authorization, ownership, or tenant boundaries
- Timeouts, retries, partial failures, and repeated execution
- Concurrency, ordering, stale state, and idempotency
- Loading, error, empty, disabled, keyboard, and narrow-screen UI states
- Compatibility with existing callers and stored data

Choose edges from the actual change; do not add ceremonial cases that cannot catch a plausible defect.

### 4. Run proportionate repository checks

Run the focused test first, then the smallest relevant broader suite. Add type checking, linting, formatting, packaging, migration validation, or smoke tests when the touched surface warrants them and repository instructions permit them.

If a check cannot run, report the exact blocker and compensate with the strongest safe evidence available. Do not mark the work complete if the missing check leaves the central claim unproven.

## Audit coherence

Before presenting the result, answer:

1. Have I actually observed the changed behavior working?
2. Would the regression test fail without the change?
3. Do the names and types describe the real data and behavior?
4. Are unexpected inputs handled deliberately?
5. Does the abstraction make sense both locally and in the wider codebase?
6. Can I explain the change from input to output in plain language?
7. Did I avoid shifting discovery or verification work onto the reviewer?

If an answer is “no” or “not sure,” continue working or disclose the unresolved risk.

## Present evidence

End with a compact reviewer-ready record:

```text
Behavior proven:
- <observable outcome>

Evidence:
- `<command or manual path>` — <result>
- `<test command>` — <result and test count, if known>

Edges checked:
- <edge> — <result>

Not verified:
- <anything not run, with reason>
```

Include screenshots, logs, requests/responses, or other artifacts when they materially help a reviewer verify the result. Never imply that generated code, a clean diff, passing types, or a plausible-looking implementation alone proves correctness.
