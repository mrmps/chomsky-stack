---
name: junk-detection
description: Audit diffs, pull requests, and codebases for reward-hacked or Goodharted code, backwards-compatibility cruft, needless fallbacks and shims, accidental complexity, unreadable giant files or functions, wrong abstractions, fake or evaluator-overfit tests, hardcoded stubs, and hand-rolled machinery that a standard or established library could replace. Use when asked to deslop, simplify, detect junk, review AI-generated or vibe-coded changes, investigate RL-maxxing code, reduce codebase entropy, or find code that passes checks without genuinely satisfying the product contract.
---

# Junk detection

Separate bad aesthetics from bad incentives. Find code that optimizes a proxy, preserves a constraint that no longer exists, or makes future change harder without buying required behavior.

Read [references/taxonomy.md](references/taxonomy.md) before the first audit in a task. Treat the scanner as triage, never as a verdict.

## Choose the audit surface

1. Read repository instructions and the relevant product or domain contract.
2. For branch or PR work, compare the merge-base with `origin/main` (or the repository's actual trunk) through `HEAD`, then include staged, unstaged, and untracked work.
3. For a whole-codebase request, start with changed and frequently touched paths, then broaden to all first-party code.
4. Exclude generated, vendored, minified, lock, fixture, snapshot, and migration output unless the request targets it.
5. Preserve the user's existing changes. Audit only unless the user also asks for fixes.

Run the bundled triage script from the repository root:

```bash
python3 <skill-dir>/scripts/scan_hotspots.py --scope diff
python3 <skill-dir>/scripts/scan_hotspots.py --scope all
```

Use `--base <ref>` when trunk is not `origin/main`. Use `--json` when another tool will consume the output.

## Reconstruct the real contract

Before calling anything junk, identify:

- The behavior the user or product actually needs.
- Public APIs, persisted data, deployed clients, URLs, events, and integrations that constrain compatibility.
- What the tests, types, lint rules, benchmarks, or review rubric measure.
- The gap between that proxy and the intended behavior.
- The narrowest direct observation that would prove the behavior.

If the contract is unknown, report a suspect and the missing evidence. Do not manufacture certainty from code shape alone.

## Audit through six lenses

### 1. Reward-hacked implementation

Look for a patch that satisfies the evaluator instead of the task:

- Production code branches on test names, fixtures, environment markers, or known inputs.
- Expected outputs, IDs, timestamps, paths, or benchmark cases are hardcoded.
- Tests, graders, CI, timeouts, snapshots, or assertions are weakened to create a green signal.
- Errors are swallowed, exit codes forced to success, features stubbed, or data silently fabricated.
- A test passes but asserts nothing meaningful, mocks away the behavior, or only repeats the implementation.
- The implementation handles visible cases in isolation but breaks composition, invalid inputs, retries, or real user flows.
- The final claim is stronger than the evidence actually collected.

Classify this as **reward hacking** or **specification gaming** only when the proxy/intent gap is evidenced. Use **test overfitting** for a narrower visible-test fit. Use **structural erosion** for cumulative maintainability loss without evaluator gaming.

### 2. Compatibility cruft

Search for legacy aliases, dual readers/writers, old parameter names, fallback formats, shims, adapters, deprecated branches, migration flags, and catch-all parsing.

For each path, demand a live claimant: a published contract, supported version, deployed caller, stored record, migration window, telemetry, or explicit policy. No claimant means the compatibility code is a deletion candidate. A real claimant means it may be essential even when ugly.

Prefer a bounded migration with an owner and removal condition over permanent dual behavior.

### 3. Accidental complexity and unreadability

Use line count and branch count only to locate hotspots. Confirm mixed responsibilities, condition-laden abstractions, distant state mutation, temporal coupling, duplicated policy, deeply nested control flow, or names that conceal the data model.

Ask whether the complexity belongs to the domain or to the chosen design. A long cohesive table or generated parser may be fine; a short function with five hidden side effects may not be.

Prefer deleting states, branches, wrappers, and concepts over merely splitting a file into smaller files.

### 4. Wrong abstraction and defensive slop

Look for abstractions with mode flags, callers that need different subsets, wrappers that only rename another API, helpers used once, speculative extension points, excessive comments, broad casts, abnormal try/catch blocks, and defensive checks on trusted internal paths.

Inline the suspected abstraction mentally. If each caller becomes simpler and more truthful, recommend unwinding it. Do not worship DRY: duplication can be cheaper than a condition-laden false abstraction.

### 5. Reinvented machinery

Inventory the language standard library and already-installed dependencies before proposing a new package. Flag custom implementations of security primitives, protocol parsers, schema validation, retries/backoff, caching, concurrency, date/time handling, URL handling, serialization, diffing, globbing, state machines, or rich UI primitives when a mature existing tool already satisfies the exact contract.

Compare total cost, not line count: correctness surface, edge cases, maintenance, dependency weight, supply-chain risk, bundle/runtime cost, project conventions, and replaceability. Recommend a library only when the replacement is materially simpler and better supported. Never add a large dependency to replace a transparent ten-line helper.

### 6. User-path incoherence

Trace the real path from input to visible outcome. For auth and chat, explicitly inspect:

- Auth loading, signed-out, expired, revoked, retry, redirect, and return-to states.
- Server-side authorization and ownership, not only client gating.
- Duplicate submits, reconnects, cancellation, ordering, stale state, optimistic rollback, and partial streaming.
- Empty, error, offline, disabled, narrow-screen, keyboard, screen-reader, and focus-restoration states.
- Error copy that identifies what failed and offers a recovery action without leaking sensitive details.

UI code can be reward-hacked too: a happy-path screenshot or shallow E2E pass is not proof that the interaction survives failure and repetition.

## Demand evidence

Confirm a finding with at least one of:

- A reachable caller or user flow demonstrating the bad behavior.
- A counterexample outside the visible tests.
- A simpler executable replacement or deletion diff.
- Duplicate policy that can demonstrably collapse to one source of truth.
- A standard or installed library whose documented contract covers the behavior.
- History or telemetry showing a compatibility branch has no remaining claimant.

Use property-based, generative, metamorphic, integration, or held-out cases when example tests are easy to game. Passing the existing suite is supporting evidence, not the definition of success.

## Rank findings

- **P0 — Critical:** security boundary bypass, destructive data error, or evaluator tampering that invalidates all evidence.
- **P1 — High:** shipped behavior is wrong or unrecoverable; fake success; auth/ownership failure; compatibility branch corrupts current behavior.
- **P2 — Medium:** substantial structural erosion, wrong abstraction, permanent compatibility cost, or hand-rolled machinery with a credible simpler replacement.
- **P3 — Low:** localized slop or readability cost with a clear cleanup and limited risk.

Do not inflate severity because code looks AI-generated.

## Report findings first

For each confirmed finding provide:

1. Severity and exact `path:line`.
2. Class: reward hack, compatibility cruft, accidental complexity, wrong abstraction, reinvented machinery, or user-path incoherence.
3. The real contract and the proxy or obsolete assumption the code optimizes.
4. Concrete failure or maintenance cost.
5. The smallest high-leverage simplification.
6. Proof required before and after changing it.

Separate **confirmed findings** from **suspects needing evidence**. Consolidate one systemic cause instead of listing every symptom. If nothing clears the evidence bar, say so.

End with:

```text
Audit surface:
- <base, paths, and states inspected>

Evidence:
- <commands, tests, direct observations>

Not verified:
- <missing runtime, history, telemetry, or product evidence>
```

## Guardrails

- Preserve behavior unless a clear bug or obsolete contract is proven.
- Do not delete backwards compatibility from public or persisted surfaces on intuition; Hyrum's Law is the counterweight to cleanup enthusiasm.
- Do not confuse unfamiliar, verbose, generated, performance-critical, or security-sensitive code with junk.
- Do not turn cleanup into architectural churn or dependency tourism.
- Do not modify tests merely to make a failure disappear.
- Prefer minimal focused changes and direct demonstrations over broad rewrites.
- Stop when the proposed cleanup adds more concepts than it removes.
