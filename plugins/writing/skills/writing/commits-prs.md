# Commit messages and PR descriptions

These texts record a change. History is correct here: what changed, and why.

## Commit message

- Subject line: imperative, 50 characters maximum, no period. "Add the retry limit to the queue."
- Body: why the change is necessary, then what it changes. Wrap at 72 characters.
- If the change removes or replaces something, name it and give the reason.

## PR description

- If the repository has a PR template, use its headings.
- Start with a summary of 3 sentences maximum: the result of the change.
- Show the changes as a table or a list: part, change, reason.
- Give the test steps as a numbered list.
- Do not repeat the diff. Give the reason and the effect.

## Check list

- The reason for each removal or replacement is in the text.
- The documents that the change touches describe the current state only (`documents.md`).
