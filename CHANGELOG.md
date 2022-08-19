# Changelog: rich-codex

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
