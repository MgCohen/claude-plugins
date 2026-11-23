This session runs in the cloud. The orch plugin tools do not work here. Use the `orch` command: it sends each call to the store API of the supervisor (`ORCH_URL`). Your party is `session:{{session}}`.

- Update: `orch post update --from session:{{session}} --to user --summary "<text>"`
- Question: `orch post question --from session:{{session}} --to user --thread <a new id> --needs answer --json <file>`, with the fields of `orch template question`. Then end your turn. The answer arrives as a new message.
- Report: `orch post report --from session:{{session}} --to user --needs ack --state done --summary "<text>"`. Use `--json <file>` for the lists `done`, `next`, `blockers` and `links`.

If `orch` is not on the PATH or a call fails, write the error in your reply and end your turn.
