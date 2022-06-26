# Command / snippet behaviours

## Command time limits

As rich-codex runs commands within a non-interactive subshell, any command that requires input could cause the tool to hang forever.

To avoid this, rich-codex sets a maximum time limit on all commands (default: `5 seconds`). Once a command runs for this time, it is killed and the screenshot is created with whatever output was captured up to that point.

The amount of time that rich-codex waits for can be configured using `--timeout` / `TIMEOUT` / `timeout` (CLI, env/markdown, action/config).

## Snippet syntax

If snippets can be parsed as JSON, they will be automatically reformatted (pretty-printed) and set to use JSON code syntax colouring. Otherwise they will be printed as white text by default.

To use coloured syntax highlighting on your non-JSON code snippets, you need to tell rich-codex what syntax to use with the `--snippet-syntax` / `SNIPPET_SYNTAX` / `snippet_syntax` option (CLI, env/markdown, action/config).

Syntax highlighting is done using [rich](https://rich.readthedocs.io/en/latest/syntax.html) which uses [Pygments](https://pygments.org). Any language [supported by Pygments](https://pygments.org/languages/) should work.
