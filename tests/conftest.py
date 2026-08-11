"""Shared fixtures for the rich-codex test suite."""

import logging
import os
from io import StringIO

import pytest
from rich.console import Console

from rich_codex.codex_search import CodexSearch
from rich_codex.rich_img import RichImg

# Every argument of CodexSearch.__init__ is positional-or-keyword with no default,
# so tests build one through the `codex_search` factory instead of listing them all.
CODEX_SEARCH_DEFAULTS = {
    "search_include": None,
    "search_exclude": None,
    "configs": None,
    "no_confirm": True,
    "no_dedupe": False,
    "extra_env": None,
    "snippet_syntax": None,
    "timeout": 5,
    "working_dir": None,
    "before_command": None,
    "after_command": None,
    "hide_command": None,
    "title_command": None,
    "head": None,
    "tail": None,
    "trim_after": None,
    "truncated_text": None,
    "min_pct_diff": None,
    "skip_change_regex": None,
    "terminal_width": None,
    "terminal_min_width": None,
    "notrim": None,
    "terminal_theme": None,
    "snippet_theme": None,
    "use_pty": None,
    "console": None,
}


@pytest.fixture(autouse=True)
def capture_debug_logs(caplog):
    """Capture everything rich-codex logs, down to DEBUG level."""
    caplog.set_level(logging.DEBUG, logger="rich-codex")


@pytest.fixture
def tmp_cwd(tmp_path, monkeypatch):
    """Run the test inside an empty temporary working directory."""
    tmp_path = tmp_path.resolve()
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def tty_stdin():
    """Put a real pty on file descriptor 0.

    RichImg.run_command() asks fd 0 for its window size when using a pty, but
    pytest replaces stdin with a plain file, which has no window size to give.
    """
    pty = pytest.importorskip("pty", reason="pty is not available on this platform")
    controller, worker = pty.openpty()
    saved_stdin = os.dup(0)
    os.dup2(worker, 0)
    try:
        yield
    finally:
        os.dup2(saved_stdin, 0)
        for fd in (saved_stdin, worker, controller):
            os.close(fd)


@pytest.fixture
def console():
    """Build a Console that records output to a string instead of a terminal."""
    return Console(file=StringIO(), width=200, force_terminal=False, highlight=False)


@pytest.fixture
def codex_search(console):
    """Build CodexSearch objects, with all constructor args defaulted."""

    def _codex_search(**kwargs):
        return CodexSearch(**{**CODEX_SEARCH_DEFAULTS, "console": console, **kwargs})

    return _codex_search


@pytest.fixture
def rich_img(console):
    """Build RichImg objects that never touch the real terminal."""

    def _rich_img(**kwargs):
        kwargs.setdefault("console", console)
        return RichImg(**kwargs)

    return _rich_img
