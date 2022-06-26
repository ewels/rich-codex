If snippets can be parsed as JSON, they will be automatically reformatted (pretty-printed) and set to use JSON code syntax colouring. Otherwise they will be printed as white text by default.

To use coloured syntax highlighting on your non-JSON code snippets, you need to tell rich-codex what syntax to use with the `--snippet-syntax` / `SNIPPET_SYNTAX` / `snippet_syntax` option (CLI, env/markdown, action/config).

Syntax highlighting is done using [rich](https://rich.readthedocs.io/en/latest/syntax.html) which uses [Pygments](https://pygments.org). Any language [supported by Pygments](https://pygments.org/languages/) should work.
