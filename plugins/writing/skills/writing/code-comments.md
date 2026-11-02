# Code comments and docstrings

A comment describes the code as it is now. Use the density and the form of the comments near it.

| Do not write | Write |
|---|---|
| "// Changed to use the cache." | "// Reads from the cache. The database is slow for this query." |
| "// Removed the old retry loop." | Nothing. Put the change in the commit. |
| "// Increment i." | Nothing. The code shows it. |
| "/// This method basically returns the index." | "/// Returns the card index." |

- Write why, not what. Comment only the parts that the code cannot show.
- Docstrings: start with a verb in the simple present ("Returns", "Starts").
- Do not refer to tickets, sessions or reviews, unless the repository does this.
- If you change code, rewrite or delete each comment that the change makes false.

## Check list

- No change words: "now", "no longer", "new", "old", "changed", "removed".
- Each comment is true for the current code.
