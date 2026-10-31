# Layout rules — terms, tables, graphs, documents and splits

These are house rules of this plugin. They are not part of ASD-STE100. They apply to all output
that is more than a short reply: documents, artifacts, pages, READMEs, reports and slides.

## Terms

A long text has many parts: headings, labels, legends, table cells and body text. Each part can
drift to a different word for the same idea. These rules stop that drift.

1. Before you write, list the key terms of the text. Give each idea one term only.
2. Define each key term one time, at its first use or in a short glossary.
3. Use exactly that term in all headings, labels, legends, table cells, captions and buttons.
4. Do not use abbreviations of a term ("refs" for "references") in labels.
5. Use one term for "no value" ("None"). Use it in all tables.
6. Use one term for "not permitted" ("forbidden" or "must not use"). Do not mix them.

## Visuals first

Use a visual before prose. Write prose only for the parts that a visual cannot show.

| Content | Use |
|---|---|
| A sequence of steps or states | Flow graph |
| Calls between functions or services | Call stack or sequence diagram |
| Parts and their dependencies | Dependency graph |
| Numbers, trends or comparisons | Chart |
| Items with the same attributes | Table |
| Code behavior or an API | Code snippet |
| A command to run | Command block |

- **Replace, do not add.** When you add a visual, delete the prose that says the same thing. A
  visual and a paragraph with the same content is a fault.
- If a paragraph describes a flow, a call order or a structure, replace it with a visual.
- **Minimum size.** A diagram needs 3 nodes or more. A table needs 3 rows or more. If the content
  is smaller, write one sentence.
- **Prose share.** Outside code blocks, prose is 50% of the words maximum. The other words are in
  tables, diagrams and lists.
- Give each visual a title that states its message. Add one or two sentences only if the visual
  needs them.
- Keep snippets short: the lines that show the point, not the full file.
- In a reply, a short table, list or snippet is also a visual. Use it before prose.

## Sentences and paragraphs

| Item | Maximum |
|---|---|
| Procedure sentence | 15 words |
| Descriptive sentence | 20 words |
| Paragraph | 4 sentences, 60 words |
| Actions in one sentence | 1 (2 only if you must do them at the same time) |

- Write list items and table cells of the same type with the same structure. Use all fragments or
  all full sentences. Do not mix them.
- Do not refer to the session, the chat or "the briefing" in a document. The reader of a document
  does not see the session. Give the name of the source.

## Tables

- Use a table when three or more items share two or more attributes.
- Maximum: 6 columns and 15 rows.
- Headers: noun phrases, 3 words maximum. Put the unit in the header: "Size (KB)".
- Cells: fragments, 8 words maximum. A cell that needs a sentence belongs in the body text.
- Do not put a fragment and a sentence in the same cell.
- Do not leave a cell empty. Write the "no value" term ("None").
- If a cell lists more than three items, use a list below the table, or split the row.
- If a table has more than 15 rows, split it by group, or move it to its own tab.

## Graphs, charts and diagrams

- Show one message in each chart. The title gives that message: "Cards in each zone after the
  draw step".
- Maximum: 5 series and 12 categories in each chart.
- Labels: 4 words maximum. Put labels on the data, not in a legend, when possible.
- Edge labels for actions: one verb in the simple present ("sends", "reads", "starts").
- Diagrams: 10 nodes maximum. If a diagram has more nodes, split it by layer or by step.
- Node, edge and legend labels use the key terms of the text. They do not use synonyms.

## Documents

- Start with a summary of 3 sentences maximum. Give the result or the decision first.
- Use 3 heading levels maximum.
- Add a heading at least every 250 words.
- Sections: 300 words maximum.
- Lists: 7 items maximum, and 2 levels of nesting maximum.
- Use the same structure for blocks of the same type (for example: Purpose, Path, Contains, Uses).

## Foldables

A document often has a segment that repeats for each item: one block for each layer, finding,
endpoint, module or step. Put each of these blocks in a foldable.

- Use a foldable for each item when a segment has three or more items with the same structure.
- The foldable title shows the item name and one key fact: "Domain · VSA.Domain, Notes.Domain".
- Keep all foldables closed at the start. Add "Open all" and "Close all" when there are five or
  more items.
- Put the summary of all items (a table or a graph) before the foldables, and keep it open.
- In HTML, use `<details>` and `<summary>`. In Markdown, use `<details>` and `<summary>` too.
- Do not put the main message or a warning in a foldable. The reader must see it without a click.

## Splits

| Output | Limit | If the output is longer |
|---|---|---|
| Chat reply | 150 words (target) | If more than 400 words, write an artifact or a file. |
| Document or page | 1,500 words, or 7 top-level sections | Split into tabs. Use documents only for different readers. |
| Section | 300 words | Split into two sections. |
| Table | 15 rows | Split by group, or move to a tab. |
| Diagram | 10 nodes | Split by layer or by step. |

If a document is too long, split it into **tabs** first. Tabs are the default split.

- Use tabs when the parts are for the same reader and the same purpose. Example: "Overview",
  "Rules", "Details".
- The first tab is the overview: the summary and the main visual.
- Give each tab a short noun phrase as its name, 2 words maximum.
- Use 2 to 6 tabs. If you need more, use separate documents.

Use **separate documents** only when the parts are for different readers, or change at different
times. Link each document to the others.

Code blocks do not count in the word limits. Long code examples can go in a tab of their own.

## Markdown documents

Markdown has no tabs. If a Markdown document is longer than the limits, do one of these:

1. **Split into linked files (default).** Put the files in one folder. Add an index file with the
   summary, the main visual and a link to each file. Each file has one topic.
2. **One file only.** If the user asks for one file, or gives one path, keep the summary and the
   main visual open. Put each large section (more than 300 words) in a foldable.

- Use `<details>` only when the reader uses GitHub or a browser. Some editors show `<details>` as
  plain text. If you are not sure, split into files.
- A long single file is not permitted. Shorten it, or use one of the two options above.
