import logging

from rich.logging import RichHandler

from rich_codex.rich_img import RichImg

import rich_click as click

logging.basicConfig(level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])

log = logging.getLogger("rich-codex")


@click.command()
@click.option("--search-include", envvar="SEARCH_INCLUDE", show_envvar=True)
@click.option("--search-exclude", envvar="SEARCH_EXCLUDE", show_envvar=True)
@click.option("--command", envvar="COMMAND", show_envvar=True)
@click.option("--snippet", envvar="SNIPPET", show_envvar=True)
@click.option("--img-paths", envvar="IMG_PATHS", show_envvar=True)
@click.option("--configs", envvar="CONFIGS", show_envvar=True)
@click.option("--terminal-width", envvar="TERMINAL_WIDTH", show_envvar=True)
@click.option("--terminal-theme", envvar="TERMINAL_THEME", show_envvar=True)
def main(search_include, search_exclude, command, snippet, img_paths, configs, terminal_width, terminal_theme):
    """Run the click command-line interface."""
    # Check for mutually exclusive options
    if command and snippet:
        raise click.BadOptionUsage("--command", "Please use either --command OR --snippet but not both")
    if (command or snippet) and not img_paths:
        raise click.BadOptionUsage("--img-paths", "--img-paths is required when using --command or --snippet")
    if (command or snippet) and configs:
        raise click.BadOptionUsage("--configs", "Please use either --command / --snippet OR --configs but not both")

    # Initialise the RichImg object
    obj = RichImg(terminal_width, terminal_theme)

    # Generate image from a command
    if command is not None:
        obj.pipe_command(command, img_paths)


if __name__ == "__main__":
    main()
