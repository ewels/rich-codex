import logging
from datetime import datetime
from os import getenv
from sys import exit

from jsonschema.exceptions import ValidationError
from rich.console import Console
from rich.logging import RichHandler

from rich_codex import codex_search, rich_img, utils

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
    "--timeout",
    type=int,
    default=5,
    envvar="TIMEOUT",
    show_envvar=True,
    show_default=True,
    help="Maximum run time for command (seconds)",
)
@click.option(
    "--before-command",
    envvar="BEFORE_COMMAND",
    show_envvar=True,
    help="Setup commands to run before running main output command",
)
@click.option(
    "--after-command",
    envvar="AFTER_COMMAND",
    show_envvar=True,
    help="Setup commands to run after running main output command",
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
    "--fake-command",
    envvar="FAKE_COMMAND",
    show_envvar=True,
    help="Pretend command to show in the screenshot prompt",
)
@click.option(
    "--hide-command",
    is_flag=True,
    envvar="HIDE_COMMAND",
    show_envvar=True,
    help="Hide the terminal prompt with the command at the top of the output",
)
@click.option(
    "--title-command",
    is_flag=True,
    envvar="TITLE_COMMAND",
    show_envvar=True,
    help="Use the command as the terminal title if not set explicitly",
)
@click.option(
    "--head",
    type=int,
    envvar="RC_HEAD",
    show_envvar=True,
    help="Show only the first N lines of output",
)
@click.option(
    "--tail",
    type=int,
    envvar="RC_TAIL",
    show_envvar=True,
    help="Show only the last N lines of output",
)
@click.option(
    "--trim-after",
    envvar="TRIM_AFTER",
    show_envvar=True,
    help="Don't print any more lines after this string is found",
)
@click.option(
    "--truncated-text",
    default="[..truncated..]",
    envvar="TRUNCATED_TEXT",
    show_envvar=True,
    help="Text to show when --head or --tail truncate content",
)
@click.option(
    "--skip-git-checks",
    is_flag=True,
    envvar="SKIP_GIT_CHECKS",
    show_envvar=True,
    help="Skip safety checks for git repos",
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
    "--terminal-min-width",
    type=int,
    default=80,
    envvar="TERMINAL_MIN_WIDTH",
    show_envvar=True,
    show_default=True,
    help="Minimum width of the terminal when trimming",
)
@click.option(
    "--notrim",
    is_flag=True,
    envvar="NOTRIM",
    show_envvar=True,
    help="Disable automatic trimming of terminal width",
)
@click.option(
    "--terminal-theme",
    envvar="TERMINAL_THEME",
    show_envvar=True,
    help="Colour theme",
)
@click.option(
    "--snippet-theme",
    envvar="SNIPPET_THEME",
    show_envvar=True,
    help="Snippet Pygments theme",
)
@click.option(
    "--use-pty",
    is_flag=True,
    envvar="USE_PTY",
    show_envvar=True,
    help="Use a pseudo-terminal for commands (may capture coloured output)",
)
@click.option(
    "--created-files",
    envvar="CREATED_FILES",
    show_envvar=True,
    help="Save a list of created files to this file",
    metavar="<filename>",
)
@click.option(
    "--deleted-files",
    envvar="DELETED_FILES",
    show_envvar=True,
    help="Save a list of deleted files to this file",
    metavar="<filename>",
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
    timeout,
    before_command,
    after_command,
    snippet,
    snippet_syntax,
    img_paths,
    clean_img_paths,
    configs,
    fake_command,
    hide_command,
    title_command,
    head,
    tail,
    trim_after,
    truncated_text,
    skip_git_checks,
    no_confirm,
    min_pct_diff,
    skip_change_regex,
    terminal_width,
    terminal_min_width,
    notrim,
    terminal_theme,
    snippet_theme,
    use_pty,
    created_files,
    deleted_files,
    verbose,
    save_log,
    log_file,
):
    """Create rich code images for your docs."""
    # Sensible defaults
    no_confirm = True if not no_confirm and getenv("GITHUB_ACTIONS") else no_confirm
    force_terminal = True if getenv("GITHUB_ACTIONS") or getenv("FORCE_COLOR") or getenv("PY_COLORS") else None
    terminal_width = int(terminal_width) if type(terminal_width) is str else terminal_width
    terminal_min_width = int(terminal_min_width) if type(terminal_min_width) is str else terminal_min_width
    saved_image_paths = []
    num_skipped_images = 0
    num_saved_images = 0
    img_obj = None
    codex_obj = None

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
            show_path=False,
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

    # Check git status
    git_status, git_status_msg = utils.check_git_status()
    if skip_git_checks or git_status:
        log.debug(f"Git status check: {git_status_msg} (skip_git_checks: {skip_git_checks})")
    elif not git_status:
        log.error(f"[bright_red]Error with git:[/] [red]{git_status_msg}")
        log.info("Please resolve and run again, or use '--skip-git-checks'")
        exit(1)

    if no_confirm:
        log.debug("Skipping confirmation of commands")
    if force_terminal:
        log.debug("Forcing terminal logging output")
    if terminal_width:
        log.info(f"Setting terminal width to {terminal_width}")
    if terminal_min_width and not notrim:
        log.info(f"Trimming terminal output down to a minimum of {terminal_min_width}")
    if terminal_width and terminal_min_width:
        if terminal_min_width > terminal_width:
            log.error(
                "terminal_min_width ({}) > terminal_width ({})! Disabling terminal_min_width".format(
                    terminal_min_width, terminal_width
                )
            )
            terminal_min_width = None

    # Console for printing to stdout
    console = Console(
        force_terminal=force_terminal,
        highlight=False,
        width=100 if getenv("GITHUB_ACTIONS") else None,
    )

    # Check for mutually exclusive options
    if command and snippet:
        raise click.BadOptionUsage("--command", "Please use either --command OR --snippet but not both")
    if (command or snippet) and not img_paths:
        raise click.BadOptionUsage("--img-paths", "--img-paths is required when using --command or --snippet")

    # Generate image from a supplied command / snippet
    if command or snippet:
        img_obj = rich_img.RichImg(
            snippet_syntax=snippet_syntax,
            timeout=timeout,
            before_command=before_command,
            after_command=after_command,
            fake_command=fake_command,
            hide_command=hide_command,
            title_command=title_command,
            head=head,
            tail=tail,
            trim_after=trim_after,
            truncated_text=truncated_text,
            min_pct_diff=min_pct_diff,
            skip_change_regex=skip_change_regex,
            terminal_width=terminal_width,
            terminal_min_width=terminal_min_width,
            notrim=notrim,
            terminal_theme=terminal_theme,
            snippet_theme=snippet_theme,
            use_pty=use_pty,
            console=console,
        )
        img_obj.no_confirm = no_confirm
        if command:
            log.info(f"Command: [white on black] {command} [/]")
            img_obj.command = command
        if snippet:
            log_snippet = snippet[0:30].replace("\n", " ")
            log.info(f"Snippet: [white on black] {log_snippet}... [/]")
            img_obj.snippet = snippet
        img_obj.img_paths = img_paths.splitlines() if img_paths else []
        if img_obj.confirm_command():
            img_obj.get_output()
            img_obj.save_images()
            saved_image_paths += img_obj.saved_img_paths
            num_saved_images += img_obj.num_img_saved
            num_skipped_images += img_obj.num_img_skipped

    # Generate images from config files

    # Search files for codex strings
    codex_obj = codex_search.CodexSearch(
        search_include=search_include,
        search_exclude=search_exclude,
        configs=configs,
        no_confirm=no_confirm,
        snippet_syntax=snippet_syntax,
        timeout=timeout,
        before_command=before_command,
        after_command=after_command,
        hide_command=hide_command,
        title_command=title_command,
        head=head,
        tail=tail,
        trim_after=trim_after,
        truncated_text=truncated_text,
        min_pct_diff=min_pct_diff,
        skip_change_regex=skip_change_regex,
        terminal_width=terminal_width,
        terminal_min_width=terminal_min_width,
        notrim=notrim,
        terminal_theme=terminal_theme,
        snippet_theme=snippet_theme,
        use_pty=use_pty,
        console=console,
    )
    try:
        codex_obj.parse_configs()
    except ValidationError as e:
        log.critical(e)
        exit(1)
    if no_search:
        log.info("Skipping file search")
    else:
        num_errors = codex_obj.search_files()
        if num_errors > 0:
            log.error("Found errors whilst running")
            exit(1)
    codex_obj.collapse_duplicates()
    codex_obj.confirm_commands()
    codex_obj.save_all_images()
    saved_image_paths += codex_obj.saved_img_paths
    num_saved_images += codex_obj.num_img_saved
    num_skipped_images += codex_obj.num_img_skipped

    # Clean unrecognised images
    if clean_img_paths:
        cleaned_paths = utils.clean_images(clean_img_paths, img_obj, codex_obj)

    # Write saved file paths to disk
    if created_files and len(saved_image_paths):
        log.info(f"Saving list of new file paths to: [magenta]{created_files}[/]")
        with open(created_files, "w") as f:
            f.write("\n".join(saved_image_paths))

    # Write cleaned file paths to disk
    if deleted_files and len(cleaned_paths):
        log.info(f"Saving list of deleted file paths to: [magenta]{deleted_files}[/]")
        with open(deleted_files, "w") as f:
            f.write("\n".join([str(path) for path in cleaned_paths]))

    if num_skipped_images > 0:
        log.info(f"[dim]Skipped {num_skipped_images} images 🤫")
    if num_saved_images > 0:
        log.info(f"Saved {num_saved_images} images ✨")
    if len(cleaned_paths) > 0:
        log.info(f"Deleted {len(cleaned_paths)} images 💥")
    if num_skipped_images == 0 and num_saved_images == 0:
        log.warning("Couldn't find anything to do 🙄")


if __name__ == "__main__":
    main()
