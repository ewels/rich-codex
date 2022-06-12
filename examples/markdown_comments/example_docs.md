# My amazing documentation

This markdown file contains some HTML comments which do not render.
However, they instruct `rich-screenshot-action` to save images.
The markdown then includes image tags for the expected image filenames.

Markdown images that include a `inline code command` as the only alt-text will be discovered and rendered.
The terminal capture is handled by the Rich library:

![`rich-codex --help`](img/rich-codex-help.svg)

Add a Markdown [image title string](https://daringfireball.net/projects/markdown/syntax#img) after the filename to customise the terminal window title:

![`rich-codex --help`](img/rich-codex-help-custom-title.svg "Make mine a non-fat frappuccino with extra whipped cream and chocolate sauce")

You can use HTML comments to customise additional aspects of the generated image.
If you want rich-click to ignore an image, use a comment with `SKIP=true`

<!-- RICH-CODEX TERMINAL_THEME=MONOKAI -->
![`rich-codex --help`](img/rich-codex-help-narrow.svg)

As well as commands, the action can take code snippets, which are auto-formatted by rich-cli:

<!-- rich-codex code img/example-json.svg
---
{"menu": {
  "id": "file", "value": "File",
  "popup": {
    "menuitem": [
      {"value": "New", "onclick": "CreateNewDoc()"},
      {"value": "Open", "onclick": "OpenDoc()"},
      {"value": "Close", "onclick": "CloseDoc()"}
    ]
  }
}}
-->
![json-snippet](img/example-json.svg)
