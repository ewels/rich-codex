# My amazing documentation

This markdown file contains some HTML comments which do not render.
However, they instruct `rich-screenshot-action` to save images.
The markdown then includes image tags for the expected image filenames.

Markdown images that include a `inline code command` as the only alt-text will be discovered and rendered.
The terminal capture is handled by the Rich library:
![`rich-codex --help`](img/rich-codex-help.svg)

You can also use HTML comments, leaving you free to craft markdown image tags however you like.
The action uses [CairoSVG](https://cairosvg.org/) to generate PNG and PDF files:

<!-- rich-codex cmd img/cairo-help.png "cairosvg --help" -->
![A screenshot of the Cairo help text](img/cairo-help.png)

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
