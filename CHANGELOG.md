# Changelog: rich-codex

## Version 1.3.0 (2026-08-12)

A lot of tweaks and improvements that have been building up, mostly driven with Claude.
Hopefully the code should be quite a lot more robust now.

Main new feature is the ability to run with `.mdx` files as well as `.md`, using `{/* */}` comments.

### Breaking changes

- 💥 Minimum supported Python is now 3.10, up from 3.7 ([#61](https://github.com/ewels/rich-codex/pull/61))

### New features

- ✨ MDX support: `.mdx` files are searched by default, and config can be written as JSX comments (`{/* RICH-CODEX ... */}`), as MDX doesn't allow HTML comments ([#58](https://github.com/ewels/rich-codex/pull/58))
- ✨ New `--no-dedupe` option, to run duplicate commands ([#33](https://github.com/ewels/rich-codex/issues/33))
- ✨ `extra_env` can now be set once for all commands ([#57](https://github.com/ewels/rich-codex/issues/57))
- ✨ Smaller SVG diffs thanks to a stable ID based on the output path ([#60](https://github.com/ewels/rich-codex/pull/60))
- ✨ CLI table now shows source line numbers and output filenames ([#57](https://github.com/ewels/rich-codex/issues/57))
- ✨ Tidier `--help`, with the options grouped into panels ([#57](https://github.com/ewels/rich-codex/issues/57))
- ✨ New `skip_install` action input, mostly for self-testing rich-codex changes ([#61](https://github.com/ewels/rich-codex/pull/61))

### Updates

- ♻️ Stopped `/CreationDate` changes in PDFs as it never worked. Use `min_pct_diff` for PDF outputs instead ([#60](https://github.com/ewels/rich-codex/pull/60))
- ♻️ New unit test suite ([#60](https://github.com/ewels/rich-codex/pull/60)), type annotations checked with mypy ([#62](https://github.com/ewels/rich-codex/pull/62)), prek and ruff in place of pre-commit, black, flake8 and isort, and CI across Python 3.10 - 3.14 ([#61](https://github.com/ewels/rich-codex/pull/61))

### Bugs fixed

- 🐛 `skip_change_regex` never matched anything, so images updated regardless ([#60](https://github.com/ewels/rich-codex/pull/60))
- 🐛 `outputs` is now optional in config files ([#57](https://github.com/ewels/rich-codex/issues/57))
- 🐛 Writing an SVG alongside a PNG or PDF in one go could delete the SVG ([#60](https://github.com/ewels/rich-codex/pull/60))
- 🐛 The Docker image can now write PNG and PDF files ([#61](https://github.com/ewels/rich-codex/pull/61))
- 🐛 Action: `use_uv: true` could never install rich-codex ([#61](https://github.com/ewels/rich-codex/pull/61))
- 🐛 Action: `commit_changes: "false"` committed and pushed anyway. Same for `error_changes` ([#61](https://github.com/ewels/rich-codex/pull/61))
- 🐛 Action: using rich-codex twice in one workflow run failed, as both uploaded their log with the same artifact name ([#61](https://github.com/ewels/rich-codex/pull/61))
- 🐛 Action: the `python_verison` input was a typo and was being ignored anyway. Use `python_version`; the old name still works but warns ([#57](https://github.com/ewels/rich-codex/issues/57))

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
