## YAML config files

If you prefer, you can configure rich-codex outputs within YAML config files.

### Config file locations

By default, rich-codex looks for files in the following locations (relative to where it runs):

- `.rich-codex.yml`
- `.github/rich-codex.yml`
- `docs/img/rich-codex.yml`

You can pass one or more additional config locations (separated with newlines) using `--configs` / `RC_CONFIGS` / `rc_configs` (command line / environment variable / GitHub action key).

Any files that are not found (including those supplied in addition to the defaults) will be silently ignored.

<!-- prettier-ignore-start -->
!!! note
    Strange things may happen if you have more than one config file, such as global config settings overwriting one another in unpredictable ways.
    So it's probably best not to use more than one.
<!-- prettier-ignore-end -->

### Validation

When found, rich-codex will first parse the YAML and validate using the [bundled schema](https://github.com/ewels/rich-codex/blob/main/src/rich_codex/config-schema.yml).
If any validation errors are found, rich-codex will provide a log and exit with an error.

### Structure

Config files can have both top-level configuration options that apply to all files and also an `outputs` array of different things to create.

Each `outputs` array item must contain an `img_paths` array of output filenames and either a `command` or a `snippet`.
You can optionally add `title` to customise the terminal window title.

For example:

```yaml
outputs:
  - command: "cat docs/cat.txt | lolcat -S 1"
    title: Image from a config
    img_paths:
      - docs/img/cat.png
  - snippet: |
      #!/usr/bin/env python3
      # -*- coding: utf-8 -*-

      from rich_codex.cli import main

      if __name__ == "__main__":
          main()
    img_paths:
      - docs/img/main_header.svg
```

There are many other config keys also available.
See the [configuration docs](../config/overview.md) for more details.
