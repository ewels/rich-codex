# rich-codex

This GitHub Action generates screengrab images of a terminal window containing code snippets or outputs from commands.

It uses the Python library [rich](https://github.com/textualize/rich) and also the command line tool [rich-cli](https://github.com/textualize/rich-cli/).

It can be configured in three different ways:

- [Markdown comments](#markdown-comments): Searches for special HTML comments in your markdown files
- [Action inputs](#action-inputs): Specify a command or snippet using the action `with` inputs
- [Config files](#yaml-config-files): Use one or more YAML config files for multiple images and more complex customisation

Once the action generates images, it's up to you to use them however you like.
Some examples can be found in the [Complete examples](#complete-examples) section below.

## Markdown comments

```yaml
rich_codex:
  - uses: actions/checkout@v3
  - uses: ewels/rich-codex@v1
```

## Action inputs

## YAML config files

## Complete examples

### Auto-generate and push

This action looks for rich-codex markdown comments, generates the images and then creates and pushes a new commit with the changes.

```yaml
on: [push]
jobs:
  rich_codex:
    - name: Check out the repo
      uses: actions/checkout@v3

    - name: Generate code images
      uses: ewels/rich-codex@v1

    - name: Add and commit new images
      uses: EndBug/add-and-commit@v9
      with:
        message: Generate new screengrabs with rich-codex
        committer_name: GitHub Actions
        committer_email: actions@github.com
```

## Inputs

### `include`

Files to search for rich-codex comments.

### `exclude`

Files to exclude from search for rich-codex comments.

### `cmd`

Command to run.

### `snippet`

Literal code snippet to render.

### `img_paths`

Path to image filenames if using 'cmd' or 'snippet'.

### `configs`

Paths to YAML config files.

### `width`

Width of the terminal.

### `theme`

Colour theme.

## Outputs

### `images`

JSON array of all generated images.

### `svgs`

JSON array of all generated SVG files.

### `pngs`

JSON array of all generated PNG files.

### `pdfs`

JSON array of all generated PDF files.
