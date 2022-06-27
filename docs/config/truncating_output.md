## Hiding the command

By default, rich-codex shows a command prompt with the command that was used to generate the iamge.
This can be disabled by setting using `--hide-command` / `HIDE_COMMAND` / `hide_command` (CLI, env/markdown, action/config).

## Heads and tails

If your tool produces a lot of output you can show just the beginning, end or beginning + end.
You can set the number of lines of output that you would like to show using: _(CLI, env/markdown, action/config)_

- `--head` / `RC_HEAD` / `head`
- `--tail` / `RC_TAIL` / `tail`

If the number you set is larger than the amount of output then all output will be shown as usual.

By default, if any output is truncated a line will be printed: `[..truncated..]`.
You can customise this text using `--truncated-text` / `TRUNCATED_TEXT` / `truncated_text`.
Set it to `None` to omit the line completely.
