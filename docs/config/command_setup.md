## Setting extra environment vars

In some cases you may want to set environment variables for a single command only.
In this case, you can use the `extra_env` config option, which adds YAML key:value pairs to the environment for just that command (and the before / after commands, see below).

I use this method to set the terminal width for the rich-click screenshots in this documentation:

<!-- prettier-ignore-start -->
```markdown
<!-- RICH-CODEX
terminal_width: 120
notrim: true
extra_env:
  TERMINAL_WIDTH: 120
-->
![`rich-codex --help`](../img/rich-codex-cli-envs.svg)
```

!!! tip
    It's probably easier to set these at run-level if that's an option, these are really only if you want to customise for a single output.
<!-- prettier-ignore-end -->

## Faking simple commands

Sometimes you may need to have long complicated commands to get the screenshot you need, when the typical command for an end user would be much simpler.

In this case, you can fake the command shown in the terminal prompt using `--fake-command` / `$FAKE_COMMAND` / `fake_command`.

For example:

<!-- prettier-ignore-start -->

```markdown
<!-- RICH-CODEX fake_command: "my_tool --is-simple" -->
![`echo "I won't tell if you don't 🤫" > temp_file.txt && echo "" && cat temp_file.txt && rm temp_file.txt`](../img/fake_command.svg)
```
![](../img/fake_command.svg)

<!-- prettier-ignore-end -->

## Running commands before and after

Chaining complex commands may not always work if the setup / cleanup commands generate output that you don't want to show in the screenshot.

In these more complex scenarios, you can run additional commands before and after the one used for the screenshot. This is done with the following options:

- `--before-command` / `$BEFORE_COMMAND` / `before_command`
- `--after-command` / `$AFTER_COMMAND` / `after_command`.

These run separate `subprocess` calls with the specified commands before and after the target command.
This can be useful for initialising an environment and then cleaning up afterwards.

For example:

<!-- prettier-ignore-start -->

```markdown
<!-- RICH-CODEX
before_command: >
  echo "This is a very simple example" > before_after_command_example.txt
after_command: rm before_after_command_example.txt
-->
![`cat before_after_command_example.txt`](../img/before_after_command.svg)
```
![](../img/before_after_command.svg)

!!! note:
    Commands should be a single string, so remember to chain using `&&` and ideally use YAML multi-line strings that collapse newlines using `>`.

<!-- prettier-ignore-end -->
