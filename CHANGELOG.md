# Changelog: rich-codex

## Version 1.3.0 (2026-08-11)

### New features

- ✨ MDX support: `.mdx` files are now searched by default and config comments can be written as JSX comments (`{/* RICH-CODEX ... */}`), as MDX doesn't allow HTML comments
- ✨ `extra_env` can now be set once for all commands, via a config file, `--extra-env` / `$EXTRA_ENV` or the `extra_env` action input ([#57](https://github.com/ewels/rich-codex/issues/57))
- ✨ Show the source line number and output filenames in the table of commands to confirm ([#57](https://github.com/ewels/rich-codex/issues/57))
- ✨ Group the CLI options into panels in `--help` ([#57](https://github.com/ewels/rich-codex/issues/57))
- ✨ New action input `skip_install`, for when you want to install rich-codex yourself (a specific version, a branch, or a local checkout)
- ✨ New `--no-dedupe` / `$NO_DEDUPE` / `no_dedupe` option, to run duplicate commands separately instead of sharing one screenshot ([#33](https://github.com/ewels/rich-codex/issues/33))

### Testing

- ✨ New unit test suite: 254 tests covering all four modules at 100% coverage, run against every supported Python version in CI ([#60](https://github.com/ewels/rich-codex/pull/60))
- ✨ SVGs now get a stable ID derived from the output path, instead of a checksum of their content. Regenerating an image gives a small diff rather than rewriting most of the file ([#60](https://github.com/ewels/rich-codex/pull/60))

### Bug fixes

- 🐛 `outputs` is now optional in config files, which previously crashed with a `KeyError` ([#57](https://github.com/ewels/rich-codex/issues/57))
- 🐛 Fix `--skip-change-regex` / `$SKIP_CHANGE_REGEX`, which could never match anything: the file diff was consumed before being searched. Diffing also used `difflib.Differ`, which is quadratic and took minutes on large files, and the config schema declared the option as a boolean so setting it in a config file failed validation ([#60](https://github.com/ewels/rich-codex/pull/60))
- 🐛 Fix `save_images()` deleting a generated SVG when a PNG or PDF output followed it ([#60](https://github.com/ewels/rich-codex/pull/60))
- 🐛 A config comment that isn't a dictionary is now counted as an error alongside the others, instead of aborting the whole run ([#60](https://github.com/ewels/rich-codex/pull/60))
- 🐛 `clean_img_paths` no longer raises a `ValueError` on a blank line ([#60](https://github.com/ewels/rich-codex/pull/60))
- 🐛 Fix the `python_verison` action input typo, now `python_version` (old name deprecated). It was also being ignored, and is now passed to the Python / uv setup ([#57](https://github.com/ewels/rich-codex/issues/57))
- 🐛 Fix environment variables missing from the `--help` screenshots with rich-click 1.9
- 🐛 Remove some leftover debug logging that printed the contents of file diffs at `INFO` level
- 🐛 Fix a `ValueError` crash when an output image path is outside the working directory
- 🐛 The hint shown when CairoSVG is missing now says `'rich-codex[cairo]'` instead of `'rich-codex'`, as the `[cairo]` part was being swallowed as rich markup
- 🐛 The Docker image now installs the `cairo` extra, so that PNG and PDF output works
- 🐛 Fix two broken links on the docs homepage, found by building the docs with `--strict`
- 🐛 Fix terminal theme screenshots in the docs, which pointed at `setup.cfg` (removed in v1.2.11)
- 🐛 Fix a typo in the `snippet_syntax` description ("sytax"), shown in `--help` and in the action inputs, plus four more in the docs

### Removed

- 💥 The built-in filter that ignored `/CreationDate` changes in PDFs is gone. CairoSVG writes that metadata into a compressed stream, so it never appeared as plaintext for a regex to match. Use `min_pct_diff` for PDF outputs instead ([#60](https://github.com/ewels/rich-codex/pull/60))

### GitHub Action

- 🐛 Fix `use_uv: true`, which could never install rich-codex: `uv pip install` had no virtual environment to install into, and the default `3.x` version is setup-python syntax that uv rejects
- 🐛 `commit_changes: "false"` now means false. Previously any non-empty value was treated as true, so setting it to `"false"` still committed and pushed. The same applied to `error_changes`
- 🐛 The log file artifact name now includes the job name and matrix index, so that using the action more than once in a single workflow run no longer fails with a duplicate artifact name
- 🔒 Action inputs are passed to scripts through the environment instead of being expanded into them, so their contents can't be run as shell code
- ⬆️ Update the actions used internally, and pin them all to commit SHAs: `checkout` v7, `setup-python` v7, `setup-uv` v9, `upload-artifact` v7

### Python support

- 💥 Minimum supported Python version is now 3.10, up from 3.7. Python 3.7, 3.8 and 3.9 are all end-of-life, and 3.8 / 3.9 are no longer available on GitHub's newest runner images
- ⬆️ Require `rich-click>=1.9.0`, which also drops support for Python 3.7
- ✨ Python 3.10 - 3.14 are all tested in CI on every push
- ⬆️ The Docker image is now based on `python:3.14-alpine`, up from `python:3.10-alpine`
- ♻️ Modernise the code for Python 3.10+, with ruff's `UP` rules to keep it that way

### CI

- ✨ As well as the unit tests, CI now checks an installed copy of rich-codex end to end on every supported Python version, so packaging mistakes get caught
- ✨ New `Test action` workflow, covering both of the action's install paths (`pip` and `uv`), neither of which was tested before
- ✨ The Docker image is now built (but not published) on pull requests, so that a broken `Dockerfile` is caught before it's merged
- 🔒 Give every workflow job an explicit `permissions` block and stop persisting git credentials where they aren't needed

### Developer tooling

- ♻️ Git hooks now run with [prek](https://prek.j178.dev) instead of pre-commit, configured in `prek.toml`. It's a single Rust binary with no Python runtime of its own, and the TOML config is harder to get wrong than the YAML equivalent
- ♻️ [Ruff](https://docs.astral.sh/ruff/) replaces black, flake8, isort and pyupgrade, configured in `pyproject.toml`. `.flake8` is gone, along with the `[tool.black]` and `[tool.isort]` sections
- ✨ New hooks: `actionlint` for the workflow files, `pyproject-fmt` for `pyproject.toml`, and `codespell` for the docs
- ✨ All hooks are pinned to a commit SHA, matching the versions used in the sister project [rich-click](https://github.com/ewels/rich-click)

### Type checking

- ✨ Everything in `src/` now has type annotations, checked by [mypy](https://mypy-lang.org/) with `disallow_untyped_defs`, as a prek hook and in CI. The `[tool.mypy]` config was previously unused, so nothing was actually being checked
- 🐛 `--terminal-width` / `$TERMINAL_WIDTH` now reports a usage error for a non-numeric value, instead of exiting with an unhandled `ValueError` traceback. It was the only numeric option that wasn't parsed as an integer
- 🐛 `clean_img_paths` no longer crashes part-way through deleting when a matched file resolves to somewhere outside the working directory (a symlink pointing out of the repo)
- 🐛 `--img-paths` now ignores blank lines, like every other newline-separated option
- 🐛 `save_images()` now warns and returns instead of raising `AttributeError` if it's called before any output has been rendered
- ♻️ Each rendered image no longer leaves a `/dev/null` file handle open for the lifetime of the run, which could exhaust the open-file limit on a repo with many images
- ♻️ `run_command()` always returns `None`; it used to return `False` when a command was refused. Check `.aborted` for that, as it always could
- ♻️ `clean_images()` returns a sorted list of deleted paths, rather than a set on success and an empty list otherwise. Deletions and the `--deleted-files` list are now in a stable order
- ♻️ Pass a lexer name to rich's `Syntax` rather than `None`, and stop passing the validator object to `ValidationError`, which expects a name. Neither changes any output

## Version 1.2.11 (2025-04-22)

- 🐛 Fix validation error ([#55](https://github.com/ewels/rich-codex/pull/55))
- ✨ In Github Action, added uv support (`use_uv`), skip Python setup support (`skip_python_setup`), and specific Python version support (`python_verison`).

## Version 1.2.10 (2025-03-14)

- 🐛 Fix missing required argument ([#53](https://github.com/ewels/rich-codex/pull/53))

## Version 1.2.9 (2025-03-12)

- ✨ Add `working_dir` as new input to the GitHub Action, by @dwreeves in https://github.com/ewels/rich-codex/pull/47
- ♻️ Update all GitHub actions used, by @ewels in https://github.com/ewels/rich-codex/pull/51

## Version 1.2.8 (2025-02-20)

- ✨ Update upload-artifact action to v4 ([#49](https://github.com/ewels/rich-codex/pull/49))

## Version 1.2.7 (2024-01-17)

- 🐛 Remove `rich-cli` as a dependency ([#45](https://github.com/ewels/rich-codex/issues/45))

## Version 1.2.6 (2022-10-03)

- 🐛 Handle `OSError` when creating directories with a log message instead of crashing

## Version 1.2.5 (2022-08-25)

- 🐛 Tweak output whitespace, fix use of `Path.absolute()` ([#39](https://github.com/ewels/rich-codex/pull/39))
- 🐛 Fix parsing of multiple config files ([#37](https://github.com/ewels/rich-codex/issues/37))
- 🐛 Fixed `KeyError` for top-level config options ([#35](https://github.com/ewels/rich-codex/issues/35))

## Version 1.2.4 (2022-08-19)

- ✨ Debug log `before_command` and `after_command` so that you can see return code, stderr, stdout

## Version 1.2.3 (2022-08-18)

- ✨ Maintain order of commands in markdown, add alphabetical sort of the files to search
- 🐛 Fix typo ([#30](https://github.com/ewels/rich-codex/pull/30))
- 🐛 Fix GitPod edit button ([#29](https://github.com/ewels/rich-codex/pull/29))
- 🐛 Set missing `hide_command` option in example ([#31](https://github.com/ewels/rich-codex/pull/31))

## Version 1.2.2 (2022-08-15)

- ✨ Log _which_ files have uncommitted changes in git ([#25](https://github.com/ewels/rich-codex/issues/25))
- 🐛 Close temp files before deleting (bugfix for Windows) ([#27](https://github.com/ewels/rich-codex/issues/27))

## Version 1.2.1 (2022-08-14)

- ✨ Drop minimum Python version to 3.7
- 🐛 Handle logging error with relative paths ([#26](https://github.com/ewels/rich-codex/issues/26))

## Version 1.2.0 (2022-08-01)

- ✨ Log a warning if duplicate image paths are found ([#20](https://github.com/ewels/rich-codex/issues/20))
- 🐛 Fix `UnboundLocalError` if not cleaning an image path ([#24](https://github.com/ewels/rich-codex/issues/24))

## Version 1.1.0 (2022-07-21)

- ✨ Added CLI flags `--created-files` and `--deleted-files` to create a file with affected file paths
- ✨ GitHub Action: only `git add` / `git rm` files that rich-codex itself created or deleted ([#21](https://github.com/ewels/rich-codex/issues/21))

## Version 1.0.2 (2022-07-08)

- 🐛 Don't use cache in action `actions/setup-python` step
- 🐛 Bump minimum Python version to 3.9 (may try to drop this in the future) ([#19](https://github.com/ewels/rich-codex/issues/19))
- 🐳 Build + tag versioned labels of the Docker image on release
- 📖 Improvements to docs

## Version 1.0.1 (2022-07-07)

Patch release to add in a missing `pyyaml` dependency.

## Version 1.0.0 (2022-07-07)

First public release of rich-codex.
