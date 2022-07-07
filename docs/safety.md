<!-- prettier-ignore-start -->
!!! danger "💥⚠️ **Warning** ⚠️💥"
    Reminder: rich-codex runs arbitrary commands found in documentation on your host system. You are responsible for ensuring that it does not do any damage.
<!-- prettier-ignore-end -->

## Prompts for commands

When rich-codex runs interactively, it collects all commands to be run and presents these to you, the user. You then need to choose whether to run all commands, choose some or to ignore all of them.

You can disable these checks by using the `--no-confirm` CLI flag / setting env var `$NO_CONFIRM`.

## Banned commands

As a very basic safety step, rich-codex attempts to ignore any commands that start with the following: `rm`, `cp`, `mv`, `sudo`. This is to avoid accidentally messing with your local system.

Please note that this is only for rough protection against accidents and would be easy for a malicious user to circumvent _(for example, putting these commands in a bash script and running that)_.

## Git checks

By default, rich-codex checks that:

- You are running within a initialised git repository
- You do not have any uncommitted changes

This is because rich-codex overwrites local files. If you're running within a clean git repo you can easily see what has been changed and revert it.

You can disable these checks by using the `--skip-git-checks` CLI flag / setting env var `$SKIP_GIT_CHECKS`.
