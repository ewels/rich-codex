# Terminal Width

## Trimming

By default, rich-codex will run your command / parse your snippet and check the length of all output lines. The terminal width will be set to that of the longest line.

A mimimum width is used to prevent very narrow images. The default for this is `80` characters and can be customised using `--terminal-min-width` / `TERMINAL_MIN_WIDTH` / `terminal_min_width` (CLI, env/markdown, action/config).

To turn off trimming, use `--notrim` / `NOTRIM` / `notrim`.

<!-- prettier-ignore-start -->
!!! info
    Note that console output that is _padded_ with spaces will use the full terminal width available. Much of the output from the rich library is padded.

    In these cases, you will need to consult the upstream tool on how to set terminal width and match that in rich-codex.
<!-- prettier-ignore-end -->

## Fixing terminal width

You can define a specific width to use for the terminal image using `--terminal-width` / `TERMINAL_WIDTH` / `terminal_width` (CLI, env/markdown, action/config). This is typically joined with `--notrim` to disable automatic trimming.

If your console output doesn't match this width, you may get weird effects such as cropping or wrapping. You will probably want to try to match this width with upstream tools.

<!-- prettier-ignore-start -->
!!! tip
    Some tools (such as [rich-click](https://github.com/ewels/rich-click)) also honour the environment variable `$TERMINAL_WIDTH`
<!-- prettier-ignore-end -->
