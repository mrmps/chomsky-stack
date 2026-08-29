# Chomsky Stack

Six opinionated agent skills for deciding what to build, keeping it simple, writing without fluff, and proving that shipped work actually works.

Created by [Michael Ryaboy](https://x.com/michael_chomsky) (`@michael_chomsky`). Modeled after [better-gstack](https://github.com/mrmps/better-gstack), with all of its skills included.

```bash
npx skills add mrmps/chomsky-stack
```

## Skills

| Skill | What it does |
|---|---|
| `office-hours` | Tests demand, the status quo, user specificity, the narrowest wedge, observed behavior, and future fit before code is written. |
| `plan-ceo-review` | Reviews whether a plan should expand, hold, or shrink, then pressure-tests its execution. |
| `unsummarizable` | Removes fluff until taking out more words would remove interesting ideas. |
| `complexity` | Reads [How Complex Systems Fail](https://how.complexsystems.fail/) and minimizes complexity. |
| `meaningful-contribution` | Requires behavior-changing work to be demonstrated with direct evidence, regression coverage, and edge-case checks. |
| `gr` | Runs the full Greptile review, fix, verification, merge, deployment, and production-validation loop. |

## Install

Install everything:

```bash
npx skills add mrmps/chomsky-stack
```

Install one skill:

```bash
npx skills add mrmps/chomsky-stack --skill unsummarizable
```

Or clone and copy the folders into any agent that reads `SKILL.md`:

```bash
git clone https://github.com/mrmps/chomsky-stack.git
cp -r chomsky-stack/skills/* ~/.claude/skills/
```

## Shape

```text
skills/
├── complexity/
├── gr/
├── meaningful-contribution/
├── office-hours/
├── plan-ceo-review/
└── unsummarizable/
```

There is no runtime, telemetry, state directory, setup script, update checker, daemon, or cross-skill runtime. The repository is only skills and their directly supporting files.

## Attribution

`office-hours` and `plan-ceo-review` come from [better-gstack](https://github.com/mrmps/better-gstack), an independent minimal fork of [Garry Tan's gstack](https://github.com/garrytan/gstack). Their methodology and much of their text are Garry Tan's; he has not endorsed or reviewed Chomsky Stack.

`unsummarizable` is inspired by [Paul Graham's description of unsummarizable writing](https://x.com/paulg/status/2062891972042637573).

`gr`, `meaningful-contribution`, `complexity`, `unsummarizable`, and this compilation are by [Michael Ryaboy](https://x.com/michael_chomsky).

## License

MIT. See [LICENSE](LICENSE).
