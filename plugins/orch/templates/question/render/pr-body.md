[orch] This PR holds one decision of the orchestrator ({{origin}}). Approve, change or refuse it alone.

Question: {{question}}

Answer: {{answer}} ({{reason}})

Decision: `{{decision}}`, version {{version}}

Branch: `{{branch}}` on top of `{{base}}`{{#basePr}} (PR #{{basePr}}){{/basePr}}{{#replaces}}

It replaces PR #{{replaces}}, which is closed. Not reviewed yet.{{/replaces}}

Review it in the orchestrator: `orch review {{decision}} approve|change|refuse "<text>"`.
