"""Tests for rich_codex.rich_img."""

from pathlib import Path

import pytest
from conftest import svg_text

from rich_codex import rich_img as rich_img_module
from rich_codex.rich_img import RichImg


def rendered_text(img_obj):
    """Plain text of whatever was printed to the capture console."""
    return img_obj.capture_console.export_text()


class TestInit:
    """Tests for RichImg.__init__()."""

    def test_defaults(self, rich_img):
        img = rich_img()
        assert img.command is None
        assert img.snippet is None
        assert img.img_paths == []
        assert img.working_dir == Path.cwd()
        assert img.title == ""
        assert img.extra_env == {}
        assert img.timeout == 5
        assert img.truncated_text == "[..truncated..]"
        assert img.terminal_min_width == 80
        assert img.aborted is False
        assert img.source is None

    def test_numeric_strings_are_cast(self, rich_img):
        img = rich_img(head="3", tail="4", terminal_width="120", terminal_min_width="60")
        assert img.head == 3
        assert img.tail == 4
        assert img.terminal_width == 120
        assert img.terminal_min_width == 60

    def test_min_width_larger_than_width_is_dropped(self, rich_img):
        img = rich_img(terminal_width=60, terminal_min_width=100)
        assert img.terminal_min_width is None

    def test_min_width_smaller_than_width_is_kept(self, rich_img):
        img = rich_img(terminal_width=100, terminal_min_width=60)
        assert img.terminal_min_width == 60

    def test_source_becomes_a_path(self, rich_img):
        assert rich_img(source="docs/index.md").source == Path("docs/index.md")

    def test_working_dir_becomes_a_path(self, rich_img, tmp_cwd):
        assert rich_img(working_dir=str(tmp_cwd)).working_dir == tmp_cwd


class TestEqualityAndHashing:
    """Tests for __eq__, __hash__ and _hash_no_fn()."""

    def test_identical_objects_are_equal(self, rich_img):
        assert rich_img(command="echo hi", img_paths=["a.svg"]) == rich_img(command="echo hi", img_paths=["a.svg"])

    def test_different_commands_are_not_equal(self, rich_img):
        assert rich_img(command="echo hi") != rich_img(command="echo bye")

    def test_different_paths_are_not_equal(self, rich_img):
        assert rich_img(command="echo hi", img_paths=["a.svg"]) != rich_img(command="echo hi", img_paths=["b.svg"])

    def test_source_line_is_ignored(self, rich_img):
        """Line numbers say where an image was defined, not what it renders."""
        assert rich_img(command="echo hi", source_line=1) == rich_img(command="echo hi", source_line=99)

    def test_source_is_not_ignored(self, rich_img):
        assert rich_img(command="echo hi", source="a.md") != rich_img(command="echo hi", source="b.md")

    def test_comparison_with_other_types(self, rich_img):
        assert rich_img().__eq__("not a RichImg") is NotImplemented
        assert rich_img() != "not a RichImg"

    def test_hash_matches_equality(self, rich_img):
        assert hash(rich_img(command="echo hi")) == hash(rich_img(command="echo hi"))
        assert hash(rich_img(command="echo hi")) != hash(rich_img(command="echo bye"))

    def test_hashable_in_a_set(self, rich_img):
        imgs = [rich_img(command="echo hi"), rich_img(command="echo hi"), rich_img(command="echo bye")]
        assert len(set(imgs)) == 2

    def test_hash_no_fn_ignores_img_paths(self, rich_img):
        a = rich_img(command="echo hi", img_paths=["a.svg"])
        b = rich_img(command="echo hi", img_paths=["b.svg"])
        assert a._hash_no_fn() == b._hash_no_fn()
        assert hash(a) != hash(b)

    def test_hash_no_fn_still_uses_command(self, rich_img):
        a = rich_img(command="echo hi", img_paths=["a.svg"])
        b = rich_img(command="echo bye", img_paths=["a.svg"])
        assert a._hash_no_fn() != b._hash_no_fn()


class TestConfirmCommand:
    """Tests for RichImg.confirm_command()."""

    def test_no_command_is_always_confirmed(self, rich_img):
        assert rich_img().confirm_command() is True

    def test_no_confirm_skips_the_prompt(self, rich_img, monkeypatch):
        monkeypatch.setattr(
            rich_img_module.Confirm, "ask", lambda *a, **kw: pytest.fail("should not have prompted")  # noqa: ARG005
        )
        img = rich_img(command="echo hi")
        img.no_confirm = True
        assert img.confirm_command() is True

    @pytest.mark.parametrize("answer", [True, False])
    def test_prompt_answer_is_returned(self, rich_img, monkeypatch, answer):
        monkeypatch.setattr(rich_img_module.Confirm, "ask", lambda *a, **kw: answer)
        assert rich_img(command="echo hi").confirm_command() is answer


class TestRunCommand:
    """Tests for RichImg.run_command()."""

    def test_no_command(self, rich_img):
        assert rich_img().run_command() is None

    @pytest.mark.parametrize("command", ["rm -rf /", "cp a b", "mv a b", "sudo rm x"])
    def test_dangerous_commands_are_aborted(self, rich_img, command):
        img = rich_img(command=command)
        assert img.run_command() is False
        assert img.aborted is True

    def test_similar_but_safe_command_is_allowed(self, rich_img, tmp_cwd):
        img = rich_img(command="echo remove")
        img.run_command()
        assert img.aborted is False
        assert "remove" in rendered_text(img)

    def test_command_output_is_captured(self, rich_img, tmp_cwd):
        img = rich_img(command="echo hello world")
        img.run_command()
        output = rendered_text(img)
        assert "$ echo hello world" in output
        assert "hello world" in output

    def test_stderr_is_captured(self, rich_img, tmp_cwd):
        img = rich_img(command="echo oh no >&2")
        img.run_command()
        assert "oh no" in rendered_text(img)

    def test_command_is_stripped(self, rich_img, tmp_cwd):
        img = rich_img(command="  echo hi  ")
        img.run_command()
        assert img.command == "echo hi"

    def test_hide_command(self, rich_img, tmp_cwd):
        img = rich_img(command="echo hello", hide_command=True)
        img.run_command()
        output = rendered_text(img)
        assert "$ echo hello" not in output
        assert "hello" in output

    def test_fake_command_is_shown_instead(self, rich_img, tmp_cwd):
        img = rich_img(command="echo hello", fake_command="magic --please")
        img.run_command()
        output = rendered_text(img)
        assert "$ magic --please" in output
        assert "$ echo hello" not in output

    def test_title_command(self, rich_img, tmp_cwd):
        img = rich_img(command="echo hello", title_command=True)
        img.run_command()
        assert img.title == "echo hello"

    def test_title_command_prefers_fake_command(self, rich_img, tmp_cwd):
        img = rich_img(command="echo hello", fake_command="magic", title_command=True)
        img.run_command()
        assert img.title == "magic"

    def test_explicit_title_wins_over_title_command(self, rich_img, tmp_cwd):
        img = rich_img(command="echo hello", title="My title", title_command=True)
        img.run_command()
        assert img.title == "My title"

    def test_working_dir_is_used_and_created(self, rich_img, tmp_cwd):
        work_dir = tmp_cwd / "nested" / "dir"
        img = rich_img(command="pwd", working_dir=str(work_dir))
        img.run_command()
        assert work_dir.is_dir()
        assert str(work_dir) in rendered_text(img)

    def test_extra_env(self, rich_img, tmp_cwd):
        img = rich_img(command="echo $RC_TEST_VAR", extra_env={"RC_TEST_VAR": "set-by-test"})
        img.run_command()
        assert "set-by-test" in rendered_text(img)

    def test_extra_env_values_are_stringified(self, rich_img, tmp_cwd):
        img = rich_img(command="echo $RC_TEST_NUM", extra_env={"RC_TEST_NUM": 42})
        img.run_command()
        assert "42" in rendered_text(img)

    def test_before_command_runs_first(self, rich_img, tmp_cwd):
        img = rich_img(command="cat before.txt", before_command="echo made-by-before > before.txt")
        img.run_command()
        assert "made-by-before" in rendered_text(img)

    def test_after_command_runs(self, rich_img, tmp_cwd):
        img = rich_img(command="echo hi", after_command="echo made-by-after > after.txt")
        img.run_command()
        assert (tmp_cwd / "after.txt").exists()

    def test_head_truncates_output(self, rich_img, tmp_cwd):
        img = rich_img(command="printf 'one\\ntwo\\nthree\\nfour\\n'", head=2, hide_command=True)
        img.run_command()
        output = rendered_text(img)
        assert "one" in output
        assert "two" in output
        assert "four" not in output
        assert "[..truncated..]" in output

    def test_tail_truncates_output(self, rich_img, tmp_cwd):
        img = rich_img(command="printf 'one\\ntwo\\nthree\\nfour\\n'", tail=2, hide_command=True)
        img.run_command()
        output = rendered_text(img)
        assert "one" not in output
        assert "four" in output
        assert "[..truncated..]" in output

    def test_head_and_tail_together(self, rich_img, tmp_cwd):
        # No trailing newline, otherwise the empty final line takes the one 'tail' slot
        img = rich_img(command="printf 'one\\ntwo\\nthree\\nfour\\nfive'", head=1, tail=1, hide_command=True)
        img.run_command()
        output = rendered_text(img)
        assert "one" in output
        assert "five" in output
        assert "three" not in output

    def test_head_larger_than_output_is_dropped(self, rich_img, tmp_cwd):
        img = rich_img(command="printf 'one\\ntwo\\n'", head=100, hide_command=True)
        img.run_command()
        assert img.head is None
        assert "[..truncated..]" not in rendered_text(img)

    def test_tail_larger_than_output_is_dropped(self, rich_img, tmp_cwd):
        img = rich_img(command="printf 'one\\ntwo\\n'", tail=100)
        img.run_command()
        assert img.tail is None

    def test_custom_truncated_text(self, rich_img, tmp_cwd):
        img = rich_img(command="printf 'one\\ntwo\\nthree\\n'", head=1, truncated_text="~snip~")
        img.run_command()
        assert "~snip~" in rendered_text(img)

    def test_truncated_text_printed_only_once(self, rich_img, tmp_cwd):
        img = rich_img(command="printf 'one\\ntwo\\nthree\\nfour\\n'", head=1)
        img.run_command()
        assert rendered_text(img).count("[..truncated..]") == 1

    def test_trim_after(self, rich_img, tmp_cwd):
        img = rich_img(command="printf 'keep\\nSTOP HERE\\ndrop\\n'", trim_after="STOP HERE", hide_command=True)
        img.run_command()
        output = rendered_text(img)
        assert "keep" in output
        assert "STOP HERE" in output
        assert "drop" not in output

    def test_terminal_width(self, rich_img, tmp_cwd):
        img = rich_img(command="echo hi", terminal_width=42, notrim=True)
        img.run_command()
        assert img.capture_console.width == 42

    def test_terminal_min_width_expands_for_long_lines(self, rich_img, tmp_cwd):
        long_line = "x" * 120
        img = rich_img(command=f"echo {long_line}", terminal_min_width=80)
        img.run_command()
        assert img.capture_console.width >= 120

    def test_terminal_min_width_is_a_floor(self, rich_img, tmp_cwd):
        img = rich_img(command="echo hi", terminal_min_width=80)
        img.run_command()
        assert img.capture_console.width == 80

    def test_timeout_kills_the_command(self, rich_img, tmp_cwd, caplog):
        img = rich_img(command="sleep 30", timeout=0.2)
        img.run_command()
        assert "timed out" in caplog.text

    def test_use_pty(self, rich_img, tmp_cwd, tty_stdin):
        img = rich_img(command="echo hello-from-pty", use_pty=True, terminal_width=100, notrim=True)
        img.run_command()
        assert "hello-from-pty" in rendered_text(img)

    def test_use_pty_falls_back_when_import_fails(self, rich_img, tmp_cwd, block_import, caplog):
        """On Windows the pty import fails, and we fall back to plain subprocess."""
        block_import("pty", "fcntl", "termios")
        img = rich_img(command="echo fallback-output", use_pty=True)
        img.run_command()
        assert "Could not use pty" in caplog.text
        assert "fallback-output" in rendered_text(img)

    def test_pty_timeout_is_handled(self, rich_img, tmp_cwd, caplog, tty_stdin):
        img = rich_img(command="sleep 30", use_pty=True, timeout=0.2)
        img.run_command()
        assert "timed out" in caplog.text


class TestFormatSnippet:
    """Tests for RichImg.format_snippet()."""

    def test_no_snippet(self, rich_img):
        assert rich_img().format_snippet() is None

    def test_plain_snippet(self, rich_img):
        img = rich_img(snippet="hello snippet", snippet_syntax="text")
        img.format_snippet()
        assert "hello snippet" in rendered_text(img)

    def test_json_is_pretty_printed(self, rich_img):
        img = rich_img(snippet='{"a": 1, "b": [2, 3]}')
        img.format_snippet()
        assert img.snippet_syntax == "json"
        assert img.snippet == '{\n    "a": 1,\n    "b": [\n        2,\n        3\n    ]\n}'

    def test_explicit_json_syntax_is_pretty_printed(self, rich_img):
        img = rich_img(snippet='{"a":1}', snippet_syntax="json")
        img.format_snippet()
        assert '"a": 1' in img.snippet

    def test_invalid_json_is_left_alone(self, rich_img):
        img = rich_img(snippet="not json at all")
        img.format_snippet()
        assert img.snippet == "not json at all"
        assert img.snippet_syntax is None

    def test_non_json_syntax_is_not_parsed(self, rich_img):
        img = rich_img(snippet='{"a":1}', snippet_syntax="python")
        img.format_snippet()
        assert img.snippet == '{"a":1}'
        assert img.snippet_syntax == "python"

    def test_terminal_min_width_expands_for_long_lines(self, rich_img):
        img = rich_img(snippet="y" * 150, snippet_syntax="text", terminal_min_width=80)
        img.format_snippet()
        assert img.capture_console.width >= 150

    def test_terminal_width_is_used_when_notrim(self, rich_img):
        img = rich_img(snippet="short", snippet_syntax="text", terminal_width=55, notrim=True)
        img.format_snippet()
        assert img.capture_console.width == 55

    def test_custom_snippet_theme(self, rich_img):
        img = rich_img(snippet="print('hi')", snippet_syntax="python", snippet_theme="dracula")
        img.format_snippet()
        assert "print" in rendered_text(img)


class TestGetOutput:
    """Tests for RichImg.get_output()."""

    def test_dispatches_to_run_command(self, rich_img, tmp_cwd):
        img = rich_img(command="echo dispatched")
        img.get_output()
        assert "dispatched" in rendered_text(img)

    def test_dispatches_to_format_snippet(self, rich_img):
        img = rich_img(snippet="snippet content", snippet_syntax="text")
        img.get_output()
        assert "snippet content" in rendered_text(img)

    def test_command_wins_over_snippet(self, rich_img, tmp_cwd):
        img = rich_img(command="echo from-command", snippet="from-snippet")
        img.get_output()
        assert "from-command" in rendered_text(img)

    def test_warns_with_neither(self, rich_img, caplog):
        rich_img().get_output()
        assert "no command or snippet" in caplog.text


class TestEnoughImageDifference:
    """Tests for RichImg._enough_image_difference()."""

    def test_new_file_is_always_saved(self, rich_img, tmp_cwd, caplog):
        new_file = tmp_cwd / "new.svg"
        new_file.write_text("<svg>hello</svg>")
        img = rich_img()
        assert img._enough_image_difference(str(new_file), str(tmp_cwd / "target.svg")) is True
        assert img.num_img_saved == 1
        assert "new image" in caplog.text

    def test_identical_files_are_skipped(self, rich_img, tmp_cwd):
        content = "<svg>identical</svg>"
        new_file = tmp_cwd / "new.svg"
        old_file = tmp_cwd / "old.svg"
        new_file.write_text(content)
        old_file.write_text(content)
        img = rich_img()
        assert img._enough_image_difference(str(new_file), str(old_file)) is False
        assert img.num_img_skipped == 1

    def test_changed_file_is_saved(self, rich_img, tmp_cwd):
        new_file = tmp_cwd / "new.svg"
        old_file = tmp_cwd / "old.svg"
        new_file.write_text("<svg>completely different content here</svg>")
        old_file.write_text("<svg>old</svg>")
        img = rich_img()
        assert img._enough_image_difference(str(new_file), str(old_file)) is True

    def test_min_pct_diff_suppresses_small_changes(self, rich_img, tmp_cwd):
        new_file = tmp_cwd / "new.svg"
        old_file = tmp_cwd / "old.svg"
        new_file.write_text("<svg>" + "a" * 500 + "b</svg>")
        old_file.write_text("<svg>" + "a" * 500 + "c</svg>")
        img = rich_img(min_pct_diff=50)
        assert img._enough_image_difference(str(new_file), str(old_file)) is False

    def test_min_pct_diff_allows_large_changes(self, rich_img, tmp_cwd):
        new_file = tmp_cwd / "new.svg"
        old_file = tmp_cwd / "old.svg"
        new_file.write_text("totally new content that shares nothing")
        old_file.write_text("xxxxxxxxxxxxxxxxxxxx")
        img = rich_img(min_pct_diff=10)
        assert img._enough_image_difference(str(new_file), str(old_file)) is True

    def test_skip_change_regex_matching_all_diffs(self, rich_img, tmp_cwd, caplog):
        new_file = tmp_cwd / "new.svg"
        old_file = tmp_cwd / "old.svg"
        new_file.write_text("stable line\ngenerated: 2022-01-01\n")
        old_file.write_text("stable line\ngenerated: 1999-12-31\n")
        img = rich_img(skip_change_regex="generated:")
        assert img._enough_image_difference(str(new_file), str(old_file)) is False
        assert "Checking diff" in caplog.text

    def test_blank_skip_change_regex_lines_are_ignored(self, rich_img, tmp_cwd):
        """An empty pattern would match every line and silently freeze every image."""
        new_file = tmp_cwd / "new.svg"
        old_file = tmp_cwd / "old.svg"
        new_file.write_text("changed line\ngenerated: 2022-01-01\n")
        old_file.write_text("original line\ngenerated: 1999-12-31\n")
        img = rich_img(skip_change_regex="generated:\n\n")
        assert img._enough_image_difference(str(new_file), str(old_file)) is True

    def test_skip_change_regex_not_matching_all_diffs(self, rich_img, tmp_cwd):
        new_file = tmp_cwd / "new.svg"
        old_file = tmp_cwd / "old.svg"
        new_file.write_text("changed line\ngenerated: 2022-01-01\n")
        old_file.write_text("original line\ngenerated: 1999-12-31\n")
        img = rich_img(skip_change_regex="generated:")
        assert img._enough_image_difference(str(new_file), str(old_file)) is True

    @pytest.mark.parametrize(
        ("new_name", "old_name"),
        [
            ("new.pdf", "old.pdf"),
            # The new file is normally a suffix-less temp file, so the target picks the regexes
            ("tmp1234", "old.pdf"),
            ("tmp1234", "old.PDF"),
        ],
    )
    def test_builtin_pdf_regex_is_used(self, rich_img, tmp_cwd, new_name, old_name):
        """Ignore the /CreationDate line, which always differs between two PDFs."""
        new_file = tmp_cwd / new_name
        old_file = tmp_cwd / old_name
        new_file.write_text("%PDF-1.4\n/CreationDate (D:20220101)\ncontent\n")
        old_file.write_text("%PDF-1.4\n/CreationDate (D:19991231)\ncontent\n")
        img = rich_img()
        assert img._enough_image_difference(str(new_file), str(old_file)) is False

    def test_no_lost_lines_to_match(self, rich_img, tmp_cwd, caplog):
        """The old file only gained lines, so there is nothing for the regexes to match."""
        new_file = tmp_cwd / "new.svg"
        old_file = tmp_cwd / "old.svg"
        new_file.write_text("first line\nsecond line\n")
        old_file.write_text("first line\nsecond line\nthird line\n")
        img = rich_img(skip_change_regex="line")
        assert img._enough_image_difference(str(new_file), str(old_file)) is True
        assert "no diff found" in caplog.text

    def test_binary_files_with_no_decodable_text(self, rich_img, tmp_cwd, caplog):
        """Undecodable bytes leave nothing to run the skip regexes against."""
        new_file = tmp_cwd / "new.pdf"
        old_file = tmp_cwd / "old.pdf"
        new_file.write_bytes(b"\xff\xfe\xff")
        old_file.write_bytes(b"\xfd")
        img = rich_img()
        assert img._enough_image_difference(str(new_file), str(old_file)) is True
        assert "no text to diff" in caplog.text

    def test_duplicate_target_filename_warns(self, rich_img, tmp_cwd, caplog):
        new_file = tmp_cwd / "new.svg"
        new_file.write_text("<svg />")
        target = str(tmp_cwd / "target.svg")
        img = rich_img()
        img._enough_image_difference(str(new_file), target)
        img._enough_image_difference(str(new_file), target)
        assert "More than one image with file name" in caplog.text
        assert img.saved_img_paths == [target]


class TestSaveImages:
    """Tests for RichImg.save_images()."""

    def rendered(self, rich_img, **kwargs):
        """Build a RichImg with a rendered snippet, ready to save."""
        img = rich_img(snippet="hello world", snippet_syntax="text", **kwargs)
        img.format_snippet()
        return img

    def test_aborted_does_nothing(self, rich_img, tmp_cwd):
        img = rich_img(img_paths=[str(tmp_cwd / "out.svg")])
        img.aborted = True
        img.save_images()
        assert not (tmp_cwd / "out.svg").exists()

    def test_no_paths_warns(self, rich_img, tmp_cwd, caplog):
        rich_img().save_images()
        assert "no paths" in caplog.text

    def test_saves_an_svg(self, rich_img, tmp_cwd):
        out = tmp_cwd / "out.svg"
        img = self.rendered(rich_img, img_paths=[str(out)])
        img.save_images()
        assert out.exists()
        assert "hello world" in svg_text(out)
        assert img.num_img_saved == 1
        assert img.saved_img_paths == [str(out)]

    def test_creates_parent_directories(self, rich_img, tmp_cwd):
        out = tmp_cwd / "deeply" / "nested" / "out.svg"
        img = self.rendered(rich_img, img_paths=[str(out)])
        img.save_images()
        assert out.exists()

    def test_uppercase_suffix(self, rich_img, tmp_cwd):
        out = tmp_cwd / "out.SVG"
        img = self.rendered(rich_img, img_paths=[str(out)])
        img.save_images()
        assert out.exists()

    def test_second_svg_is_copied_from_the_first(self, rich_img, tmp_cwd):
        first = tmp_cwd / "first.svg"
        second = tmp_cwd / "second.svg"
        img = self.rendered(rich_img, img_paths=[str(first), str(second)])
        img.save_images()
        assert first.read_text() == second.read_text()
        assert img.num_img_saved == 2

    def test_unchanged_image_is_skipped_on_rerun(self, rich_img, tmp_cwd):
        out = tmp_cwd / "out.svg"
        self.rendered(rich_img, img_paths=[str(out)]).save_images()
        first_mtime = out.stat().st_mtime_ns
        img = self.rendered(rich_img, img_paths=[str(out)])
        img.save_images()
        assert img.num_img_skipped == 1
        assert img.num_img_saved == 0
        assert out.stat().st_mtime_ns == first_mtime

    def test_terminal_theme(self, rich_img, tmp_cwd):
        out = tmp_cwd / "out.svg"
        img = self.rendered(rich_img, img_paths=[str(out)], terminal_theme="MONOKAI")
        img.save_images()
        assert out.exists()

    def test_unknown_terminal_theme_falls_back(self, rich_img, tmp_cwd, caplog):
        out = tmp_cwd / "out.svg"
        img = self.rendered(rich_img, img_paths=[str(out)], terminal_theme="NOT_A_THEME")
        img.save_images()
        assert "not found" in caplog.text
        assert out.exists()

    def test_title_is_used(self, rich_img, tmp_cwd):
        out = tmp_cwd / "out.svg"
        img = self.rendered(rich_img, img_paths=[str(out)], title="My Terminal")
        img.save_images()
        assert "My Terminal" in svg_text(out)

    def test_temporary_files_are_cleaned_up(self, rich_img, tmp_cwd):
        import tempfile

        before = set(Path(tempfile.gettempdir()).iterdir())
        img = self.rendered(rich_img, img_paths=[str(tmp_cwd / "out.svg")])
        img.save_images()
        assert set(Path(tempfile.gettempdir()).iterdir()) == before

    def test_invalid_path_is_skipped(self, rich_img, tmp_cwd, caplog, monkeypatch):
        valid = tmp_cwd / "valid.svg"
        img = self.rendered(rich_img, img_paths=[str(valid), "/proc/nope/out.svg"])

        real_mkdir = Path.mkdir

        def fake_mkdir(self, *args, **kwargs):
            if "nope" in str(self):
                raise PermissionError("nope")
            return real_mkdir(self, *args, **kwargs)

        monkeypatch.setattr(Path, "mkdir", fake_mkdir)
        img.save_images()
        assert "Invalid path" in caplog.text
        assert valid.exists()

    def test_png_conversion(self, rich_img, tmp_cwd):
        pytest.importorskip("cairosvg", reason="CairoSVG is an optional extra")
        out = tmp_cwd / "out.png"
        img = self.rendered(rich_img, img_paths=[str(out)])
        img.save_images()
        assert out.read_bytes().startswith(b"\x89PNG")

    def test_pdf_conversion(self, rich_img, tmp_cwd):
        pytest.importorskip("cairosvg", reason="CairoSVG is an optional extra")
        out = tmp_cwd / "out.pdf"
        img = self.rendered(rich_img, img_paths=[str(out)])
        img.save_images()
        assert out.read_bytes().startswith(b"%PDF")

    def test_second_png_is_copied_from_the_first(self, rich_img, tmp_cwd):
        pytest.importorskip("cairosvg", reason="CairoSVG is an optional extra")
        first = tmp_cwd / "first.png"
        second = tmp_cwd / "second.png"
        img = self.rendered(rich_img, img_paths=[str(first), str(second)])
        img.save_images()
        assert first.read_bytes() == second.read_bytes()

    def test_second_pdf_is_copied_from_the_first(self, rich_img, tmp_cwd):
        pytest.importorskip("cairosvg", reason="CairoSVG is an optional extra")
        first = tmp_cwd / "first.pdf"
        second = tmp_cwd / "second.pdf"
        img = self.rendered(rich_img, img_paths=[str(first), str(second)])
        img.save_images()
        assert first.read_bytes() == second.read_bytes()

    def test_png_and_pdf_share_one_svg(self, rich_img, tmp_cwd):
        pytest.importorskip("cairosvg", reason="CairoSVG is an optional extra")
        paths = [tmp_cwd / f"out.{suffix}" for suffix in ("png", "pdf")]
        img = self.rendered(rich_img, img_paths=[str(p) for p in paths])
        img.save_images()
        assert all(p.exists() for p in paths)
        assert img.num_img_saved == 2

    def test_all_three_formats_share_one_svg(self, rich_img, tmp_cwd):
        pytest.importorskip("cairosvg", reason="CairoSVG is an optional extra")
        paths = [tmp_cwd / f"out.{suffix}" for suffix in ("svg", "png", "pdf")]
        img = self.rendered(rich_img, img_paths=[str(p) for p in paths])
        img.save_images()
        assert all(p.exists() for p in paths)
        assert img.num_img_saved == 3

    def test_missing_cairosvg_is_reported(self, rich_img, tmp_cwd, caplog, block_import):
        block_import("cairosvg")
        out = tmp_cwd / "out.png"
        img = self.rendered(rich_img, img_paths=[str(out)])
        img.save_images()
        assert "CairoSVG not installed" in caplog.text
        assert not out.exists()

    def test_missing_cairo_system_libs_are_reported(self, rich_img, tmp_cwd, caplog, block_import):
        block_import("cairosvg", exc=OSError)
        out = tmp_cwd / "out.png"
        img = self.rendered(rich_img, img_paths=[str(out)])
        img.save_images()
        assert "Missing" in caplog.text
        assert not out.exists()


class TestModuleConstants:
    """Tests for the attribute lists derived from the config schema."""

    def test_hash_attrs_exclude_source_line(self):
        assert "source_line" not in rich_img_module.HASH_ATTRS
        assert "command" in rich_img_module.HASH_ATTRS
        assert "source" in rich_img_module.HASH_ATTRS

    def test_hash_attrs_no_fn_excludes_img_paths(self):
        assert "img_paths" not in rich_img_module.HASH_ATTRS_NO_FN
        assert "img_paths" in rich_img_module.HASH_ATTRS

    def test_every_hash_attr_exists_on_the_object(self):
        img = RichImg()
        for attr in rich_img_module.HASH_ATTRS:
            assert hasattr(img, attr), f"RichImg has no attribute '{attr}'"


def test_ignored_commands_are_matched_as_prefixes(rich_img, tmp_cwd):
    """Anything starting with an ignored command is refused, even 'rmdir'."""
    assert rich_img(command="rmdir foo").run_command() is False
    assert rich_img(command="echo rm").aborted is False
