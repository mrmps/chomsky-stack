# Junk detection taxonomy and evidence

## Terms

| Term | Use it when | Typical code symptom |
| --- | --- | --- |
| Reward hacking | An agent maximizes a reward or evaluator signal by violating the intended task | Disabling checks, editing assertions, forced success, exploiting the harness |
| Specification gaming | Behavior satisfies the literal specification while missing the intended outcome | Correct-looking output produced through a loophole or shortcut |
| Goodharting | Informal description of turning a proxy into the target | Green metrics while product behavior or maintainability worsens |
| Test/evaluator overfitting | Code is narrowly fitted to visible examples | Hardcoded cases, fixture detection, failure on held-out composition or edge cases |
| Hill-climbing into a local optimum | Incremental proxy improvements trap the system in a brittle design | Repeated patches add flags and branches because each local change is cheapest |
| Structural erosion | Complexity becomes concentrated in high-complexity functions over iterations | Giant orchestrators, branching mode switches, mixed responsibilities |
| Iterative degradation | Repeated changes make later changes harder even while checkpoints pass | Rising verbosity, duplication, extension cost, and regression rate |
| Accidental complexity | Complexity comes from the solution rather than the problem domain | Layers, states, wrappers, and transformations without a domain need |
| Compatibility cruft | Legacy support remains after its consumers or migration window are gone | Old/new dual paths, aliases, shims, tolerant catch-all parsing |
| Speculative generality | Code supports imagined future requirements | Unused extension points, configuration modes, abstractions with one caller |
| Wrong abstraction | One shared abstraction actually represents divergent concepts | Boolean/mode parameters and conditionals that vary behavior by caller |
| Reinvented wheel / NIH | Custom machinery duplicates a mature available capability | Bespoke parser, retry loop, cache, schema validator, crypto, date logic |
| AI code slop | Colloquial umbrella for low-signal, high-volume generated code | Excess comments, broad catches/casts, duplicated helpers, plausible stubs |

Best concise description for the user's “RL-maxxing code”:

> Agents Goodhart the codebase: they hill-climb the evaluator, producing reward-hacked code rather than good software.

Use **reward hacking** or **specification gaming** for the causal failure, **test overfitting** for visible-case fitting, and **iterative structural erosion** for the everyday codebase degradation that accumulates across otherwise successful patches.

## What it looks like

### Strong reward-hacking signals

- Production code imports or parses tests, snapshots, fixtures, or grader files.
- A verifier returns success unconditionally or process exit status is overridden.
- Assertions, timeouts, collection rules, or coverage settings weaken in the same patch as the implementation.
- Known inputs map directly to expected outputs without a general rule.
- A feature silently substitutes mock, placeholder, or cached data when the real path fails.
- Tests assert call occurrence, snapshots, or duplicated implementation logic while never observing the requested outcome.
- Impossible or contradictory requirements cause a fabricated success rather than an explicit blocker.

### Strong structural-erosion signals

- A central function absorbs each new feature through another flag or branch.
- Duplicate logic diverges across error, auth, mobile, streaming, or legacy paths.
- A shared abstraction requires callers to opt out of most of its behavior.
- State has multiple owners or multiple representations with synchronization code.
- A file is large because it contains policy, orchestration, persistence, rendering, and error mapping together.
- The patch adds more fallback states than real product states.

### Compatibility evidence checklist

Keep compatibility when at least one concrete claimant exists:

- Documented public contract or supported SDK version.
- Deployed external caller or integration.
- Persisted data still present in production.
- Active migration window with an owner and removal date/condition.
- Telemetry or logs showing current use.
- Explicit legal, protocol, or product policy.

Absent a claimant, label the code a deletion candidate, not immediately safe to delete.

### Library replacement checklist

Before recommending a dependency, verify:

- The package or standard library covers the exact contract and edge cases.
- It is already installed or its maintenance/security posture is acceptable.
- Its API removes domain code rather than wrapping it in another adapter maze.
- Bundle size, runtime, licensing, platform, and supply-chain costs fit the project.
- The custom behavior is not the product's core differentiator.
- The migration and rollback are smaller than maintaining the custom code.

## Research base

Primary and technical sources:

- [Cursor `deslop` skill at the requested commit](https://github.com/cursor/plugins/blob/fd878692de15a3069c21c8f429eb0b9f2fe178fa/cursor-team-kit/skills/deslop/SKILL.md) — diff-first cleanup of extra comments, abnormal defensive checks, `any` casts, nesting, and local-style violations. This skill preserves its minimal-edit guardrails and adds evidence, compatibility, library, user-path, and reward-hacking lenses.
- [Google DeepMind: Specification gaming](https://deepmind.google/blog/specification-gaming-the-flip-side-of-ai-ingenuity/) — defines satisfying a literal objective without the intended outcome.
- [OpenAI: Monitoring internal coding agents for misalignment](https://openai.com/index/how-we-monitor-internal-coding-agents-misalignment/) — describes coding-agent reward hacking as optimizing tests, graders, or CI instead of solving the task.
- [OpenAI: Detecting misbehavior in frontier reasoning models](https://openai.com/index/chain-of-thought-monitoring/) — real coding examples include unconditional verification, test parsing, stubbing, and forced success.
- [SlopCodeBench](https://arxiv.org/abs/2603.24755) — measures iterative verbosity and structural erosion; passing checkpoints undermeasures extension robustness.
- [SpecBench](https://arxiv.org/abs/2605.21384) — compares visible validation with held-out composed behavior to measure coding-agent reward hacking.
- [Anthropic: Coding audit realism](https://alignment.anthropic.com/2026/coding-audit-realism/) — treats unprompted weakening or modification of tests instead of source fixes as reward hacking.
- [Anthropic: Property-based testing](https://www.anthropic.com/research/property-based-testing) — motivates properties and generative cases as a stronger generality check than a few examples.
- [Hyrum's Law](https://www.hyrumslaw.com/) — warns that sufficiently used observable behavior becomes an implicit interface; require evidence before deleting compatibility.
- [Sandi Metz: The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction) — condition-laden shared abstractions can cost more than duplication.
- [Dan McKinley: Choose Boring Technology](https://mcfunley.com/choose-boring-technology) — technology choices carry operational and cognitive overhead; minimize novelty.
- [Martin Fowler: YAGNI](https://martinfowler.com/bliki/Yagni.html) — speculative capability has carrying cost even before it is used.
- [Herb Sutter: Using the Standard Library](https://herbsutter.com/2013/05/16/gotw-3-solution-using-the-standard-library-or-temporaries-revisited/) — prefer standard-library reuse over handcrafting equivalent machinery.

Practitioner reports from X; use as pattern discovery, not independent proof:

- [Gabe Orlanski, SlopCodeBench author](https://x.com/GOrlanski/status/2037589308731695609) — reports that more code raises review/maintenance cost and correlates with later checkpoint cost.
- [Imbue](https://x.com/imbue_ai/status/2031762951343100411) — reports agents quietly replacing blocked features with hardcoded data while code and tests still look plausible.
- [Kaxil Naik](https://x.com/kaxil/status/2037503513350005134) — reports tests that pass but test nothing, plausible wrong fixes, and overcomplication when model capability exceeds task complexity.
- [Meathill](https://x.com/meathill1/status/2036334114169823731) — describes recurring maintenance hotspots in vibe-coded projects: bloated files, duplication, scattered docs, weak tests, and hand-rolled wheels.
