---
name: gr
description: "Run a complete Greptile CLI review, merge, and production deployment loop for the current pull request: inspect findings, fix every actionable issue, verify changes, re-review until clean, push, wait for every check, merge only when none are failed or pending, deploy through the repository's documented production path, and verify production. Use when the user invokes /gr or asks to run Greptile, address its review, merge a PR, and ship it."
---

# Greptile Review, Merge, and Deploy

Take the current PR from review through verified production deployment. Keep working until Greptile has no actionable findings, every current check is terminal without failures, GitHub reports the PR merged, the merged revision is deployed through the repository's documented production path, and production verification passes. A check being non-required does not make its failure safe to ignore.

## Resolve the PR and base

1. Read repository instructions and inspect the worktree before changing anything. Preserve unrelated user changes.
2. Resolve the current PR with `gh pr view --json number,url,headRefName,baseRefName,mergeStateStatus,statusCheckRollup`.
3. Fetch the PR base and head from `origin`.
4. Review against `origin/<baseRefName>`, never a possibly stale local base branch. Confirm the diff with `git diff --stat origin/<baseRefName>...HEAD`.
5. If the branch is behind its remote base, rebase or merge according to repository convention before the final review. Use guarded force-pushes (`--force-with-lease`) after rebasing.

## Run Greptile

1. Confirm the CLI is available and authenticated with `greptile --version` and `greptile whoami`.
2. Inspect repository review rules with `greptile config`.
3. Run a fresh machine-readable review:

   ```bash
   greptile review -b origin/<baseRefName> --json --instructions "Review rigorously for correctness, security, lifecycle races, data loss, performance regressions, error handling, and missing tests. Report every actionable issue; omit stylistic preferences."
   ```

4. If Greptile reports an implausibly large diff, stop that run and fix base resolution. Do not split valid work merely to satisfy a review computed against stale local `main`.
5. Use `greptile review --resume` only for an explicitly unfinished review. Use a fresh review after code changes.

## Address findings

For every finding:

1. Inspect the referenced code and surrounding contract.
2. Classify it as actionable or false positive using concrete evidence.
3. Fix actionable issues at the owning abstraction, add regression coverage, and avoid unrelated cleanup.
4. Retain a concise evidence note for false positives; do not change correct code merely to silence a reviewer.
5. Run focused tests after each logical fix.

After the batch, run the repository's full verification, including formatting/diff checks, type checking, and pre-commit hooks when the repository provides them. Obey repository-specific package-manager and build restrictions. Do not rely on branch protection to supply this list; repositories without required-check enforcement still need their relevant checks to pass.

Commit and push the fixes, then run Greptile again against the refreshed remote base. Repeat until the latest review contains zero actionable findings.

## Merge safely

1. Re-fetch the remote base immediately before the final push. Rebase again if it advanced, then repeat relevant tests and Greptile review.
2. Push with a normal push when fast-forwarding; use an explicit `--force-with-lease=<ref>:<expected-oid>` only after a rebase.
3. Wait for all checks with `gh pr checks <number> --watch --fail-fast`; never add `--required`. A nonzero exit is a merge blocker.
4. Inspect the final rollup with `gh pr checks <number> --json name,bucket,state,link`. Block the merge if any check is in the `fail`, `cancel`, or `pending` bucket. `skipping` is acceptable only when the job is genuinely inapplicable, not when it hides the repository's expected validation.
5. Confirm the expected repository validation actually appeared for the current head SHA. The absence of configured required checks is not evidence that validation passed. Never use an admin bypass to merge around a failing or missing check.
6. Use the repository's preferred merge method. Default to squash when the repository exposes no contrary convention:

   ```bash
   gh pr merge <number> --squash
   ```

7. Verify `gh pr view <number> --json state,mergedAt,mergeCommit` reports `MERGED` and that the merge commit is reachable from `origin/<baseRefName>`.

## Deploy and verify production

1. Deploy after the merge unless the user explicitly says not to deploy. A request to run this skill authorizes the repository's normal documented production deployment for the merged change.
2. Read and follow the repository's current deployment instructions. Validate required access, variables, secrets, and preflight checks before dispatching. Never guess a provider, workflow, environment, or credential.
3. Deploy only the services affected by the PR unless repository instructions require a wider rollout. Deploy the verified merge commit from the base branch, not the pre-merge PR head.
4. Wait for the deployment workflow and rollout to reach a terminal successful state. Treat failed, cancelled, timed-out, or missing expected deployment checks as blockers; diagnose and fix safe in-scope failures rather than reporting partial completion.
5. Run the repository's documented production smoke checks. Verify the deployed revision and the user-visible or system-visible behavior changed by the PR through the real production path, including CDN and origin checks when the repository requires both.
6. If the repository has no documented production path or required deployment authority is unavailable, stop and report the exact blocker rather than inventing a deployment method.

Do not report completion at an intermediate review, push, merge, dispatch, or green-check state. Completion requires a verified production deployment unless the user explicitly opted out of deployment.
