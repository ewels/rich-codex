## Command-line / action inputs

You can generate images by providing a command or snippet directly to the CLI at run time.

You need the following command line flags / environment variables / GitHub Action inputs:

One of:

- `--command` / `$COMMAND` / `command`
- `--snippet` / `$SNIPPET` / `snippet`

_And:_

- `--img-paths` / `$IMG_PATHS` / `img_paths`

For example:

```bash
rich-codex --command 'my-command --yay' --img-paths 'docs/example.svg'
```
