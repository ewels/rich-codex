"""Tests for rich_codex.cli, driven through Click's CliRunner."""

import logging
import re

import pytest
from click.testing import CliRunner
from conftest import svg_text, write

from rich_codex import __version__
from rich_codex.cli import main


@pytest.fixture(autouse=True)
def reset_root_logger():
    """cli.main() adds handlers to the root logger, so clean up between tests."""
    log = logging.getLogger()
    original_handlers = list(log.handlers)
    original_level = log.level
    yield
    for handler in log.handlers:
        if handler not in original_handlers:
            handler.close()
    log.handlers = original_handlers
    log.setLevel(original_level)


@pytest.fixture(autouse=True)
def no_github_actions_env(monkeypatch):
    """Don't let the ambient CI environment change the defaults under test."""
    for var in ("GITHUB_ACTIONS", "FORCE_COLOR", "PY_COLORS"):
        monkeypatch.delenv(var, raising=False)
    # Every option is settable by envvar, so make sure none leak in from the outside
    for param in main.params:
        if param.envvar:
            monkeypatch.delenv(param.envvar, raising=False)


@pytest.fixture
def runner():
    """Make a Click CLI runner for driving rich-codex."""
    return CliRunner()


def invoke(runner, args, **kwargs):
    """Run the CLI, always skipping the git checks unless the test asks otherwise."""
    if "--skip-git-checks" not in args:
        args = ["--skip-git-checks", *args]
    return runner.invoke(main, args, catch_exceptions=False, **kwargs)


def plain(result):
    """CLI output as flat text.

    Rich styles parts of a message and wraps it inside a panel, so a phrase like
    'either --command OR --snippet' can arrive with colour codes in the middle of it
    and a box border partway through. Whether that happens depends on whether the
    terminal supports colour and how wide it is, which differs between a developer's
    machine and CI, so assertions are made against the text alone.
    """
    text = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
    text = re.sub(r"[│╭╮╰╯─]", " ", text)
    return re.sub(r"\s+", " ", text)


class TestHelp:
    """Tests for the --help output."""

    def test_help_exits_cleanly(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0

    def test_help_lists_key_options(self, runner):
        result = runner.invoke(main, ["--help"])
        for option in ("--command", "--snippet", "--img-paths", "--search-include", "--no-confirm"):
            assert option in plain(result)


class TestOptionValidation:
    """Tests for mutually exclusive and required option combinations."""

    def test_command_and_snippet_are_exclusive(self, runner, tmp_cwd):
        result = invoke(runner, ["--command", "echo hi", "--snippet", "hi", "--img-paths", "a.svg"])
        assert result.exit_code != 0
        assert "either --command OR --snippet" in plain(result)

    def test_command_requires_img_paths(self, runner, tmp_cwd):
        result = invoke(runner, ["--command", "echo hi"])
        assert result.exit_code != 0
        assert "--img-paths is required" in plain(result)

    def test_snippet_requires_img_paths(self, runner, tmp_cwd):
        result = invoke(runner, ["--snippet", "hello"])
        assert result.exit_code != 0
        assert "--img-paths is required" in plain(result)

    def test_bad_extra_env(self, runner, tmp_cwd):
        result = invoke(runner, ["--extra-env", "NOT_A_PAIR", "--no-search"])
        assert result.exit_code != 0
        assert "Could not parse as 'KEY=value'" in plain(result)


class TestGitChecks:
    """Tests for the git safety checks."""

    def test_dirty_repo_exits(self, runner, tmp_cwd, monkeypatch):
        monkeypatch.setattr("rich_codex.utils.check_git_status", lambda: (False, "Found uncommitted changes: [x]"))
        result = runner.invoke(main, ["--no-search"], catch_exceptions=False)
        assert result.exit_code == 1

    def test_skip_git_checks_continues(self, runner, tmp_cwd, monkeypatch):
        monkeypatch.setattr("rich_codex.utils.check_git_status", lambda: (False, "Found uncommitted changes: [x]"))
        result = runner.invoke(main, ["--skip-git-checks", "--no-search"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_clean_repo_continues(self, runner, tmp_cwd, monkeypatch):
        monkeypatch.setattr("rich_codex.utils.check_git_status", lambda: (True, "Git repo looks good."))
        result = runner.invoke(main, ["--no-search"], catch_exceptions=False)
        assert result.exit_code == 0


class TestSnippetAndCommand:
    """Tests for generating a single image from the command line."""

    def test_snippet_to_svg(self, runner, tmp_cwd):
        result = invoke(runner, ["--snippet", "hello snippet", "--snippet-syntax", "text", "--img-paths", "out.svg"])
        assert result.exit_code == 0
        assert (tmp_cwd / "out.svg").exists()

    def test_command_to_svg(self, runner, tmp_cwd):
        result = invoke(runner, ["--command", "echo hello", "--img-paths", "out.svg", "--no-confirm"])
        assert result.exit_code == 0
        assert "echo hello" in svg_text(tmp_cwd / "out.svg")

    def test_multiple_img_paths(self, runner, tmp_cwd):
        result = invoke(
            runner, ["--snippet", "hi", "--snippet-syntax", "text", "--img-paths", "one.svg\ntwo.svg", "--no-confirm"]
        )
        assert result.exit_code == 0
        assert (tmp_cwd / "one.svg").exists()
        assert (tmp_cwd / "two.svg").exists()

    def test_declining_the_command_prompt(self, runner, tmp_cwd):
        result = invoke(runner, ["--command", "echo hello", "--img-paths", "out.svg"], input="n\n")
        assert result.exit_code == 0
        assert not (tmp_cwd / "out.svg").exists()

    def test_accepting_the_command_prompt(self, runner, tmp_cwd):
        result = invoke(runner, ["--command", "echo hello", "--img-paths", "out.svg"], input="y\n")
        assert result.exit_code == 0
        assert (tmp_cwd / "out.svg").exists()

    def test_terminal_width_options(self, runner, tmp_cwd):
        result = invoke(
            runner,
            ["--snippet", "hi", "--snippet-syntax", "text", "--img-paths", "out.svg", "--terminal-width", "60"],
        )
        assert result.exit_code == 0
        assert (tmp_cwd / "out.svg").exists()

    def test_min_width_larger_than_width_is_disabled(self, runner, tmp_cwd, caplog):
        result = invoke(
            runner,
            [
                "--snippet",
                "hi",
                "--snippet-syntax",
                "text",
                "--img-paths",
                "out.svg",
                "--terminal-width",
                "40",
                "--terminal-min-width",
                "100",
            ],
        )
        assert result.exit_code == 0
        # Asserted on the log records rather than the output: Rich truncates long console lines
        assert "Disabling terminal_min_width" in caplog.text

    def test_extra_env_reaches_the_command(self, runner, tmp_cwd):
        result = invoke(
            runner,
            [
                "--command",
                "echo $RC_CLI_TEST",
                "--img-paths",
                "out.svg",
                "--extra-env",
                "RC_CLI_TEST=from-cli",
                "--no-confirm",
            ],
        )
        assert result.exit_code == 0
        assert "from-cli" in (tmp_cwd / "out.svg").read_text()


class TestSearch:
    """Tests for the markdown search behaviour."""

    def test_search_finds_images(self, runner, tmp_cwd):
        (tmp_cwd / "README.md").write_text("![`echo found-me`](out.svg)\n")
        result = invoke(runner, ["--no-confirm"])
        assert result.exit_code == 0
        assert (tmp_cwd / "out.svg").exists()

    def test_no_search_skips_it(self, runner, tmp_cwd):
        (tmp_cwd / "README.md").write_text("![`echo found-me`](out.svg)\n")
        result = invoke(runner, ["--no-search", "--no-confirm"])
        assert result.exit_code == 0
        assert not (tmp_cwd / "out.svg").exists()
        assert "Skipping file search" in plain(result)

    def test_search_errors_exit_nonzero(self, runner, tmp_cwd):
        (tmp_cwd / "README.md").write_text("<!-- RICH-CODEX terminal_width: wide -->\n![`echo hi`](out.svg)\n")
        result = invoke(runner, ["--no-confirm"])
        assert result.exit_code == 1
        assert "Found errors whilst running" in plain(result)

    def test_invalid_config_file_exits_nonzero(self, runner, tmp_cwd):
        (tmp_cwd / ".rich-codex.yml").write_text("not_a_real_option: true\n")
        result = invoke(runner, ["--no-search"])
        assert result.exit_code == 1

    def test_config_file_outputs(self, runner, tmp_cwd):
        write(
            tmp_cwd / ".rich-codex.yml",
            """
            outputs:
              - command: echo from-config
                img_paths:
                  - out.svg
            """,
        )
        result = invoke(runner, ["--no-search", "--no-confirm"])
        assert result.exit_code == 0
        assert (tmp_cwd / "out.svg").exists()

    def test_search_include_option(self, runner, tmp_cwd):
        (tmp_cwd / "README.md").write_text("![`echo readme`](readme.svg)\n")
        (tmp_cwd / "OTHER.md").write_text("![`echo other`](other.svg)\n")
        result = invoke(runner, ["--search-include", "README.md", "--no-confirm"])
        assert result.exit_code == 0
        assert (tmp_cwd / "readme.svg").exists()
        assert not (tmp_cwd / "other.svg").exists()

    def test_unchanged_images_are_reported_as_skipped(self, runner, tmp_cwd):
        args = ["--snippet", "hi", "--snippet-syntax", "text", "--img-paths", "out.svg"]
        assert invoke(runner, args).exit_code == 0
        result = invoke(runner, args)
        assert result.exit_code == 0
        assert "Skipped 1 images" in plain(result)

    def test_nothing_to_do_warns(self, runner, tmp_cwd):
        result = invoke(runner, ["--no-search"])
        assert result.exit_code == 0
        assert "Couldn't find anything to do" in plain(result)


class TestFileLists:
    """Tests for --created-files, --deleted-files and --clean-img-paths."""

    def test_created_files_list(self, runner, tmp_cwd):
        result = invoke(
            runner,
            ["--snippet", "hi", "--snippet-syntax", "text", "--img-paths", "out.svg", "--created-files", "created.txt"],
        )
        assert result.exit_code == 0
        assert (tmp_cwd / "created.txt").read_text().strip().endswith("out.svg")

    def test_created_files_not_written_when_nothing_saved(self, runner, tmp_cwd):
        result = invoke(runner, ["--no-search", "--created-files", "created.txt"])
        assert result.exit_code == 0
        assert not (tmp_cwd / "created.txt").exists()

    def test_clean_img_paths_deletes_stale_images(self, runner, tmp_cwd):
        stale = tmp_cwd / "stale.svg"
        stale.write_text("<svg />")
        result = invoke(
            runner,
            [
                "--snippet",
                "hi",
                "--snippet-syntax",
                "text",
                "--img-paths",
                "out.svg",
                "--clean-img-paths",
                "*.svg",
            ],
        )
        assert result.exit_code == 0
        assert not stale.exists()
        assert (tmp_cwd / "out.svg").exists()
        assert "Deleted 1 images" in plain(result)

    def test_deleted_files_list(self, runner, tmp_cwd):
        (tmp_cwd / "stale.svg").write_text("<svg />")
        result = invoke(
            runner,
            [
                "--snippet",
                "hi",
                "--snippet-syntax",
                "text",
                "--img-paths",
                "out.svg",
                "--clean-img-paths",
                "*.svg",
                "--deleted-files",
                "deleted.txt",
            ],
        )
        assert result.exit_code == 0
        assert "stale.svg" in (tmp_cwd / "deleted.txt").read_text()


class TestLogging:
    """Tests for the logging options."""

    def test_version_is_logged(self, runner, tmp_cwd):
        result = invoke(runner, ["--no-search"])
        assert f"version {__version__}" in plain(result)

    def test_verbose_shows_debug_messages(self, runner, tmp_cwd):
        result = invoke(runner, ["--no-search", "--verbose"])
        assert "Skipping file search" in plain(result)
        assert "Git status check" in plain(result)

    def test_quiet_hides_debug_messages(self, runner, tmp_cwd):
        result = invoke(runner, ["--no-search"])
        assert "Git status check" not in plain(result)

    def test_log_file(self, runner, tmp_cwd):
        result = invoke(runner, ["--no-search", "--log-file", "rc.log"])
        assert result.exit_code == 0
        assert "Git status check" in (tmp_cwd / "rc.log").read_text()

    def test_save_log_picks_a_filename(self, runner, tmp_cwd):
        result = invoke(runner, ["--no-search", "--save-log"])
        assert result.exit_code == 0
        assert len(list(tmp_cwd.glob("rich_codex_*.log"))) == 1


class TestGithubActionsDefaults:
    """Tests for the behaviour changes when running inside GitHub Actions."""

    def test_no_confirm_is_implied(self, runner, tmp_cwd, monkeypatch):
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        (tmp_cwd / "README.md").write_text("![`echo in-actions`](out.svg)\n")
        # No input supplied: the run would hang on a prompt if confirmation weren't skipped
        result = invoke(runner, [])
        assert result.exit_code == 0
        assert (tmp_cwd / "out.svg").exists()


class TestEntryPoint:
    """Tests for the module entry points."""

    def test_module_is_runnable(self, tmp_cwd):
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "rich_codex", "--help"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0
        assert "--img-paths" in result.stdout

    def test_main_module_exposes_the_cli(self, monkeypatch):
        """`python -m rich_codex` calls the same entry point as the console script."""
        import runpy

        calls = []
        monkeypatch.setattr("rich_codex.cli.main", lambda *a, **kw: calls.append(True))
        runpy.run_module("rich_codex.__main__", run_name="__main__")
        assert calls == [True]

    def test_version_is_a_string(self):
        assert isinstance(__version__, str)
        assert __version__.count(".") >= 2


def test_cli_module_defines_option_groups():
    """rich-click option groups keep --help readable; every option in them must exist."""
    from rich_codex import cli

    import rich_click as click

    grouped = {opt for group in click.rich_click.OPTION_GROUPS["rich-codex"] for opt in group["options"]}
    declared = {opt for param in cli.main.params for opt in param.opts}
    assert grouped - declared == {"--help"}
