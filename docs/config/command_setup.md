## Running commands before and after

For more complex scenarios, you can also use the config options `--before-command` / `$BEFORE_COMMAND` / `before_command` and `--after-command` / `$AFTER_COMMAND` / `after_command`.

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
![`cat before_after_command_example.txt`](docs/images/before_after_command.svg)
```
![](docs/images/before_after_command.svg)

!!! note:
    Commands should be a single string, so remember to chain using `&&` and ideally use YAML multi-line strings that collapse newlines using `>`.

<!-- prettier-ignore-end -->
