## Running commands

If you write markdown with images that contain _just_ a `backtick command` as the alt-text, rich-codex will find them.

For example, the following markdown will generate `../img/rich-codex-help.svg` (the image shown above) based on the output of the command `rich-codex --help`:

<!-- RICH-CODEX
terminal_width: 120
notrim: true
extra_env:
  TERMINAL_WIDTH: 120
-->

```markdown
![`rich-codex --help`](../img/rich-codex-help.svg)
```

![rich-codex --help](../img/rich-codex-help.svg)

## Printing files

You can use any command-line tool to print files for screenshots.
A good option is [rich-cli](https://github.com/Textualize/rich-cli), which you can use to easily produce screenshots of files with the `rich` command with nice syntax highlighting:

<!-- prettier-ignore-start -->
!!! tip
    You probably want to hide the command with `hide_command` - see below for more about configuration.

```markdown
<!-- RICH-CODEX hide_command: true -->
![`rich ../example.py --tail 20 --force-terminal`](../img/rich-codex-snippet.svg)
```
<!-- RICH-CODEX hide_command: true -->
![`rich ../example.py --tail 20 --force-terminal`](../img/rich-codex-snippet.svg)


!!! tip
    💡 Use the `--force-terminal` flag to keep colours in your screenshots

!!! note
    `rich-codex` used to bundle `rich-cli` as a requirement, but this was dropped in v1.2.7
<!-- prettier-ignore-end -->

## Title text

You can also add markdown image [title text](https://daringfireball.net/projects/markdown/syntax#img) in quotes after the filename, which will be used in the top menu bar of the screenshot terminal. (Alternatively, set the `title` config option in a comment).

This can be useful when adding lots of command markup to get a good screenshot.
You might also want to hide the command prompt.
For example:

<!-- prettier-ignore-start -->
```markdown
You don't always want people to see the exact command you used, after all.
<!-- RICH-CODEX hide_command: true -->
![`rich ../example.py --tail 20 --force-terminal --guides --panel rounded --panel-style magenta --theme monokai`](../img/rich-codex-snippet-title.svg "example.py")
```
<!-- prettier-ignore-end -->

![long rich-cli command](../img/rich-codex-snippet-title.svg "example.py")

## Config comments

You can use a HTML comment in a line above the image to set config attributes for this image only.
The comment should begin with `RICH-CODEX` and then have valid YAML after that.

The parsed configuration will be validated - see an overview of available variables on the [config overview docs](../config/overview.md).

For example:

<!-- prettier-ignore-start -->

```markdown
<!-- RICH-CODEX {terminal_width: 60, terminal_theme: MONOKAI} -->
![`cowsay -t "Taste the rainbow" | lolcat -S 100`](../img/taste-the-rainbow.svg "Taste the rainbow")
```

<!-- RICH-CODEX {terminal_width: 60, terminal_theme: MONOKAI} -->
![`cowsay -t "Taste the rainbow" | lolcat -S 100`](../img/taste-the-rainbow.svg "Taste the rainbow")

<!-- prettier-ignore-end -->

## MDX files

Rich-codex searches both `.md` and `.mdx` files by default (see [`--search-include`](../config/overview.md)).

MDX (v2 and above, used by Docusaurus, Next.js and others) doesn't allow HTML comments, so config comments can also be written as JSX comments (`{/* … */}`):

<!-- prettier-ignore-start -->

```markdown
{/* RICH-CODEX {terminal_width: 60, terminal_theme: MONOKAI} */}
![`cowsay -t "Taste the rainbow" | lolcat -S 100`](../img/taste-the-rainbow.svg "Taste the rainbow")
```

Multi-line config comments work in the same way, closing the block with `*/}`:

```markdown
{/* RICH-CODEX
terminal_width: 120
notrim: true
extra_env:
  TERMINAL_WIDTH: 120
*/}
![`rich-codex --help`](../img/rich-codex-help.svg)
```

!!! note
    The `RICH-CODEX` keyword must be on the same line as the opening `{/*`, just as it must be with `<!--`.

Both comment styles are recognised in every file that is searched, so you can use JSX comments in `.md` files and HTML comments in `.mdx` files if you prefer (though the latter won't compile as MDX).

<!-- prettier-ignore-end -->

## Code block output

Rich-codex can run the command in a code block and save its output as text with colours, for docs sites that show ANSI colours, such as Astro Starlight with [starlight-codeblocks](https://github.com/ewels/starlight-codeblocks).

Put a config comment directly above the code block (it can be empty), and say where the output goes.

### To a file

Set `runnable.outputFile` on the fence line, relative to the markdown file. starlight-codeblocks shows the file as the block's output, in colour ([needs starlight-codeblocks#35](https://github.com/ewels/starlight-codeblocks/pull/35)).

<!-- prettier-ignore-start -->

````markdown
<!-- RICH-CODEX -->
```sh runnable.outputFile="../img/help.ansi"
$ my-tool --help
```
````

<!-- prettier-ignore-end -->

`img_paths` in the config comment works too, and can add `.svg` or `.png` images of the same output.

### Into the code block

Put an `[!output]` line in the block. Rich-codex replaces everything after it, up to the closing fence or an `[!output end]` line, with the output. Colours are written as `\e[33m`, which starlight-codeblocks shows with `runnable.outputLang=ansi`.

<!-- prettier-ignore-start -->

````markdown
<!-- RICH-CODEX -->
```sh runnable.outputLang=ansi
$ my-tool --version
# [!output]
\e[1mmy-tool\e[0m 1.0
```
````

<!-- prettier-ignore-end -->

If the output has a line that would end the block, rich-codex doesn't write it and the run fails. Write that output to a file instead.

### Good to know

- Shell prompts work as in starlight-codeblocks. In a terminal block (`sh`, `console`, ...) with lines that start with `$ ` or `> `, only those lines are run, without the prompt, plus lines that continue them with a trailing `\`. The other lines are output.
- `command` in the config comment runs something other than what the block shows. Other options work as they do for images.
- Text output never has the command line, or hyperlinks.
- Commands get `FORCE_COLOR=1`, and `COLUMNS` and `TERMINAL_WIDTH` from `terminal_width`.
- Code blocks inside another code block, such as the examples on this page, are never run.

## Code snippets

In addition to running commands, you can format code blocks or "snippets".

To do this, make the `<!-- RICH-CODEX` code comment config with the `snippet` key.
Remember that you can use the pipe character `|` in YAML to have multi-line strings, but you need to be careful with indentation to maintain valid YAML. I'd recommend you write the YAML in a code editor with syntax highlighting and then paste it in.

<!-- prettier-ignore-start -->

!!! info
    The alt-text for the markdown image embed doesn't matter for snippets. However, if it has a command in backticks then this will take priority over the snippet.

If the snippet is valid JSON, it will be pretty-printed and coloured. Otherwise text will default to white.

```markdown
<!-- RICH-CODEX
snippet: |
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
![my JSON snippet](../img/example-json-snippet.svg)
```
![my snippet](../img/example-json-snippet.svg)

For other code languages, use `snippet_syntax` to define which language to format in. For example:

```markdown
<!-- RICH-CODEX
snippet_syntax: python
snippet: |
  >>> print("[italic red]Hello[/italic red] World!", locals())
  Hello World!
  {
      '__annotations__': {},
      '__builtins__': <module 'builtins' (built-in)>,
      '__doc__': None,
      '__loader__': <class '_frozen_importlib.BuiltinImporter'>,
      '__name__': '__main__',
      '__package__': None,
      '__spec__': None,
      'print': <function print at 0x1027fd4c0>,
  }
-->
![](../img/example-python-snippet.svg)
```
![](../img/example-python-snippet.svg)

<!-- prettier-ignore-end -->
