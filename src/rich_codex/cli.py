import logging
from datetime import datetime
from os import environ, getenv

from rich.console import Console
from rich.logging import RichHandler
from rich.pretty import pretty_repr

from rich_codex import codex_search, rich_img

import rich_click as click

click.rich_click.OPTION_ENVVAR_FIRST = True
click.rich_click.ENVVAR_STRING = "[env: {}]"

log = logging.getLogger()


@click.command()
@click.option(
    "--search-include",
    envvar="SEARCH_INCLUDE",
    show_envvar=True,
    help="Glob patterns to search for rich-codex comments",
)
@click.option(
    "--search-exclude",
    envvar="SEARCH_EXCLUDE",
    show_envvar=True,
    help="Glob patterns to exclude from search for rich-codex comments",
)
@click.option(
    "--no-search",
    is_flag=True,
    envvar="NO_SEARCH",
    show_envvar=True,
    help="Set to disable searching for rich-codex comments",
)
@click.option(
    "--command",
    envvar="COMMAND",
    show_envvar=True,
    help="Specify a command to run to capture output",
)
@click.option(
    "--snippet",
    envvar="SNIPPET",
    show_envvar=True,
    help="Literal code snippet to render",
)
@click.option(
    "--snippet-syntax",
    envvar="SNIPPET_SYNTAX",
    show_envvar=True,
    help="Language to use for snippet sytax highlighting",
)
@click.option(
    "--img-paths",
    envvar="IMG_PATHS",
    show_envvar=True,
    help="Path to image filenames if using 'command' or 'snippet'",
)
@click.option(
    "--clean-img-paths",
    envvar="CLEAN_IMG_PATHS",
    show_envvar=True,
    help="Remove any matching files that are not generated",
)
@click.option(
    "--configs",
    envvar="RC_CONFIGS",
    show_envvar=True,
    help="Paths to YAML config files",
)
@click.option(
    "--no-confirm",
    is_flag=True,
    envvar="NO_CONFIRM",
    show_envvar=True,
    help="Set to skip confirmation prompt before running commands",
)
@click.option(
    "--min-pct-diff",
    envvar="MIN_PCT_DIFF",
    type=float,
    default=0,
    show_envvar=True,
    show_default=True,
    help="Minimum file percentage change required to update image",
)
@click.option(
    "--skip-change-regex",
    envvar="SKIP_CHANGE_REGEX",
    show_envvar=True,
    help="Skip image update if file changes match regex",
)
@click.option(
    "--terminal-width",
    envvar="TERMINAL_WIDTH",
    show_envvar=True,
    help="Width of the terminal",
)
@click.option(
    "--terminal-theme",
    envvar="TERMINAL_THEME",
    show_envvar=True,
    help="Colour theme",
)
@click.option(
    "--use-pty",
    is_flag=True,
    envvar="USE_PTY",
    show_envvar=True,
    help="Use a pseudo-terminal for commands (may capture coloured output)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    envvar="LOG_VERBOSE",
    show_envvar=True,
    help="Print verbose output to the console.",
)
@click.option(
    "--save-log",
    is_flag=True,
    envvar="LOG_SAVE",
    show_envvar=True,
    help="Save a verbose log to a file (automatic filename).",
    metavar="<filename>",
)
@click.option(
    "-l",
    "--log-file",
    envvar="LOG_FILENAME",
    show_envvar=True,
    help="Save a verbose log to a file (specific filename).",
    metavar="<filename>",
)
def main(
    search_include,
    search_exclude,
    no_search,
    command,
    snippet,
    snippet_syntax,
    img_paths,
    clean_img_paths,
    configs,
    no_confirm,
    min_pct_diff,
    skip_change_regex,
    terminal_width,
    terminal_theme,
    use_pty,
    verbose,
    save_log,
    log_file,
):
    """Create rich code images for your docs."""
    # Sensible defaults
    no_confirm = True if not no_confirm and getenv("GITHUB_ACTIONS") else no_confirm
    force_terminal = True if getenv("GITHUB_ACTIONS") or getenv("FORCE_COLOR") or getenv("PY_COLORS") else None
    terminal_width = int(terminal_width) if type(terminal_width) is str else terminal_width
    num_skipped_images = 0
    num_saved_images = 0
    num_img_cleaned = 0

    if no_confirm:
        log.debug("Skipping confirmation of commands")
    if force_terminal:
        log.debug("Forcing terminal logging output")
    if terminal_width:
        log.info(f"Setting terminal width to {terminal_width}")

    # Set up the logger
    log.setLevel(logging.DEBUG)

    # Set up logs to the console
    log.addHandler(
        RichHandler(
            level=logging.DEBUG if verbose else logging.INFO,
            console=Console(
                stderr=True,
                force_terminal=force_terminal,
            ),
            show_time=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_suppress=[click],
        )
    )

    # Set up logs to a file if we asked for one
    if save_log and not log_file:
        timestamp = datetime.now().strftime("%Y.%m.%d--%H.%M.%S.%f")
        log_file = f"rich_codex_{timestamp}.log"

    if log_file:
        log_fh = logging.FileHandler(log_file, encoding="utf-8")
        log_fh.setLevel(logging.DEBUG)
        log_fh.setFormatter(logging.Formatter("[%(asctime)s] %(name)-20s [%(levelname)-7s]  %(message)s"))
        log.addHandler(log_fh)

    # Console for printing to stdout
    console = Console(force_terminal=force_terminal)

    log.debug("Environment variables: " + pretty_repr(environ))

    # Check for mutually exclusive options
    if command and snippet:
        raise click.BadOptionUsage("--command", "Please use either --command OR --snippet but not both")
    if (command or snippet) and not img_paths:
        raise click.BadOptionUsage("--img-paths", "--img-paths is required when using --command or --snippet")
    if (command or snippet) and configs:
        raise click.BadOptionUsage("--configs", "Please use either --command / --snippet OR --configs but not both")

    # Generate image from a supplied command / snippet
    if command or snippet:
        img_obj = rich_img.RichImg(min_pct_diff, skip_change_regex, terminal_width, terminal_theme, use_pty, console)
        img_obj.no_confirm = no_confirm
        if command:
            log.info(f"Command: [white on black] {command} [/]")
            img_obj.cmd = command
        if snippet:
            log_snippet = snippet[0:30].replace("\n", " ")
            log.info(f"Snippet: [white on black] {log_snippet}... [/]")
            img_obj.snippet = snippet
            img_obj.snippet_syntax = snippet_syntax
        img_obj.img_paths = img_paths.splitlines() if img_paths else []
        img_obj.clean_img_paths = clean_img_paths.splitlines() if clean_img_paths else []
        if img_obj.confirm_command():
            img_obj.get_output()
            img_obj.save_images()
            img_obj.clean_images()
            num_saved_images = img_obj.num_img_saved
            num_skipped_images = img_obj.num_img_skipped
            num_img_cleaned = img_obj.num_img_cleaned

    # Search files for codex strings
    if no_search:
        log.info("Skipping file search")
    else:
        codex_obj = codex_search.CodexSearch(
            search_include,
            search_exclude,
            no_confirm,
            min_pct_diff,
            skip_change_regex,
            terminal_width,
            terminal_theme,
            use_pty,
            console,
        )
        codex_obj.search_files()
        codex_obj.collapse_duplicates()
        codex_obj.confirm_commands()
        codex_obj.save_all_images()
        num_saved_images = codex_obj.num_img_saved
        num_skipped_images = codex_obj.num_img_skipped

    if num_skipped_images > 0:
        log.info(f"[dim]Skipped {num_skipped_images} images 🤫")
    if num_saved_images > 0:
        log.info(f"Saved {num_saved_images} images ✨")
    if num_img_cleaned > 0:
        log.info(f"Deleted {num_img_cleaned} images 🗑")
    if num_skipped_images == 0 and num_saved_images == 0:
        log.warning("Couldn't find anything to do 🙄")


if __name__ == "__main__":
    main()
