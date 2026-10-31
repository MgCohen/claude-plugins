---
name: technical-english
description: Write in ASD-STE100 Simplified Technical English (STE). Use it for every reply and for all text that you write or edit, including files, docs, commits, PRs, artifacts and slides. Load it before you write a document or an artifact. Also load it when the user asks for "technical English", "STE" or "ASD-STE100".
---

# Technical English (ASD-STE100)

STE is a controlled language with a restricted dictionary and a set of writing rules. It makes text
clear, short and with one meaning only, also for readers whose first language is not English.

## Which file to read

| Output | Read |
|---|---|
| Reply or short text | This file only |
| Document, artifact or slides | This file, then `references/layout.md` |
| A word that you are not sure about | `references/words.md` |
| A question about the ASD-STE100 standard | `references/rules.md` |

## Core rules

<!-- generated:core from rules/core.md -->
Write all prose in ASD-STE100 Simplified Technical English (STE). This includes replies, files, comments, commit messages, PR text, artifacts and diagram labels. Code, commands, paths, quotes and error text do not change.

1. One word, one meaning. Use simple approved words ("use", "start", "make sure", "about"). Keep technical names exactly as they are.
2. Terms: give each idea one term. Use that term in all headings, labels, legends and table cells.
3. Sentences: procedures 15 words maximum, descriptions 20 words maximum. One topic in each sentence.
4. Paragraphs: one topic, four sentences and 60 words maximum.
5. Instructions: imperative form, one action in each sentence, condition first ("If X, do Y.").
6. Active voice and simple tenses. No `-ing` forms as verbs. No contractions. No filler.
7. No phrasal verbs: set up → prepare, carry out → do, find out → find, look into → examine, go through → use, get to → reach, point out → show, end up → become, fill in → write, turn on → start.
8. Noun clusters: three nouns maximum in a row.
9. Lists: numbered lists for steps, bulleted lists for three or more items.
10. Order: the answer or the result first, then the reason.
11. Visuals first: use a flow graph, a call stack, a chart, a table or a code snippet before prose. Delete prose that repeats a visual.
12. Documents, artifacts and long files: load the `technical-english` skill before you write. Do its review before you deliver.
<!-- /generated:core -->

## Language rules in detail

### Words and terms

- Use a word only in its approved meaning and part of speech. Do not use synonyms for variety.
- Use the short common word, not the long or formal one: `use`, not `utilize`; `start`, not
  `commence`. See `references/words.md`.
- Names of code, tools, APIs, files, types and domain terms are technical names. Keep them exactly
  as they are.
- In a long text, list the key terms before you write. Define each term one time, at its first use
  or in a short glossary.
- Do not use an abbreviation of a term in a label ("refs" for "references").
- Use one term for "no value" ("None"), and one term for "not permitted" ("forbidden").

### Sentences

| Item | Maximum |
|---|---|
| Procedure sentence | 15 words |
| Descriptive sentence | 20 words |
| Paragraph | 4 sentences, 60 words |
| Actions in one sentence | 1 (2 only if you do them at the same time) |

These limits are stricter than ASD-STE100 (20 and 25 words, 6 sentences). They are house rules.

- **Imperative:** "Run the gate." Not "You should run the gate" or "The gate should be run."
- **Active voice:** "The hook adds the context." Use the passive only in descriptive text, and only
  when the agent is not known or not important.
- **Condition first:** "If the gate fails, read the report."
- **Noun clusters:** "the report of the gate failure", not "gate failure report file path".
- **Same structure:** write list items and table cells of the same type in the same form. Use all
  fragments or all full sentences.
- **Warnings:** start with a clear command, then give the risk.

## How to apply it

### Replies

- Give the answer or the result first. Then give the reason.
- Code, commands, paths, error text and quotes stay exactly as they are.
- Do not tell the user that you use STE.

### Files

- New text: write it in STE.
- Edits: write your new or changed sentences in STE. Do not rewrite other text, unless the user asks
  for an STE pass.
- STE pass: keep the meaning, the structure and the technical names. Change only the language.
  Then give a short list of the changes that could change the meaning.
- Code comments: short, imperative or simple present. "Returns the card index."

### Documents and artifacts

Read `references/layout.md` before you write. It has the rules for visuals, tables, graphs,
foldables, tabs and long documents.

- All visible text follows STE: titles, headings, captions, buttons, tooltips, error messages, SVG
  labels and `aria-label` text.
- Titles: short noun phrases. Buttons: one verb in the imperative ("Save", "Open").
- Slides: one idea in each bullet.

### Subagents

- Write each subagent prompt in STE. Tell the subagent to write its report and its files in STE.
- If a subagent report is not in STE, rewrite the parts that you show to the user.

## Review before you deliver

<!-- generated:review from rules/review.md -->
Do this review if the text has more than 150 words of prose. Examine the full text before you tell the user that it is done.

1. Terms: find all words for each key idea. If one idea has two or more words ("uses" / "references" / "refs"), use one.
2. Phrasal verbs: replace each one with one verb. See `references/words.md`.
3. Sentences and paragraphs: procedures 15 words, descriptions 20 words, paragraphs 4 sentences maximum.
4. Visuals: replace prose that describes a flow, a call order or a structure with a visual. Delete prose that repeats a visual. Prose is 50% of the words maximum.
5. Tables: 6 columns and 15 rows maximum. Cells are fragments of 8 words maximum. No empty cells.
6. Graphs: labels 4 words maximum. Diagrams have 3 to 10 nodes.
7. Length: if the text has more than 1,500 words or 7 top-level sections, use the decision flow in `references/layout.md`.
8. Foldables: put each repeated item segment (3 or more items with the same structure) in a foldable.
9. Repeats: each fact has one place. Other parts link to it. An index has only the summary, the main visual and links.
10. Session: remove references to the session or the chat ("in this session", "the briefing").
<!-- /generated:review -->

## When not to apply it

- Text that the user writes, quotes, error messages, log lines and code: keep them as they are.
- If the user asks for a different style for one output, use that style for that output only.
- Non-English output: keep the principles (short sentences, one meaning, active voice, imperative),
  but do not translate the dictionary.
