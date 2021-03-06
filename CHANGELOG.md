# Changelog: rich-codex

## Version 1.2.0.dev0

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
