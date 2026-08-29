# Review Sections (11 sections, after scope and mode are agreed)

Read this file once Step 0 is complete. Execute every section — do not run the review from memory.

**Anti-skip rule:** Never condense, abbreviate, or skip any review section (1-11) regardless of plan type (strategy, spec, code, infra). Every section exists for a reason. "This is a strategy doc so implementation sections don't apply" is always wrong — implementation details are where strategy breaks down. If a section genuinely has zero findings, say "No issues found" and move on — but you must evaluate it.

**The stop rule, stated once.** It applies at the end of every section below and is not repeated there: AskUserQuestion once per issue. Do NOT batch. Recommend + WHY. If a section turned up zero findings, state "No issues, moving on" and proceed. If it has findings, you MUST call AskUserQuestion as a tool call — a finding with an "obvious fix" is still a finding and still needs user approval before any change lands in the plan. Do not proceed until the user responds. And throughout: do NOT make any code changes. Review only.

---

## Section 1: Architecture Review

Evaluate and diagram:

* Overall system design and component boundaries. Draw the dependency graph.
* Data flow — all four paths. For every new data flow, ASCII diagram the:
    * Happy path (data flows correctly)
    * Nil path (input is nil/missing — what happens?)
    * Empty path (input is present but empty/zero-length — what happens?)
    * Error path (upstream call fails — what happens?)
* State machines. ASCII diagram for every new stateful object. Include impossible/invalid transitions and what prevents them.
* Coupling concerns. Which components are now coupled that weren't before? Is that coupling justified? Draw the before/after dependency graph.
* Scaling characteristics. What breaks first under 10x load? Under 100x?
* Single points of failure. Map them.
* Security architecture. Auth boundaries, data access patterns, API surfaces. For each new endpoint or data mutation: who can call it, what do they get, what can they change?
* Production failure scenarios. For each new integration point, describe one realistic production failure (timeout, cascade, data corruption, auth failure) and whether the plan accounts for it.
* Rollback posture. If this ships and immediately breaks, what's the rollback procedure? Git revert? Feature flag? DB migration rollback? How long?

**EXPANSION and SELECTIVE EXPANSION additions:**
* What would make this architecture beautiful? Not just correct — elegant. Is there a design that would make a new engineer joining in 6 months say "oh, that's clever and obvious at the same time"?
* What infrastructure would make this feature a platform that other features can build on?

**SELECTIVE EXPANSION:** If any accepted cherry-picks from Step 0D affect the architecture, evaluate their architectural fit here. Flag any that create coupling concerns or don't integrate cleanly — this is a chance to revisit the decision with new information.

Required ASCII diagram: full system architecture showing new components and their relationships to existing ones.

## Section 2: Error & Rescue Map

This is the section that catches silent failures. It is not optional.

For every new method, service, or codepath that can fail, fill in this table:

```
  METHOD/CODEPATH          | WHAT CAN GO WRONG           | EXCEPTION CLASS
  -------------------------|-----------------------------|-----------------
  ExampleService#call      | API timeout                 | TimeoutError
                           | API returns 429             | RateLimitError
                           | API returns malformed JSON  | JSONParseError
                           | DB connection pool exhausted| ConnectionPoolExhausted
                           | Record not found            | RecordNotFound
  -------------------------|-----------------------------|-----------------

  EXCEPTION CLASS              | RESCUED?  | RESCUE ACTION           | USER SEES
  -----------------------------|-----------|-------------------------|------------------
  TimeoutError                 | Y         | Retry 2x, then raise    | "Service temporarily unavailable"
  RateLimitError               | Y         | Backoff + retry         | Nothing (transparent)
  JSONParseError               | N ← GAP   | —                       | 500 error ← BAD
  ConnectionPoolExhausted      | N ← GAP   | —                       | 500 error ← BAD
  RecordNotFound               | Y         | Return nil, log warning | "Not found" message
```

Rules for this section:
* Catch-all error handling (`rescue StandardError`, `catch (Exception e)`, `except Exception`) is ALWAYS a smell. Name the specific exceptions.
* Catching an error with only a generic log message is insufficient. Log the full context: what was being attempted, with what arguments, for what user/request.
* Every rescued error must either retry with backoff, degrade gracefully with a user-visible message, or re-raise with added context. "Swallow and continue" is almost never acceptable.
* For each GAP (unrescued error that should be rescued): specify the rescue action and what the user should see.
* For LLM/AI service calls specifically: what happens when the response is malformed? When it's empty? When it returns invalid JSON? When the model returns a refusal? Each of these is a distinct failure mode.

## Section 3: Security & Threat Model

Security is not a sub-bullet of architecture. It gets its own section.

Evaluate:
* **Attack surface expansion.** What new attack vectors does this plan introduce? New endpoints, new params, new file paths, new background jobs?
* **Input validation.** For every new user input: is it validated, sanitized, and rejected loudly on failure? What happens with nil, empty string, string when integer expected, string exceeding max length, unicode edge cases, HTML/script injection attempts?
* **Authorization.** For every new data access: is it scoped to the right user/role? Is there a direct object reference vulnerability? Can user A access user B's data by manipulating IDs?
* **Secrets and credentials.** New secrets? In env vars, not hardcoded? Rotatable?
* **Dependency risk.** New packages? Security track record?
* **Data classification.** PII, payment data, credentials? Handling consistent with existing patterns?
* **Injection vectors.** SQL, command, template, LLM prompt injection — check all.
* **Audit logging.** For sensitive operations: is there an audit trail?

For each finding: threat, likelihood (High/Med/Low), impact (High/Med/Low), and whether the plan mitigates it.

## Section 4: Data Flow & Interaction Edge Cases

This section traces data through the system and interactions through the UI with adversarial thoroughness.

**Data Flow Tracing:** For every new data flow, produce an ASCII diagram showing:

```
  INPUT ──▶ VALIDATION ──▶ TRANSFORM ──▶ PERSIST ──▶ OUTPUT
    │            │              │            │           │
    ▼            ▼              ▼            ▼           ▼
  [nil?]    [invalid?]    [exception?]  [conflict?]  [stale?]
  [empty?]  [too long?]   [timeout?]    [dup key?]   [partial?]
  [wrong    [wrong type?] [OOM?]        [locked?]    [encoding?]
   type?]
```

For each node: what happens on each shadow path? Is it tested?

**Interaction Edge Cases:** For every new user-visible interaction, evaluate:

```
  INTERACTION          | EDGE CASE              | HANDLED? | HOW?
  ---------------------|------------------------|----------|--------
  Form submission      | Double-click submit    | ?        |
                       | Submit with stale CSRF | ?        |
                       | Submit during deploy   | ?        |
  Async operation      | User navigates away    | ?        |
                       | Operation times out    | ?        |
                       | Retry while in-flight  | ?        |
  List/table view      | Zero results           | ?        |
                       | 10,000 results         | ?        |
                       | Results change mid-page| ?        |
  Background job       | Job fails after 3 of   | ?        |
                       | 10 items processed     |          |
                       | Job runs twice (dup)   | ?        |
                       | Queue backs up 2 hours | ?        |
```

Flag any unhandled edge case as a gap. For each gap, specify the fix.

## Section 5: Code Quality Review

Evaluate:
* Code organization and module structure. Does new code fit existing patterns? If it deviates, is there a reason?
* DRY violations. Be aggressive. If the same logic exists elsewhere, flag it and reference the file and line.
* Naming quality. Are new classes, methods, and variables named for what they do, not how they do it?
* Error handling patterns. (Cross-reference Section 2 — this section reviews the patterns; Section 2 maps the specifics.)
* Missing edge cases. List explicitly: "What happens when X is nil?" "When the API returns 429?"
* Over-engineering check. Any new abstraction solving a problem that doesn't exist yet?
* Under-engineering check. Anything fragile, assuming happy path only, or missing obvious defensive checks?
* Cyclomatic complexity. Flag any new method that branches more than 5 times. Propose a refactor.

## Section 6: Test Review

Make a complete diagram of every new thing this plan introduces:

```
  NEW UX FLOWS:
    [list each new user-visible interaction]

  NEW DATA FLOWS:
    [list each new path data takes through the system]

  NEW CODEPATHS:
    [list each new branch, condition, or execution path]

  NEW BACKGROUND JOBS / ASYNC WORK:
    [list each]

  NEW INTEGRATIONS / EXTERNAL CALLS:
    [list each]

  NEW ERROR/RESCUE PATHS:
    [list each — cross-reference Section 2]
```

For each item in the diagram:
* What type of test covers it? (Unit / Integration / System / E2E)
* Does a test for it exist in the plan? If not, write the test spec header.
* What is the happy path test?
* What is the failure path test? (Be specific — which failure?)
* What is the edge case test? (nil, empty, boundary values, concurrent access)

**Test ambition check (all modes).** For each new feature, answer:
* What's the test that would make you confident shipping at 2am on a Friday?
* What's the test a hostile QA engineer would write to break this?
* What's the chaos test?

**Test pyramid check:** Many unit, fewer integration, few E2E? Or inverted?
**Flakiness risk:** Flag any test depending on time, randomness, external services, or ordering.
**Load/stress test requirements:** For any new codepath called frequently or processing significant data.

For LLM/prompt changes: check `CLAUDE.md` or `AGENTS.md` for prompt/LLM file patterns. If this plan touches any of them, state which eval suites must be run, which cases should be added, and what baselines to compare against.

## Section 7: Performance Review

Evaluate:
* **N+1 queries.** For every new ORM association traversal: is there an includes/preload?
* **Memory usage.** For every new data structure: what's the maximum size in production?
* **Database indexes.** For every new query: is there an index?
* **Caching opportunities.** For every expensive computation or external call: should it be cached?
* **Background job sizing.** For every new job: worst-case payload, runtime, retry behavior?
* **Slow paths.** Top 3 slowest new codepaths and estimated p99 latency.
* **Connection pool pressure.** New DB connections, Redis connections, HTTP connections?

## Section 8: Observability & Debuggability Review

New systems break. This section ensures you can see why.

Evaluate:
* **Logging.** For every new codepath: structured log lines at entry, exit, and each significant branch?
* **Metrics.** For every new feature: what metric tells you it's working? What tells you it's broken?
* **Tracing.** For new cross-service or cross-job flows: trace IDs propagated?
* **Alerting.** What new alerts should exist?
* **Dashboards.** What new dashboard panels do you want on day 1?
* **Debuggability.** If a bug is reported 3 weeks post-ship, can you reconstruct what happened from logs alone?
* **Admin tooling.** New operational tasks that need admin UI or scripts?
* **Runbooks.** For each new failure mode: what's the operational response?

**EXPANSION and SELECTIVE EXPANSION addition:**
* What observability would make this feature a joy to operate? (For SELECTIVE EXPANSION, include observability for any accepted cherry-picks.)

## Section 9: Deployment & Rollout Review

Evaluate:
* **Migration safety.** For every new DB migration: backward-compatible? Zero-downtime? Table locks?
* **Feature flags.** Should any part be behind a feature flag?
* **Rollout order.** Correct sequence: migrate first, deploy second?
* **Rollback plan.** Explicit step-by-step.
* **Deploy-time risk window.** Old code and new code running simultaneously — what breaks?
* **Environment parity.** Tested in staging?
* **Post-deploy verification checklist.** First 5 minutes? First hour?
* **Smoke tests.** What automated checks should run immediately post-deploy?

**EXPANSION and SELECTIVE EXPANSION addition:**
* What deploy infrastructure would make shipping this feature routine? (For SELECTIVE EXPANSION, assess whether accepted cherry-picks change the deployment risk profile.)

## Section 10: Long-Term Trajectory Review

Evaluate:
* **Technical debt introduced.** Code debt, operational debt, testing debt, documentation debt.
* **Path dependency.** Does this make future changes harder?
* **Knowledge concentration.** Documentation sufficient for a new engineer?
* **Reversibility.** Rate 1-5: 1 = one-way door, 5 = easily reversible.
* **Ecosystem fit.** Does this align with where the framework/ecosystem is heading?
* **The 1-year question.** Read this plan as a new engineer in 12 months — is it obvious?

**EXPANSION and SELECTIVE EXPANSION additions:**
* What comes after this ships? Phase 2? Phase 3? Does the architecture support that trajectory?
* Platform potential. Does this create capabilities other features can leverage?
* (SELECTIVE EXPANSION only) Retrospective: were the right cherry-picks accepted? Did any rejected expansions turn out to be load-bearing for the accepted ones?

## Section 11: Design & UX Review (skip if no UI scope detected)

The CEO calling in the designer. Not a pixel-level audit. This is ensuring the plan has design intentionality.

Evaluate:
* **Information architecture** — what does the user see first, second, third?
* **Interaction state coverage map:**
  `FEATURE | LOADING | EMPTY | ERROR | SUCCESS | PARTIAL`
* **User journey coherence** — storyboard the emotional arc
* **Generic-UI risk** — does the plan describe patterns any product could have, with nothing specific to this one?
* **Design system alignment** — does the plan match the project's stated design system?
* **Responsive intention** — is mobile mentioned or an afterthought?
* **Accessibility basics** — keyboard nav, screen readers, contrast, touch targets

**EXPANSION and SELECTIVE EXPANSION additions:**
* What would make this UI feel *inevitable*?
* What 30-minute UI touches would make users think "oh nice, they thought of that"?

Required ASCII diagram: user flow showing screens/states and transitions.

---

## CRITICAL RULE — How to ask questions

* **One issue = one AskUserQuestion call.** Never combine multiple issues into one question.
* Describe the problem concretely, with file and line references.
* Present 2-3 options, including "do nothing" where reasonable.
* For each option: effort, risk, and maintenance burden in one line.
* **Map the reasoning to the engineering preferences in SKILL.md.** One sentence connecting your recommendation to a specific preference.
* Label with issue NUMBER + option LETTER (e.g. "3A", "3B").
* **Zero findings:** if a section has zero findings, state "No issues, moving on" and proceed. Otherwise use AskUserQuestion for each finding — a finding with an "obvious fix" is still a finding.

---

## Required Outputs

### "NOT in scope" section
List work considered and explicitly deferred, with a one-line rationale each.

### "What already exists" section
List existing code/flows that partially solve sub-problems and whether the plan reuses them.

### "Dream state delta" section
Where this plan leaves us relative to the 12-month ideal.

### Error & Rescue Registry (from Section 2)
Complete table of every method that can fail, every exception class, rescued status, rescue action, user impact.

### Failure Modes Registry

```
  CODEPATH | FAILURE MODE   | RESCUED? | TEST? | USER SEES?     | LOGGED?
  ---------|----------------|----------|-------|----------------|--------
```

Any row with RESCUED=N, TEST=N, USER SEES=Silent → **CRITICAL GAP**.

### TODOS.md updates

Present each potential TODO as its own individual AskUserQuestion. Never batch TODOs — one per question. Never silently skip this step.

For each TODO, describe:
* **What:** One-line description of the work.
* **Why:** The concrete problem it solves or value it unlocks.
* **Pros:** What you gain by doing this work.
* **Cons:** Cost, complexity, or risks of doing it.
* **Context:** Enough detail that someone picking this up in 3 months understands the motivation, the current state, and where to start.
* **Effort estimate:** S/M/L/XL for a human team, with the agent-assisted equivalent (S→S, M→S, L→M, XL→L).
* **Priority:** P1/P2/P3
* **Depends on / blocked by:** Any prerequisites or ordering constraints.

Then present options: **A)** Add to TODOS.md **B)** Skip — not valuable enough **C)** Build it now in this PR instead of deferring.

### Scope Expansion Decisions (EXPANSION and SELECTIVE EXPANSION only)

Expansion opportunities and delight items were surfaced and decided in Step 0D. The decisions are persisted in the CEO plan document. Do not re-surface them — list them for completeness:
* Accepted: {list items added to scope}
* Deferred: {list items sent to TODOS.md}
* Skipped: {list items rejected}

### Diagrams (mandatory, produce all that apply)
1. System architecture
2. Data flow (including shadow paths)
3. State machine
4. Error flow
5. Deployment sequence
6. Rollback flowchart

### Stale Diagram Audit
List every ASCII diagram in files this plan touches. Still accurate?

### Completion Summary

```
  +====================================================================+
  |            MEGA PLAN REVIEW — COMPLETION SUMMARY                   |
  +====================================================================+
  | Mode selected        | EXPANSION / SELECTIVE / HOLD / REDUCTION    |
  | System Audit         | [key findings]                              |
  | Step 0               | [mode + key decisions]                      |
  | Section 1  (Arch)    | ___ issues found                            |
  | Section 2  (Errors)  | ___ error paths mapped, ___ GAPS            |
  | Section 3  (Security)| ___ issues found, ___ High severity         |
  | Section 4  (Data/UX) | ___ edge cases mapped, ___ unhandled        |
  | Section 5  (Quality) | ___ issues found                            |
  | Section 6  (Tests)   | Diagram produced, ___ gaps                  |
  | Section 7  (Perf)    | ___ issues found                            |
  | Section 8  (Observ)  | ___ gaps found                              |
  | Section 9  (Deploy)  | ___ risks flagged                           |
  | Section 10 (Future)  | Reversibility: _/5, debt items: ___         |
  | Section 11 (Design)  | ___ issues / SKIPPED (no UI scope)          |
  +--------------------------------------------------------------------+
  | NOT in scope         | written (___ items)                         |
  | What already exists  | written                                     |
  | Dream state delta    | written                                     |
  | Error/rescue registry| ___ methods, ___ CRITICAL GAPS              |
  | Failure modes        | ___ total, ___ CRITICAL GAPS                |
  | TODOS.md updates     | ___ items proposed                          |
  | Scope proposals      | ___ proposed, ___ accepted (EXP + SEL)      |
  | CEO plan             | written / skipped (HOLD/REDUCTION)          |
  | Diagrams produced    | ___ (list types)                            |
  | Stale diagrams found | ___                                         |
  | Unresolved decisions | ___ (listed below)                          |
  +====================================================================+
```

### Unresolved Decisions

If any AskUserQuestion goes unanswered, note it here. Never silently default.

---

## Next Steps

After the Completion Summary, recommend what comes next in one line:

* **UI scope was detected (Section 11 ran)** — recommend a design review of the live UI once it's built, since visual issues only surface with rendered output.
* **Scope expanded or architecture changed** — note that any prior engineering review of this plan is now stale.
* **Otherwise** — the plan is reviewed. Start building.

## Promote the CEO plan (EXPANSION and SELECTIVE EXPANSION only)

If the vision produced a compelling feature direction, the CEO plan at `docs/ceo-plans/` is already committed to the repo and visible to the team. If the user wants it as a first-class design doc instead, offer to move it to `docs/design/{feature}.md` and mark the original `status: PROMOTED`.
