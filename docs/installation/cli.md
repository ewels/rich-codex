# Command-line

In addition to the GitHub Action, rich-codex is also a stand-alone command line tool.

You are welcome to use it locally, for example when first writing new documentation and generating initial images to check their output.

!!! danger "💥⚠️ **Warning** ⚠️💥"

    Please remember that rich-codex is designed to _**run arbitrary commands**_ that it finds within documentation for your project.

    You alone are responsible for any damage you cause to your computer! 🙃 Running rich-codex entirely within GitHub Actions is recommended 👍🏻

## Local installation

You can install `rich-codex` from the [Python Package Index (PyPI)](https://pypi.org/project/rich-codex/) with `pip` or equivalent.

```bash
pip install rich-click
```

At its simplest, the command-line tool runs without any arguments and recursively searches the current working directory for anything it recognises:

```bash
rich-codex
```

Behaviour can be customised with command-line flags or by setting environment variables, see `rich-codex --help`:

![`rich-codex --help`](../img/rich-codex-help.svg)

## Requirements for PNG / PDF outputs

If you wish to generate `PNG` or `PDF` images (not just `SVG`) then there are a few additional requirements. Conversion is done using [CairoSVG](https://cairosvg.org/). First, install rich-click with the `cairo` [extra](https://packaging.python.org/en/latest/tutorials/installing-packages/#installing-setuptools-extras):

```bash
pip install rich-click[cairo]
```

You'll then probably need some additional libraries, see the [Cairo documentation](https://cairosvg.org/documentation/):

> CairoSVG and its dependencies may require additional tools during the installation: a compiler, Python headers, Cairo, and FFI headers. These tools have different names depending on the OS you are using, but:
>
> - on Windows, you’ll have to install Visual C++ compiler for Python and Cairo;
> - on macOS, you’ll have to install cairo and libffi (eg. with [Homebrew](https://brew.sh): `brew install cairo`);
> - on Linux, you’ll have to install the cairo, python3-dev and libffi-dev packages (names may vary for your distribution).

Installation can be messy, so be prepared to do a bit of googling to get things to work. Remember that running rich-codex with the `-v` flag to get verbose logging can give you more information about what's going wrong (if anything).

You'll also need Fira Code installed, an open-licence font: [GitHub repo](https://github.com/tonsky/FiraCode) / [Google Fonts](https://fonts.google.com/specimen/Fira+Code).
