There is a docker image for running rich-codex, available [on GitHub](https://github.com/ewels/rich-codex/pkgs/container/rich-codex):

```bash
docker pull ghcr.io/ewels/rich-codex:latest
```

- The label `latest` will pull the most recent release
- The label `main` will pull the development version
- Releases will have their own specific labels.

<!-- prettier-ignore-start -->
!!! warning
    If you're trying to run commands, they will likely not be available in the container!
    So this image is best used for code snippets or common linux tools.
    Alternatively, you can build your own docker image using this as a base, with additional dependencies installed: `FROM ghcr.io/ewels/rich-codex:latest`
<!-- prettier-ignore-end -->

To run, a typical command would be:

```bash
docker run -i -v `pwd`:`pwd` -w `pwd` -u $(id -u):$(id -g) ghcr.io/ewels/rich-codex
```

- The `-i` flag enables stdin so that you can confirm running commands (alternatively, use `--no-confirm` at the end)
- The `-v` argument tells Docker to bind your current working directory (`pwd`) to the same path inside the container, so that files created there will be saved to your local file system outside of the container.
- `-w` sets the working directory in the container to this path, so that it's the same as your working directory outside of the container.
- `-u` sets your local user account as the user inside the container, so that any files created have the correct ownership permissions.

You can then pass environment variables with the `-e` flag to customise behaviour. See the usage instructions below for the available environment variables.
