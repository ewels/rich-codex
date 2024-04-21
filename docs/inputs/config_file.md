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

### Install IDE Validation

You can validate your `.rich-codex.yml` files in your IDEs using JSONSchema.

#### VSCode

1. Install the [VSCode-YAML extension](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)

2. In your repo, create a `.vscode/settings.jsonc` or `.vscode/settings.template.jsonc` file containing the following data. This is what tells the extension which schema to associate with each file.

```json
{
  "yaml.schemas": {
    "https://raw.githubusercontent.com/ewels/rich-codex/main/src/rich_codex/config-schema.yml": [
      ".rich-codex.yml",
      ".rich-codex.yaml"
    ]
  }
}
```

3. To prompt other users to install the YAML extension, create a `.vscode/extensions.json` file containing the following data inside your repo:

```json
{
  "recommendations": ["redhat.vscode-yaml"]
}
```

#### JetBrains (PyCharm, IntelliJ, etc.)

There are two ways to set this up.

You can either add the following data to your `.idea/jsonSchemas.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="JsonSchemaMappingsProjectConfiguration">
    <state>
      <map>
        <entry key="rich_codex">
          <value>
            <SchemaInfo>
              <option name="generatedName" value="New Schema" />
              <option name="name" value="rich-codex" />
              <option name="relativePathToSchema" value="https://raw.githubusercontent.com/ewels/rich-codex/main/src/rich_codex/config-schema.yml" />
              <option name="patterns">
                <list>
                  <Item>
                    <option name="path" value=".rich-codex.yml" />
                  </Item>
                  <Item>
                    <option name="path" value=".rich-codex.yaml" />
                  </Item>
                </list>
              </option>
            </SchemaInfo>
          </value>
        </entry>
      </map>
    </state>
  </component>
</project>
```

Or you can do this manually in **Preferences > Languages & Frameworks > Schemas and DTDs > Json Schema Mappings**:

- **Name**: `rich-codex`
- **Schema File or URL**: `https://raw.githubusercontent.com/dbt-labs/dbt-jsonschema/main/schemas/dbt_project.json`
- **Schema Version:** JSON schema version 4
- **Mappings**:
  - `.rich-codex.yml`
  - `.rich-codex.yaml`
