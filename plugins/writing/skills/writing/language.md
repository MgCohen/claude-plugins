# Language

The core STE rules are in the output style (and in the subagent context). This file adds examples.
For a word that you are not sure about, read `words.md`.

## Examples

| Rule | Write | Do not write |
|---|---|---|
| Imperative | "Run the gate." | "You should run the gate." |
| Active voice | "The hook adds the context." | "The context is added." |
| Condition first | "If the gate fails, read the report." | "Read the report if it fails." |
| Noun clusters | "the report of the gate failure" | "gate failure report file path" |
| Approved words | "use", "start" | "utilize", "commence" |
| Code comments | "Returns the card index." | "This basically returns..." |

- Do not use synonyms for variety. Use "None" for no value and "forbidden" for not permitted.
- Do not use an abbreviation of a term in a label ("refs" for "references").
- Write list items and table cells of the same type in the same form.
- Warnings: start with a command, then give the risk.

## Edits to existing text

- Write your new sentences in STE. Do not rewrite other text, unless the user asks for an STE pass.
- STE pass: keep the meaning, the structure and the technical names. Then list the changes that
  could change the meaning.

## Check list

- One term for each idea.
- No phrasal verbs, no `-ing` forms as verbs, no contractions.
- Sentence and paragraph lengths from the output style.
