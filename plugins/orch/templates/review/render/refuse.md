Review of decision {{decision}} ({{question}}): refused.{{#text}} The user said: {{text}}{{/text}}
1. Run `orch stack close {{decision}}`. It closes the PR of `{{branch}}` and each PR stacked above it with a comment, keeps the branches, makes a new version of each closed decision, and checks out `{{base}}`.
2. Run `orch decision start {{decision}}`. It makes `{{nextBranch}}`. Do the work of this decision again, in the direction that the user gave, and commit it. Then run `orch decision pr {{decision}}`.
3. For each other decision that step 1 closed, from the lowest to the highest: run `orch decision start <id>`, reuse its old commit with `git cherry-pick` where it still fits, then run `orch decision pr <id>`.
4. Call mcp__orch__report with state done, and give each branch, its base and each PR state.
