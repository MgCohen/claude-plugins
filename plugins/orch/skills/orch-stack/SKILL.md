---
name: orch-stack
description: The git and PR steps of a default decision and of each review verdict (approve, change, refuse), with the orch decision and orch stack commands. Use it when an answer says "This is a default decision", or when a message starts with "Review of decision".
---

# Default decisions and reviews

A default decision lives on its own branch, `orch/decision-<id>`, on top of the branch before it. The user reviews each one alone. The commands keep the branches, the PRs and the store in step. Run them in your working folder.

## A default decision

1. Commit your current work on the current branch.
2. `orch decision start <id>` makes the decision branch on top of the current branch and checks it out.
3. Make the work of the decision and commit it.
4. `orch decision pr <id>` pushes the branch and opens a draft PR, if the repository has a GitHub remote.
5. Call `mcp__orch__report` with state `working`, and give the branch and the PR link.
6. Continue your later work on top of this branch.

## A review

| Verdict | Steps |
|---|---|
| approve | `orch decision ready <id>`. Do not merge unless the user asks. To merge, use `orch merge <pr>`, never `gh pr merge` |
| change | Check out the branch of the decision, make the change and commit it. Then `orch stack rebase <id>` |
| refuse | `orch stack close <id>`, then `orch decision start <id>` for the refused decision and for each closed decision above it, from the lowest to the highest. Do the work again in the direction of the user, reuse old commits with `git cherry-pick` where they fit, and run `orch decision pr <id>` for each |

After the steps, call `mcp__orch__report` with state `done`, and give each branch, its base and each PR state.

## Rules

- If the direction of the user is against `AGENTS.md`, follow the user and write the conflict in the PR comment and in the report.
- If `orch stack rebase` stops with a conflict, fix it by hand, then run the command again.
- Never delete a decision branch. A refused branch stays for reference.
- `orch status <session>` shows the stack of a session: each branch, its base, its state and its PR.
