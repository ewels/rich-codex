"""Tests for rich_codex.utils."""

import pytest
from git import Repo
from jsonschema.exceptions import ValidationError

from rich_codex import utils
from rich_codex.codex_search import CONFIG_SCHEMA
from rich_codex.rich_img import RichImg


@pytest.fixture
def schema():
    """Return the rich-codex JSON schema, as parsed once by the package itself."""
    return CONFIG_SCHEMA


class TestCleanList:
    """Tests for utils.clean_list()."""

    def test_strips_whitespace(self):
        assert utils.clean_list(["  foo  ", "\tbar\n"]) == ["foo", "bar"]

    def test_removes_blank_lines(self):
        assert utils.clean_list(["foo", "", "   ", "bar"]) == ["foo", "bar"]

    def test_removes_comments(self):
        assert utils.clean_list(["# a comment", "  # indented comment", "foo"]) == ["foo"]

    def test_keeps_trailing_comments(self):
        # Only lines that *start* with a hash are dropped
        assert utils.clean_list(["foo # not a comment"]) == ["foo # not a comment"]

    def test_empty_input(self):
        assert utils.clean_list([]) == []


class TestParseExtraEnv:
    """Tests for utils.parse_extra_env()."""

    def test_single_pair(self):
        assert utils.parse_extra_env("FOO=bar") == {"FOO": "bar"}

    def test_multiple_pairs(self):
        assert utils.parse_extra_env("FOO=bar\nBAZ=qux") == {"FOO": "bar", "BAZ": "qux"}

    def test_strips_whitespace_and_comments(self):
        assert utils.parse_extra_env("# comment\n  FOO = bar  \n\n") == {"FOO": "bar"}

    def test_value_may_contain_equals(self):
        assert utils.parse_extra_env("FOO=a=b=c") == {"FOO": "a=b=c"}

    def test_empty_value(self):
        assert utils.parse_extra_env("FOO=") == {"FOO": ""}

    def test_empty_string(self):
        assert utils.parse_extra_env("") == {}

    def test_missing_equals_raises(self):
        with pytest.raises(ValueError, match="Could not parse as 'KEY=value': 'FOO'"):
            utils.parse_extra_env("FOO")


class TestCleanImages:
    """Tests for utils.clean_images()."""

    def test_no_patterns(self, tmp_cwd):
        assert utils.clean_images(None, None, None) == []
        assert utils.clean_images("", None, None) == []

    def test_blank_and_comment_pattern_lines_are_ignored(self, tmp_cwd):
        stale = tmp_cwd / "stale.svg"
        stale.write_text("<svg />")
        assert utils.clean_images("\n\n", None, None) == []
        assert utils.clean_images("# *.svg\n", None, None) == []
        assert stale.exists()
        assert utils.clean_images("\n  *.svg  \n\n", None, None) == [stale]

    def test_no_matching_files(self, tmp_cwd):
        assert utils.clean_images("img/*.svg", None, None) == []

    def test_deletes_unknown_images(self, tmp_cwd):
        stale = tmp_cwd / "stale.svg"
        stale.write_text("<svg />")
        cleaned = utils.clean_images("*.svg", None, None)
        assert cleaned == [stale]
        assert not stale.exists()

    def test_keeps_images_generated_by_img_obj(self, tmp_cwd):
        kept = tmp_cwd / "kept.svg"
        kept.write_text("<svg />")
        img_obj = RichImg(img_paths=[str(kept)])
        assert utils.clean_images("*.svg", img_obj, None) == []
        assert kept.exists()

    def test_keeps_images_generated_by_codex_obj(self, tmp_cwd, codex_search):
        kept = tmp_cwd / "kept.svg"
        stale = tmp_cwd / "stale.svg"
        for path in (kept, stale):
            path.write_text("<svg />")
        codex_obj = codex_search()
        codex_obj.rich_imgs = [RichImg(img_paths=[str(kept)])]
        cleaned = utils.clean_images("*.svg", None, codex_obj)
        assert cleaned == [stale]
        assert kept.exists()
        assert not stale.exists()

    def test_multiple_glob_patterns(self, tmp_cwd):
        (tmp_cwd / "img").mkdir()
        one = tmp_cwd / "one.svg"
        two = tmp_cwd / "img" / "two.png"
        for path in (one, two):
            path.write_text("x")
        cleaned = utils.clean_images("*.svg\nimg/*.png", None, None)
        assert cleaned == sorted([one, two])


class TestCheckGitStatus:
    """Tests for utils.check_git_status()."""

    def test_not_a_git_repo(self, tmp_cwd):
        ok, msg = utils.check_git_status()
        assert ok is False
        assert msg == "Does not appear to be a git repository"

    def test_clean_repo(self, tmp_cwd):
        repo = Repo.init(tmp_cwd)
        (tmp_cwd / "file.txt").write_text("hello")
        repo.index.add(["file.txt"])
        repo.index.commit("initial", author_date="2022-01-01T00:00:00", commit_date="2022-01-01T00:00:00")
        ok, msg = utils.check_git_status()
        assert ok is True
        assert msg == "Git repo looks good."

    def test_untracked_files(self, tmp_cwd):
        Repo.init(tmp_cwd)
        (tmp_cwd / "untracked.txt").write_text("hello")
        ok, msg = utils.check_git_status()
        assert ok is False
        assert "untracked.txt" in msg

    def test_uncommitted_changes(self, tmp_cwd):
        repo = Repo.init(tmp_cwd)
        tracked = tmp_cwd / "file.txt"
        tracked.write_text("hello")
        repo.index.add(["file.txt"])
        repo.index.commit("initial", author_date="2022-01-01T00:00:00", commit_date="2022-01-01T00:00:00")
        tracked.write_text("changed")
        ok, msg = utils.check_git_status()
        assert ok is False
        assert "file.txt" in msg


class TestValidateConfig:
    """Tests for utils.validate_config()."""

    def test_valid_config(self, schema):
        config = {"outputs": [{"command": "echo hello", "img_paths": ["img/hello.svg"]}]}
        assert utils.validate_config(schema, config, "test.yml") is None

    def test_valid_global_only_config(self, schema):
        assert utils.validate_config(schema, {"terminal_width": 80}, "test.yml") is None

    def test_unknown_key_is_invalid(self, schema):
        with pytest.raises(ValidationError) as excinfo:
            utils.validate_config(schema, {"nonsense": True}, "test.yml")
        assert "test.yml" in str(excinfo.value)
        assert "was invalid" in str(excinfo.value)

    def test_line_number_in_message(self, schema):
        with pytest.raises(ValidationError) as excinfo:
            utils.validate_config(schema, {"nonsense": True}, "test.yml", 42)
        assert "line 42" in str(excinfo.value)

    def test_wrong_type_is_invalid(self, schema):
        with pytest.raises(ValidationError):
            utils.validate_config(schema, {"terminal_width": "wide"}, "test.yml")

    def test_bad_image_suffix_is_invalid(self, schema):
        config = {"outputs": [{"command": "echo hello", "img_paths": ["img/hello.jpg"]}]}
        with pytest.raises(ValidationError):
            utils.validate_config(schema, config, "test.yml")

    def test_output_needs_command_or_snippet(self, schema):
        """An output with neither command nor snippet fails the schema 'anyOf'."""
        config = {"outputs": [{"img_paths": ["img/hello.svg"]}]}
        with pytest.raises(ValidationError) as excinfo:
            utils.validate_config(schema, config, "test.yml")
        # anyOf errors carry sub-errors, which are printed as an indented list
        assert "*" in str(excinfo.value)
