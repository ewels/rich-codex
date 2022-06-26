## Using a pseudo-terminal

By default, rich-codex runs commands in a Python `subprocess`. This is not an interactive termainal, and as such many command-line tools will disable coloured output.

This is best solved at the tool level if possible, by telling the tool to force coloured output. However, if this is not possible then you can use the `--use-pty` flag / `USE_PTY` env var. This uses a [Python `pty` pseudo-terminal](https://docs.python.org/dev/library/pty.html) instead of [`subprocess`](https://docs.python.org/dev/library/subprocess.html) which may trick your tool into keeping coloured output.

<!-- prettier-ignore-start -->
!!! warning
    Note that PTY almost certainly won't work on Windows and is generally more likely to do weird stuff / create poorly formatted outputs than the default subprocess shell.
<!-- prettier-ignore-end -->

## Colour theme

You can customise the theme using `--terminal-theme` / `$TERMINAL_THEME` / `terminal_theme` (CLI / env / action).

Themes are taken from [Rich](https://github.com/Textualize/rich/blob/master/rich/terminal_theme.py), at the time of writing the following are available:

- `DEFAULT_TERMINAL_THEME`
- `MONOKAI`
- `DIMMED_MONOKAI`
- `NIGHT_OWLISH`
- `SVG_EXPORT_THEME`

The terminal theme should be set as a string to one of these values.

It's planned to add support for custom themes but not yet implemented. If you need this, please create a GitHub issue / pull-request.
