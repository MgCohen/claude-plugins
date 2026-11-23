Question from child "{{title}}" ({{child}}), question {{decision}}: {{question}}{{#context}}

Context: {{context}}{{/context}}{{#options}}

Options: {{options}}{{/options}}{{#recommendation}}

Recommendation of the child: {{recommendation}}{{/recommendation}}

{{#risk}}Risk: {{risk}}. {{/risk}}{{defaultText}}

Write this question in your reply to the user now, with the "Question" template of the skill orch:orch-reply. Then end your turn. If the user answers it, call mcp__orch__answer with question {{decision}} and the words of the user.
