# Command-line

In addition to the GitHub Action, rich-codex is also a stand-alone command line tool.

You are welcome to use it locally, for example when first writing new documentation and generating initial images to check their output.

!!! danger "💥⚠️ **Warning** ⚠️💥"

    Please remember that rich-codex is designed to _**run arbitrary commands**_ that it finds within documentation for your project.

    You alone are responsible for any damage you cause to your computer! 🙃 Running rich-codex entirely within GitHub Actions is recommended 👍🏻

## Local installation

You can install `rich-codex` from the [Python Package Index (PyPI)](https://pypi.org/project/rich-codex/) with `pip` or equivalent.

```bash
pip install rich-codex
```

At its simplest, the command-line tool runs without any arguments and recursively searches the current working directory for anything it recognises:

```bash
rich-codex
```

Behaviour can be customised with command-line flags or by setting environment variables, see `rich-codex --help`:

<!-- RICH-CODEX
terminal_width: 120
notrim: true
extra_env:
  TERMINAL_WIDTH: 120
-->

![`rich-codex --help`](../img/rich-codex-cli-help.svg)

## Requirements for PNG outputs

Nothing extra. `PNG` output is rasterised by [resvg](https://github.com/linebender/resvg),
which ships as a self-contained wheel, so `pip install rich-codex` is the whole story on
every platform. Fira Code is bundled with rich-codex, so you don't need it installed
either — see [embedding the terminal font](../config/fonts.md).
