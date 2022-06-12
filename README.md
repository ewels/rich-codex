# rich-codex ⚡️📖⚡️

### A [GitHub Action](#github-action) and [command-line tool](#command-line) to generate screengrab images of a terminal window containing _command outputs_ or _code snippets_.

[![PyPI Version](https://img.shields.io/pypi/v/rich-codex.svg?style=flat-square)](https://pypi.python.org/pypi/multiqc/)
[![Docker](https://img.shields.io/docker/automated/ewels/rich-codex.svg?style=flat-square)](https://hub.docker.com/r/ewels/multiqc/)

## How it works

rich-codex is a command-line tool that you can via a **GitHub action** or as a **command line tool**. It works with any markdown, including GitHub READMEs.

It collects either commands or code snippets, together with output filenames and configuration options. Commands are run in a subprocess and the standard output & standard error collected. These are then rendered as an image using [Textualize/rich](https://github.com/textualize/rich). For example:

![`rich-codex --help`](docs/img/rich-codex-help.svg)

Rich-codex creates the images that your markdown docs expect. It doesn't require a HTML build-step and doesn't make any changes to your markdown or its output. As such, it's compatible with _**any documentation engine**_, including rendering markdown on [github.com](https://github.com).

Typical use cases include:

- 📷 Example outputs that _automatically stay in sync with your package_
- ✨ Awesome looking code examples that match your docs

Rich-codex needs **Inputs** (commands / snippets) and **output filenames** to work. These can be configured in four different ways:

- 🖼 [Markdown images](#markdown-images)
  - Search markdown files for image tags with command alt text. eg: `` ![`rich-codex --help`](docs/img/rich-codex-help.svg) ``
- 💬 [Markdown comments](#markdown-comments)
  - Search markdown files for special HTML comments.
- ➡️ [Command-line / action inputs](#command-line-action-inputs)
  - Specify a command or snippet using the action `with` inputs.
- ⚙️ [Config files](#yaml-config-files)
  - Use one or more YAML config files for multiple images and more complex customisation.

Images can be generated as SVG, PNG or PDF (detected by filename extension).

## GitHub Action

Rich-codex was primarily designed to run automatically with GitHub actions, to keep your screenshots up to date for you.
Once the action generates images, it's up to you to use them however you like in the rest of your workflow.

A very simple example is shown below. This action looks for rich-codex content in the repo, generates the images and then creates and pushes a new commit with any changes.

```yaml
on: [push]
jobs:
  rich_codex:
    runs-on: ubuntu-latest
    steps:
      - name: Check out the repo
        uses: actions/checkout@v3

      - name: Install your custom tools
        run: pip install .

      - name: Generate terminal images with rich-codex
        uses: ewels/rich-codex@v1
        with:
          commit_changes: "true"
```

For a more complex example, see [`.github/workflows/examples.yml`](.github/workflows/examples.yml) in this repository.

> **NB:** For GitHub Actions to push commits to your repository, you'll need to set _Workflow permissions_ to _Read and write permissions_ under _Actions_ -> _General_ in the repo settings. See the [GitHub docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#configuring-the-default-github_token-permissions).

## Command-line

In addition to the GitHub Action, rich-codex is also a stand-alone command line tool.

You are welcome to use it locally, for example when first writing new documentation and generating initial images to check their output.

> ⚠️ **Warning** ⚠️
> Please remember that rich-codex is designed to _run_ arbitrary commands that it finds within documentation for your project.
> As such, it should be considered a fairly risky piece of software. You alone are responsible for any damage you cause to your computer! 🙃
> Running rich-codex entirely within GitHub Actions is recommended, as any damage it can cause as it doesn't really matter if it wipes the hard disk there.

### Docker image

There is a docker image for running rich-codex, however - note that if you're trying to run commands, they will likely not be available in the container! So this is best used for code snippets or common linux tools. Alternatively, you can build your own docker image using this as a base, with additional dependencies installed.

To run, a typical command would be:

```bash
docker run -i -v `pwd`:`pwd` -w `pwd` -u $(id -u):$(id -g) ewels/richcodex
```

- The `-i` flag enables stdin so that you can confirm running commands (alternatively, use `--no-confirm` at the end)
- The `-v` argument tells Docker to bind your current working directory (`pwd`) to the same path inside the container, so that files created there will be saved to your local file system outside of the container.
- `-w` sets the working directory in the container to this path, so that it's the same as your working directory outside of the container.
- `-u` sets your local user account as the user inside the container, so that any files created have the correct ownership permissions.

You can then pass environment variables with the `-e` flag to customise behaviour. See the usage instructions below for the available environment variables.

### Local installation

You can install `rich-codex` from the [Python Package Index (PyPI)](https://pypi.org/project/rich-codex/) with `pip` or equivalent.

```bash
pip install rich-click
```

At its simplest, the command-line tool runs without any arguments and recursively searches the current working directory for anything it recognises:

```bash
rich-codex
```

Behaviour can be customised with command-line flags or by setting environment variables, see `rich-codex --help`.

#### Requirements for PNG / PDF outputs

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

## Generating images

### Markdown images

If you write markdown with images that contain _just_ a `backtick command` as the alt-text, rich-codex will find them.

For example, the following markdown will generate `docs/img/rich-codex-help.svg` (the image shown above) based on the output of the command `rich-codex --help`:

```markdown
This is getting meta!
![`rich-codex --help`](docs/img/rich-codex-help.svg)
```

> Note that this particular output is generated by the [rich-click](https://github.com/ewels/rich-click) package.
> This supports environment variables for setting terminal width, so I set `TERMINAL_WIDTH=120`

You can also add title text in quotes after the filename, which will be used in the top menu bar of the screenshot terminal.

Finally, you can use a HTML comment in a line above the image to set config attributes for this image only.
The comment should begin with `RICH-CODEX` and then have `KEY=VALUE` pairs. Available configs are:

- `SKIP`: Skip this image
- `MIN_PCT_DIFF`: Minimum file percentage change required to update image
- `SKIP_CHANGE_REGEX`: Skip image update if file changes match regex
- `TERMINAL_WIDTH`: Set terminal width
- `TERMINAL_THEME`: Set terminal theme
- `USE_PTY`: Use a pseudo-terminal for commands (may capture coloured output)

For example:

<!-- prettier-ignore-start -->

```markdown
<!-- RICH-CODEX TERMINAL_WIDTH=60 -->
![`cowsay "Taste the rainbow" | lolcat -S 100`](docs/img/taste-the-rainbow.svg "Taste the rainbow")
```

<!-- RICH-CODEX TERMINAL_WIDTH=60 -->
![`cowsay "Taste the rainbow" | lolcat -S 100`](docs/img/taste-the-rainbow.svg "Taste the rainbow")

<!-- prettier-ignore-end -->

### Markdown comments

_coming soon_

### Command-line / action inputs

You can generate images by providing a command or snippet as a direct input to the tool.

You need the following command line flags / environment variables / GitHub Action inputs

- One of:
  - `--command` / `$COMMAND` / `command`
  - `--snippet` / `$SNIPPET` / `snippet`
- And:
  - `--img_paths` / `$IMG_PATHS` / `img_paths`

### YAML config files

_coming soon_

## Reference docs

### GitHub Action Inputs

#### `include`

Files to search for rich-codex comments.

#### `exclude`

Files to exclude from search for rich-codex comments.

#### `command`

Command to run.

#### `snippet`

Literal code snippet to render.

#### `img_paths`

Path to image filenames if using 'command' or 'snippet'.

#### `configs`

Paths to YAML config files.

#### `width`

Width of the terminal.

#### `theme`

Colour theme.

### GitHub Action Outputs

#### `images`

JSON array of all generated images.

#### `svgs`

JSON array of all generated SVG files.

#### `pngs`

JSON array of all generated PNG files.

#### `pdfs`

JSON array of all generated PDF files.

## Troubleshooting

### Output has no colour

By default, rich-codex runs commands in a Python `subprocess`. This is not an interactive termainal, and as such many command-line tools will disable coloured output.

This is best solved at the tool level if possible, by telling the tool to force coloured output. However, if this is not possible then you can use the `--use-pty` flag / `USE_PTY` env var. This uses a [Python `pty` pseudo-terminal](https://docs.python.org/dev/library/pty.html) instead of [`subprocess`](https://docs.python.org/dev/library/subprocess.html) which may trick your tool into keeping coloured output.

Please note that commands with pipes cannot be used in this mode currently - the pipes will be treated as literal strings (and probably other special bash characters too). If anyone knows how to resolve this, please let me know!
