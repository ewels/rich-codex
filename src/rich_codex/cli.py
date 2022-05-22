import logging

from rich.logging import RichHandler

from rich_codex import codex_search, rich_img

import rich_click as click

logging.basicConfig(level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[RichHandler(markup=True)])

log = logging.getLogger("rich-codex")


@click.command()
@click.argument("search_paths", nargs=-1)
@click.option("--search-include", envvar="SEARCH_INCLUDE", show_envvar=True)
@click.option("--search-exclude", envvar="SEARCH_EXCLUDE", show_envvar=True)
@click.option("--no-search", is_flag=True, envvar="NO_SEARCH", show_envvar=True)
@click.option("--command", envvar="COMMAND", show_envvar=True)
@click.option("--snippet", envvar="SNIPPET", show_envvar=True)
@click.option("--snippet-format", envvar="SNIPPET_FORMAT", show_envvar=True)
@click.option("--img-paths", envvar="IMG_PATHS", show_envvar=True)
@click.option("--configs", envvar="RC_CONFIGS", show_envvar=True)
@click.option("--terminal-width", envvar="TERMINAL_WIDTH", show_envvar=True)
@click.option("--terminal-theme", envvar="TERMINAL_THEME", show_envvar=True)
def main(
    search_paths,
    search_include,
    search_exclude,
    no_search,
    command,
    snippet,
    snippet_format,
    img_paths,
    configs,
    terminal_width,
    terminal_theme,
):
    """Run the click command-line interface."""
    # Check for mutually exclusive options
    if command and snippet:
        raise click.BadOptionUsage("--command", "Please use either --command OR --snippet but not both")
    if (command or snippet) and not img_paths:
        raise click.BadOptionUsage("--img-paths", "--img-paths is required when using --command or --snippet")
    if (command or snippet) and configs:
        raise click.BadOptionUsage("--configs", "Please use either --command / --snippet OR --configs but not both")

    # Generate image from a supplied command / snippet
    if command or snippet:
        img_obj = rich_img.RichImg(terminal_width, terminal_theme)
        if command:
            img_obj.pipe_command(command)
        if snippet:
            img_obj.format_snippet(snippet, snippet_format)
        img_obj.save_images(img_paths)

    # Search files for codex strings
    if not no_search:
        codex_obj = codex_search.CodexSearch(
            search_paths, search_include, search_exclude, terminal_width, terminal_theme
        )
        codex_obj.search_files()


if __name__ == "__main__":
    main()
