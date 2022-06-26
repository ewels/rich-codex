As rich-codex runs commands within a non-interactive subshell, any command that requires input could cause the tool to hang forever.

To avoid this, rich-codex sets a maximum time limit on all commands (default: `5 seconds`). Once a command runs for this time, it is killed and the screenshot is created with whatever output was captured up to that point.

The amount of time that rich-codex waits for can be configured using `--timeout` / `TIMEOUT` / `timeout` (CLI, env/markdown, action/config).
