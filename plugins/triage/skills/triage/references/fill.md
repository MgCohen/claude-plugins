# Classify and fill

## Classify

1. Read the Kinds table in `Triage · Kinds`.
2. Propose one kind, with a one-line reason.
3. When the owner accepts a kind:
   1. Find the Approved Templates row `Ask · <Kind>`.
   2. Apply it to the ask page with `apply_template`. The Form goes below Words and Context.
   3. Fetch the page until the Form is there.
   4. Set Kind, set the Template relation to the kind template, and set Status to Fill.

## Fill

Fill the sections in Form order: first the base sections, then the kind sections from `Triage · Kinds`. Placement is the Project property, not a page section. For each section, ask one question. Ask about optional sections too. The owner can skip them.

## Ask a question

Each question follows these rules:

1. Do research first: the target repo, the Docs rows, and related rows in Projects, Features, Plans, Bugs and Decisions. In the repo, read the open branches and worktrees too (`git branch -a`, `git worktree list`), not only the default branch. Much work is not merged yet.
2. Propose an answer. Do not ask an open question if a proposal is possible.
3. Use a yes/no question, or a choice of 2 to 3 options.
4. Ask one question at a time.
5. Give the gate of the section, so the owner knows what "done" is.

## Promote

When the owner accepts or edits an answer:

1. Write the accepted text into the section of the ask page. Delete the instruction line of that section.
2. If the answer came from a sub-ask, set that sub-ask to Converted.
3. Fetch the page again to verify the text.
4. Check the gate of the section. If it passes, take the next open section.
5. If all required sections pass, set Status to Review.
6. Add one comment to the ask page: `Triage turn · <status>: <what changed>`.

The ask page holds only accepted content. Put proposals, research and drafts in sub-asks or in chat.
