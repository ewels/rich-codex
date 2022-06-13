# rich-codex ⚡️📖⚡️

A GitHub Action / command-line tool which generates screengrab images of a terminal window, containing _command outputs_ or _code snippets_.

[![PyPI Version](https://img.shields.io/pypi/v/rich-codex.svg?style=flat-square)](https://pypi.python.org/pypi/multiqc/)
[![Docker](https://img.shields.io/docker/automated/ewels/rich-codex.svg?style=flat-square)](https://hub.docker.com/r/ewels/multiqc/)

## Introduction

Rich-click searches markdown code for image embeds with commands or code snippets. It runs these commands and saves a terminal screen-grab at the embedded path.

Typical use cases:

- 📷 Example CLI tool outputs that _automatically stay in sync with your package_
- ♻️ Syntax-highlighted code snippets that are always up to date with your `examples/`
- 🤩 Fast and simple images for your docs with minimal setup

## Quickstart

1. 📖 Write some markdown docs, use an image tag with a backtick command inside:
   ```markdown
   ![`cat cat.txt | lolcat -S 1`](img/cat.svg)
   ```
2. 🤖 Add a GitHub Action to automatically run the command, generate the image and commit to the repo:

   ```yaml
   on: [push]
   jobs:
     rich_codex:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3

         - name: Install your custom tools
           run: pip install lolcat

         - name: Generate terminal images with rich-codex
           uses: ewels/rich-codex@v1
           with:
             commit_changes: "true"
   ```

3. 🌈 Enjoy reading your documentation ![My cat rainbow](img/cat.svg)

## How it works

Rich-codex is a command-line tool that you can via a **GitHub action** or as a **command line tool**. It works with any markdown (including GitHub READMEs).

It collects either commands or code snippets, together with output filenames and configuration options. Commands are run in a subprocess and the standard output & standard error collected. These are then rendered as an image using [Textualize/rich](https://github.com/textualize/rich).

> Rich-codex creates the images that your markdown docs expect. It doesn't require a HTML build-step and doesn't make any changes to your markdown or its output. As such, it's compatible with _**any documentation engine**_, including rendering markdown on [github.com](https://github.com).

Rich-codex needs **inputs** (commands / snippets) and **output filenames** to work. These can be configured in four different ways:

- 🖼 [Markdown images](#markdown)
  - Search markdown files for image tags with command alt text. eg: `` ![`rich-codex --help`](img/rich-codex-help.svg) ``
- 💬 [Markdown comments](#markdown)
  - Search markdown files for special HTML comments.
- ➡️ [Command-line / action inputs](#command-line--action-inputs)
  - Specify a command or snippet using the action `with` inputs.
- ⚙️ [Config files](#yaml-config-files)
  - Use one or more YAML config files for multiple images and more complex customisation.

Images can be generated as SVG, PNG or PDF (detected by filename extension).
