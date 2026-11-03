# Classify and fill

## Classify

1. Read the Signals table in `Triage · Kinds`.
2. Propose one kind, with a one-line reason.
3. When the owner accepts a kind:
   1. Read `Template · <Kind>`.
   2. Put its Form into the description. Keep the text that is already there under Intent.
   3. Move the label to `3 · Fill`.

## Fill

Fill the sections in Form order: first the base sections from `Triage · Kinds`, then the kind sections from the template. For each section, ask one question. Ask about optional sections too. The owner can skip them.

## Ask a question

Each question follows these rules:

1. Do research first: the target repo, Linear docs and specs, and related issues. In the repo, read the open branches and worktrees too (`git branch -a`, `git worktree list`), not only the default branch. Much work is not merged yet.
2. Propose an answer. Do not ask an open question if a proposal is possible.
3. Use a yes/no question, or a choice of 2 to 3 options.
4. Ask one question at a time.
5. Give the gate of the section, so the owner knows what "done" is.

## Promote

When the owner accepts or edits an answer:

1. Write the accepted text into the section of the parent description.
2. If the answer came from a sub-issue, set that sub-issue to Done.
3. Read the issue again to verify the text.
4. Check the gate of the section. If it passes, take the next open section.
5. If all required sections pass, move the label to `4 · Review`.
6. Add one comment to the parent: `Triage turn · <stage>: <what changed>`.

The parent description holds only accepted content. Put proposals, research and drafts in sub-issues or in chat.
