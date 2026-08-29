# Contributing

Chomsky Stack accepts skills, and only skills.

## The bar

1. Put an executable `SKILL.md` under `skills/<skill-name>/`. Do not submit an essay with frontmatter.
2. Add judgment a capable model would not reliably produce unprompted. Context is scarce; generic advice makes every other skill worse.
3. Read and stand behind every line. Agent-assisted drafts are welcome; unread agent output is not.
4. Take a position and say what evidence would change it. "Consider the tradeoffs" is not a decision.
5. Stay minimal. No telemetry, state directory, setup script, update checker, daemon, or cross-skill runtime.

## Shape of a skill

```text
skills/<skill-name>/
├── SKILL.md
├── agents/openai.yaml       # optional UI metadata
└── sections/<phase>.md      # optional long phase, read on demand
```

Every `SKILL.md` needs lowercase hyphenated `name` and a `description` that explains both what it does and when it should trigger. Keep the body imperative and readable in one sitting. Split long phases into `sections/` and link them at the exact point they are needed.

## Attribution

Preserve existing credits. Add a short byline to original skills or document the contribution in the repository attribution.

## Before opening a PR

- [ ] I read every changed line.
- [ ] Every skill passes the Codex skill validator.
- [ ] The skill is opinionated and executable end to end.
- [ ] It writes only where the user expects.
- [ ] I exercised it on a representative task or documented why direct execution does not apply.

Contributions are MIT.
