You may find that your screenshots are changing every time you run rich-codex, even though no relevant changes have occurred within your code. This could be because the screenshots include timestamps or some other live data.

To avoid doubling your commit count with changes that you don't care about, rich-codex has two mechanisms which you can use to ignore changes:

- ⚖️ Percentage change in file contents
- 🔎 Regular expression matches

## Percentage change in file contents

When you run rich-codex, any new images created will generate log messages that look like this:
`Saved: 'docs/img/rich-codex-snippet-title.svg' (4.63% change)`.
This percentage change is calculated using the [python-Levenshtein](https://github.com/ztane/python-Levenshtein) package, comparing the raw bytes of the two files.

By default, any new files with 0.00% change will be ignored. If you find that you have screenshots changing by the same small percentage every time, you can raise this threshold by setting `--min-pct-diff` / `$MIN_PCT_DIFF` / `min_pct_diff` (CLI, env var, action/config).

For example, if a timestamp caused this file to change by 4.34% on every commit, those changes could be ignored as follows:

<!-- prettier-ignore-start -->
```markdown
<!-- RICH-CODEX min_pct_diff: 5 -->
![`rich-codex --help`](../img/rich-codex-help-min-pct.svg)
```
<!-- prettier-ignore-end -->

## Regular expression matches

Percentage changes in files is quick and simple, but a little crude. If you prefer, you may be able to use regular expressions instead with `--skip-change-regex` / `$SKIP_CHANGE_REGEX` / `skip_change_regex` (CLI, env var, action/config).

If there is a > 0% change in files, a diff will be generated. Any diff lines matching the supplied regexes will be removed and if none remain, the changeset will be ignored.

One regex per line, and blank lines are ignored. An empty pattern would match every line, which would freeze the image forever.

The regexes are matched against the lines of the image file, not against your terminal output, so remember that SVG writes spaces as `&#160;`. Matching a single word avoids the problem:

<!-- prettier-ignore-start -->
```markdown
<!-- RICH-CODEX skip_change_regex: 'Generated&#160;at' -->
![`my-tool --version`](../img/my-tool-version.svg)
```
<!-- prettier-ignore-end -->

<!-- prettier-ignore-start -->
!!! note
    This only works for text-based outputs such as SVG. PNG and PDF files are compressed,
    so a one-character change to a timestamp scrambles the whole file and there are no
    readable lines for a regex to match. Use `min_pct_diff` for those instead.
<!-- prettier-ignore-end -->
