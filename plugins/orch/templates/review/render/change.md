Review of decision {{decision}} ({{question}}): change requested.{{#text}} The user said: {{text}}{{/text}}
1. Check out `{{branch}}`, make the change and commit it.
2. Run `orch stack rebase {{decision}}`. It rebases each branch that is stacked above `{{branch}}` and pushes the branches that have a remote.
3. Call mcp__orch__report with state done, and give each branch, its base and each PR state.
