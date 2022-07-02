## Snippet syntax

If snippets can be parsed as JSON, they will be automatically reformatted (pretty-printed) and set to use JSON code syntax colouring. Otherwise they will be printed as white text by default.

To use coloured syntax highlighting on your non-JSON code snippets, you need to tell rich-codex what syntax to use with the `--snippet-syntax` / `SNIPPET_SYNTAX` / `snippet_syntax` option (CLI, env/markdown, action/config).

Syntax highlighting is done using [rich](https://rich.readthedocs.io/en/latest/syntax.html) which uses [Pygments](https://pygments.org). Any language [supported by Pygments](https://pygments.org/languages/) should work.

## Hiding the command

By default, rich-codex shows a command prompt with the command that was used to generate the iamge.
This can be disabled by setting using `--hide-command` / `HIDE_COMMAND` / `hide_command` (CLI, env/markdown, action/config).

## Truncating content

If your tool produces a lot of output you can show just the beginning or end of output.
You can set the number of lines of output that you would like to show using: _(CLI, env/markdown, action/config)_

- `--head` / `RC_HEAD` / `head`
- `--tail` / `RC_TAIL` / `tail`

If the number you set is larger than the amount of output then all output will be shown as usual.

<!-- prettier-ignore-start -->
!!! tip
    Remember that you can set both head _and_ tail to remove just the middle section of output 🚀
<!-- prettier-ignore-end -->

By default, if any output is truncated a line will be printed: `[..truncated..]`.
You can customise this text using `--truncated-text` / `TRUNCATED_TEXT` / `truncated_text`.
Set it to `None` to omit the line completely.

## Trimming content

You can clean off unwanted content based on a string pattern match using `--trim-after` / `TRIM_AFTER` / `trim_after`.

Set it to a string - if that string is found in the input, no more lines will be printed after that.

No `truncated_text` is shown for this method currently (could be added if anyone wants it).
