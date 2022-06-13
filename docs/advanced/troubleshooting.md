## Output has no colour

By default, rich-codex runs commands in a Python `subprocess`. This is not an interactive termainal, and as such many command-line tools will disable coloured output.

This is best solved at the tool level if possible, by telling the tool to force coloured output. However, if this is not possible then you can use the `--use-pty` flag / `USE_PTY` env var. This uses a [Python `pty` pseudo-terminal](https://docs.python.org/dev/library/pty.html) instead of [`subprocess`](https://docs.python.org/dev/library/subprocess.html) which may trick your tool into keeping coloured output.

Please note that commands with pipes cannot be used in this mode currently - the pipes will be treated as literal strings (and probably other special bash characters too). If anyone knows how to resolve this, please let me know!
