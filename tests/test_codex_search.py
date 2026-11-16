"""Tests for rich_codex.codex_search."""

import os
from pathlib import Path

import pytest
from conftest import write
from jsonschema.exceptions import ValidationError

from rich_codex import codex_search as codex_search_module
from rich_codex.rich_img import RichImg


class TestInit:
    """Tests for CodexSearch.__init__()."""

    def test_default_search_include(self, tmp_cwd, codex_search):
        assert codex_search().search_include == ["**/*.md", "**/*.mdx"]

    def test_custom_search_include(self, tmp_cwd, codex_search):
        cs = codex_search(search_include="docs/*.md\n# a comment\n\nREADME.md")
        assert cs.search_include == ["docs/*.md", "README.md"]

    def test_default_search_exclude(self, tmp_cwd, codex_search):
        assert codex_search().search_exclude == ["**/.git*", "**/.git*/**", "**/node_modules/**"]

    def test_custom_search_exclude_is_appended(self, tmp_cwd, codex_search):
        cs = codex_search(search_exclude="build/**")
        assert cs.search_exclude[-1] == "build/**"
        assert "**/node_modules/**" in cs.search_exclude

    def test_gitignore_is_appended_to_excludes(self, tmp_cwd, codex_search):
        write(tmp_cwd / ".gitignore", "# comment\n*.tmp\n\nbuild/\n")
        cs = codex_search()
        assert "*.tmp" in cs.search_exclude
        assert "build/" in cs.search_exclude

    def test_missing_gitignore_is_fine(self, tmp_cwd, codex_search):
        assert "*.tmp" not in codex_search().search_exclude

    def test_default_config_paths(self, tmp_cwd, codex_search):
        cs = codex_search()
        assert ".rich-codex.yml" in cs.configs
        assert ".github/rich-codex.yaml" in cs.configs
        assert len(cs.configs) == 6

    def test_custom_configs_are_appended(self, tmp_cwd, codex_search):
        assert codex_search(configs="my-config.yml").configs[-1] == "my-config.yml"

    def test_schema_is_loaded(self, tmp_cwd, codex_search):
        assert "outputs" in codex_search().config_schema["properties"]

    def test_counters_start_at_zero(self, tmp_cwd, codex_search):
        cs = codex_search()
        assert cs.rich_imgs == []
        assert cs.num_img_saved == 0
        assert cs.num_img_skipped == 0


class TestMergeConfig:
    """Tests for _merge_local_class_attrs() and _merge_config_values()."""

    def test_class_attr_fills_missing_local_key(self, tmp_cwd, codex_search):
        cs = codex_search(terminal_width=120)
        assert cs._merge_local_class_attrs({})["terminal_width"] == 120

    def test_local_key_wins(self, tmp_cwd, codex_search):
        cs = codex_search(terminal_width=120)
        assert cs._merge_local_class_attrs({"terminal_width": 60})["terminal_width"] == 60

    def test_unset_class_attrs_are_not_added(self, tmp_cwd, codex_search):
        assert "terminal_width" not in codex_search()._merge_local_class_attrs({})

    def test_extra_env_is_merged_not_replaced(self, tmp_cwd, codex_search):
        cs = codex_search(extra_env={"GLOBAL": "1", "SHARED": "global"})
        merged = cs._merge_local_class_attrs({"extra_env": {"LOCAL": "2", "SHARED": "local"}})
        assert merged["extra_env"] == {"GLOBAL": "1", "LOCAL": "2", "SHARED": "local"}

    @pytest.mark.parametrize(
        ("base", "override", "expected"),
        [
            ({"a": 1}, {"b": 2}, {"a": 1, "b": 2}),
            ({"a": 1}, {"a": 2}, {"a": 2}),
            (None, {"a": 1}, {"a": 1}),
            ({"a": 1}, None, {"a": 1}),
            (None, None, {}),
        ],
    )
    def test_merge_config_values(self, tmp_cwd, codex_search, base, override, expected):
        assert codex_search()._merge_config_values(base, override) == expected


class TestSearchFiles:
    """Tests for CodexSearch.search_files()."""

    def test_no_files_to_search(self, tmp_cwd, codex_search):
        cs = codex_search()
        assert cs.search_files() == 0
        assert cs.rich_imgs == []

    def test_finds_a_command_image(self, tmp_cwd, codex_search):
        write(tmp_cwd / "README.md", "![`echo hello`](img/hello.svg)\n")
        cs = codex_search()
        assert cs.search_files() == 0
        assert len(cs.rich_imgs) == 1
        img = cs.rich_imgs[0]
        assert img.command == "echo hello"
        assert img.img_paths == [str(tmp_cwd / "img" / "hello.svg")]
        assert img.source_type == "search"
        assert img.source_line == 1

    def test_image_title(self, tmp_cwd, codex_search):
        write(tmp_cwd / "README.md", '![`echo hello`](img/hello.svg "My title")\n')
        cs = codex_search()
        cs.search_files()
        assert cs.rich_imgs[0].title == "My title"

    def test_plain_image_is_ignored(self, tmp_cwd, codex_search):
        write(tmp_cwd / "README.md", "![just a picture](img/photo.svg)\n")
        cs = codex_search()
        assert cs.search_files() == 0
        assert cs.rich_imgs == []

    def test_html_comment_config(self, tmp_cwd, codex_search):
        write(tmp_cwd / "README.md", "<!-- RICH-CODEX terminal_width: 60 -->\n![`echo hi`](img/hi.svg)\n")
        cs = codex_search()
        cs.search_files()
        assert cs.rich_imgs[0].terminal_width == 60

    def test_mdx_comment_config(self, tmp_cwd, codex_search):
        """MDX v2+ doesn't allow HTML comments, so JSX comments are supported too."""
        write(tmp_cwd / "docs.mdx", "{/* RICH-CODEX terminal_width: 60 */}\n![`echo hi`](img/hi.svg)\n")
        cs = codex_search()
        cs.search_files()
        assert len(cs.rich_imgs) == 1
        assert cs.rich_imgs[0].terminal_width == 60

    def test_multiline_html_comment_config(self, tmp_cwd, codex_search):
        write(
            tmp_cwd / "README.md",
            """
            <!-- RICH-CODEX
            terminal_width: 60
            hide_command: true
            -->
            ![`echo hi`](img/hi.svg)
            """,
        )
        cs = codex_search()
        cs.search_files()
        assert cs.rich_imgs[0].terminal_width == 60
        assert cs.rich_imgs[0].hide_command is True

    def test_multiline_mdx_comment_config(self, tmp_cwd, codex_search):
        write(
            tmp_cwd / "docs.mdx",
            """
            {/* RICH-CODEX
            terminal_width: 60
            */}
            ![`echo hi`](img/hi.svg)
            """,
        )
        cs = codex_search()
        cs.search_files()
        assert cs.rich_imgs[0].terminal_width == 60

    def test_snippet_from_config(self, tmp_cwd, codex_search):
        write(
            tmp_cwd / "README.md",
            """
            <!-- RICH-CODEX
            snippet: 'Hello, world!'
            -->
            ![](img/snippet.svg)
            """,
        )
        cs = codex_search()
        cs.search_files()
        assert len(cs.rich_imgs) == 1
        assert cs.rich_imgs[0].snippet == "Hello, world!"
        assert cs.rich_imgs[0].command is None

    def test_plain_image_after_a_config_block_warns(self, tmp_cwd, codex_search, caplog):
        """Config that doesn't produce an image is almost certainly a mistake."""
        write(tmp_cwd / "README.md", "<!-- RICH-CODEX terminal_width: 60 -->\n![a photo](img/photo.png)\n")
        cs = codex_search()
        assert cs.search_files() == 0
        assert cs.rich_imgs == []
        assert "Skipped image but local_config was not empty" in caplog.text

    def test_skip_config(self, tmp_cwd, codex_search):
        write(tmp_cwd / "README.md", "<!-- RICH-CODEX skip: true -->\n![`echo hi`](img/hi.svg)\n")
        cs = codex_search()
        assert cs.search_files() == 0
        assert cs.rich_imgs == []

    def test_invalid_yaml_is_an_error(self, tmp_cwd, codex_search, caplog):
        write(tmp_cwd / "README.md", "<!-- RICH-CODEX ]not: [valid -->\n![`echo hi`](img/hi.svg)\n")
        cs = codex_search()
        assert cs.search_files() == 1
        assert "Error parsing config YAML" in caplog.text

    def test_non_dict_yaml_is_an_error(self, tmp_cwd, codex_search, caplog):
        """Counted as an error and the config dropped, exactly like unparseable YAML."""
        write(tmp_cwd / "README.md", "<!-- RICH-CODEX just a string -->\n![`echo hi`](img/hi.svg)\n")
        cs = codex_search()
        assert cs.search_files() == 1
        assert "config YAML is not a dictionary" in caplog.text
        assert cs.rich_imgs[0].terminal_width is None

    def test_search_continues_after_a_non_dict_config(self, tmp_cwd, codex_search):
        """A bad config in one file shouldn't abort the rest of the search."""
        write(tmp_cwd / "a-bad.md", "<!-- RICH-CODEX just a string -->\n![`echo bad`](img/bad.svg)\n")
        write(tmp_cwd / "b-good.md", "![`echo good`](img/good.svg)\n")
        cs = codex_search()
        assert cs.search_files() == 1
        assert "echo good" in [img.command for img in cs.rich_imgs]

    def test_schema_violation_is_an_error(self, tmp_cwd, codex_search, caplog):
        write(tmp_cwd / "README.md", "<!-- RICH-CODEX terminal_width: wide -->\n![`echo hi`](img/hi.svg)\n")
        cs = codex_search()
        assert cs.search_files() == 1
        assert cs.rich_imgs == []
        assert "was invalid" in caplog.text

    def test_bad_image_suffix_is_an_error(self, tmp_cwd, codex_search):
        write(tmp_cwd / "README.md", "![`echo hi`](img/hi.jpg)\n")
        cs = codex_search()
        assert cs.search_files() == 1

    def test_config_only_applies_to_the_next_image(self, tmp_cwd, codex_search):
        write(
            tmp_cwd / "README.md",
            """
            <!-- RICH-CODEX terminal_width: 60 -->
            ![`echo one`](img/one.svg)
            ![`echo two`](img/two.svg)
            """,
        )
        cs = codex_search()
        cs.search_files()
        assert cs.rich_imgs[0].terminal_width == 60
        assert cs.rich_imgs[1].terminal_width is None

    def test_class_config_applies_to_every_image(self, tmp_cwd, codex_search):
        write(tmp_cwd / "README.md", "![`echo one`](img/one.svg)\n![`echo two`](img/two.svg)\n")
        cs = codex_search(terminal_width=101)
        cs.search_files()
        assert [img.terminal_width for img in cs.rich_imgs] == [101, 101]

    def test_working_dir_defaults_to_the_source_directory(self, tmp_cwd, codex_search):
        write(tmp_cwd / "docs" / "page.md", "![`echo hi`](hi.svg)\n")
        cs = codex_search()
        cs.search_files()
        assert cs.rich_imgs[0].working_dir == tmp_cwd / "docs"
        assert cs.rich_imgs[0].img_paths == [str(tmp_cwd / "docs" / "hi.svg")]

    def test_search_include_pattern(self, tmp_cwd, codex_search):
        write(tmp_cwd / "docs" / "page.md", "![`echo docs`](a.svg)\n")
        write(tmp_cwd / "other" / "page.md", "![`echo other`](b.svg)\n")
        cs = codex_search(search_include="docs/**/*.md")
        cs.search_files()
        assert [img.command for img in cs.rich_imgs] == ["echo docs"]

    def test_search_exclude_pattern(self, tmp_cwd, codex_search):
        write(tmp_cwd / "keep.md", "![`echo keep`](a.svg)\n")
        write(tmp_cwd / "skip.md", "![`echo skip`](b.svg)\n")
        cs = codex_search(search_exclude="skip.md")
        cs.search_files()
        assert [img.command for img in cs.rich_imgs] == ["echo keep"]

    def test_directory_exclude_pattern_gets_a_glob_suffix(self, tmp_cwd, codex_search):
        write(tmp_cwd / "build" / "page.md", "![`echo built`](a.svg)\n")
        write(tmp_cwd / "keep.md", "![`echo keep`](b.svg)\n")
        cs = codex_search(search_exclude="build/")
        cs.search_files()
        assert [img.command for img in cs.rich_imgs] == ["echo keep"]

    def test_invalid_exclude_pattern_is_ignored(self, tmp_cwd, codex_search):
        write(tmp_cwd / "keep.md", "![`echo keep`](a.svg)\n")
        cs = codex_search(search_exclude="/absolute/pattern")
        cs.search_files()
        assert len(cs.rich_imgs) == 1

    def test_counts_are_logged(self, tmp_cwd, codex_search, caplog):
        write(
            tmp_cwd / "README.md",
            """
            ![`echo one`](img/one.svg)
            <!-- RICH-CODEX snippet: 'hi' -->
            ![](img/two.svg)
            """,
        )
        cs = codex_search()
        cs.search_files()
        assert "Found 1 commands" in caplog.text
        assert "Found 1 snippets" in caplog.text


class TestParseConfigs:
    """Tests for parse_configs() and parse_config()."""

    def test_no_config_files(self, tmp_cwd, codex_search):
        cs = codex_search()
        cs.parse_configs()
        assert cs.rich_imgs == []

    def test_reads_a_default_config_path(self, tmp_cwd, codex_search):
        write(
            tmp_cwd / ".rich-codex.yml",
            """
            outputs:
              - command: echo hello
                img_paths:
                  - img/hello.svg
            """,
        )
        cs = codex_search()
        cs.parse_configs()
        assert len(cs.rich_imgs) == 1
        assert cs.rich_imgs[0].command == "echo hello"
        assert cs.rich_imgs[0].source_type == "config"
        assert cs.rich_imgs[0].img_paths == [str(tmp_cwd / "img" / "hello.svg")]

    def test_reads_a_custom_config_path(self, tmp_cwd, codex_search):
        write(
            tmp_cwd / "custom.yml",
            """
            outputs:
              - snippet: hello
                img_paths: [img/hello.svg]
            """,
        )
        cs = codex_search(configs="custom.yml")
        cs.parse_configs()
        assert len(cs.rich_imgs) == 1

    def test_empty_config_file_is_valid(self, tmp_cwd, codex_search):
        write(tmp_cwd / ".rich-codex.yml", "")
        cs = codex_search()
        cs.parse_configs()
        assert cs.rich_imgs == []

    def test_global_only_config(self, tmp_cwd, codex_search, caplog):
        write(tmp_cwd / ".rich-codex.yml", "terminal_width: 123\n")
        cs = codex_search()
        cs.parse_configs()
        assert cs.terminal_width == 123
        assert "using it for global config only" in caplog.text

    def test_config_overrides_class_attrs(self, tmp_cwd, codex_search):
        write(tmp_cwd / ".rich-codex.yml", "terminal_width: 123\n")
        cs = codex_search(terminal_width=80)
        cs.parse_configs()
        assert cs.terminal_width == 123

    def test_config_extra_env_is_merged_with_class_attrs(self, tmp_cwd, codex_search):
        write(tmp_cwd / ".rich-codex.yml", "extra_env:\n  FROM_CONFIG: yes\n")
        cs = codex_search(extra_env={"FROM_CLI": "1"})
        cs.parse_configs()
        assert cs.extra_env == {"FROM_CLI": "1", "FROM_CONFIG": True}

    def test_skip_change_regex_is_a_string(self, tmp_cwd, codex_search):
        """The schema used to declare this as a boolean, which rejected every real pattern."""
        write(
            tmp_cwd / ".rich-codex.yml",
            """
            skip_change_regex: '#[0-9a-f]{6}'
            outputs:
              - command: echo hello
                img_paths: [img/hello.svg]
                skip_change_regex: 'generated:'
            """,
        )
        cs = codex_search()
        cs.parse_configs()
        assert cs.skip_change_regex == "#[0-9a-f]{6}"
        assert cs.rich_imgs[0].skip_change_regex == "generated:"

    def test_global_config_applies_to_outputs(self, tmp_cwd, codex_search):
        write(
            tmp_cwd / ".rich-codex.yml",
            """
            terminal_width: 123
            outputs:
              - command: echo hello
                img_paths: [img/hello.svg]
              - command: echo bye
                img_paths: [img/bye.svg]
                terminal_width: 60
            """,
        )
        cs = codex_search()
        cs.parse_configs()
        assert [img.terminal_width for img in cs.rich_imgs] == [123, 60]

    def test_invalid_config_raises(self, tmp_cwd, codex_search):
        write(tmp_cwd / ".rich-codex.yml", "not_a_real_option: true\n")
        cs = codex_search()
        with pytest.raises(ValidationError):
            cs.parse_configs()

    def test_output_without_img_paths_raises(self, tmp_cwd, codex_search):
        write(tmp_cwd / ".rich-codex.yml", "outputs:\n  - command: echo hello\n")
        cs = codex_search()
        with pytest.raises(ValidationError):
            cs.parse_configs()

    def test_multiple_config_files(self, tmp_cwd, codex_search, caplog):
        write(tmp_cwd / ".rich-codex.yml", "outputs: [{command: echo a, img_paths: [a.svg]}]\n")
        write(tmp_cwd / ".github" / "rich-codex.yml", "outputs: [{command: echo b, img_paths: [b.svg]}]\n")
        cs = codex_search()
        cs.parse_configs()
        assert len(cs.rich_imgs) == 2
        assert "Found 2 config files" in caplog.text

    def test_null_outputs_is_rejected_by_the_schema(self, tmp_cwd, codex_search):
        """'outputs:' with nothing under it is null, which the schema requires to be an array."""
        write(tmp_cwd / ".rich-codex.yml", "outputs:\n")
        cs = codex_search()
        with pytest.raises(ValidationError, match="not of type 'array'"):
            cs.parse_configs()

    def test_empty_outputs_list(self, tmp_cwd, codex_search):
        write(tmp_cwd / ".rich-codex.yml", "outputs: []\n")
        cs = codex_search()
        cs.parse_configs()
        assert cs.rich_imgs == []


class TestCollapseDuplicates:
    """Tests for CodexSearch.collapse_duplicates()."""

    def test_exact_duplicates_are_removed(self, tmp_cwd, codex_search):
        cs = codex_search()
        cs.rich_imgs = [RichImg(command="echo hi", img_paths=["a.svg"]) for _ in range(3)]
        cs.collapse_duplicates()
        assert len(list(cs.rich_imgs)) == 1

    def test_same_command_different_filenames_are_merged(self, tmp_cwd, codex_search):
        cs = codex_search()
        cs.rich_imgs = [
            RichImg(command="echo hi", img_paths=["a.svg"]),
            RichImg(command="echo hi", img_paths=["b.svg"]),
        ]
        cs.collapse_duplicates()
        merged = list(cs.rich_imgs)
        assert len(merged) == 1
        assert merged[0].img_paths == ["a.svg", "b.svg"]

    def test_different_commands_are_kept(self, tmp_cwd, codex_search):
        cs = codex_search()
        cs.rich_imgs = [
            RichImg(command="echo hi", img_paths=["a.svg"]),
            RichImg(command="echo bye", img_paths=["b.svg"]),
        ]
        cs.collapse_duplicates()
        assert len(list(cs.rich_imgs)) == 2

    def test_no_dedupe_keeps_filename_variants_separate(self, tmp_cwd, codex_search):
        cs = codex_search(no_dedupe=True)
        cs.rich_imgs = [
            RichImg(command="echo hi", img_paths=["a.svg"]),
            RichImg(command="echo hi", img_paths=["b.svg"]),
        ]
        cs.collapse_duplicates()
        assert len(cs.rich_imgs) == 2

    def test_no_dedupe_still_removes_exact_duplicates(self, tmp_cwd, codex_search):
        cs = codex_search(no_dedupe=True)
        cs.rich_imgs = [RichImg(command="echo hi", img_paths=["a.svg"]) for _ in range(2)]
        cs.collapse_duplicates()
        assert len(cs.rich_imgs) == 1


class TestPathHelpers:
    """Tests for _relative_path() and _path_link()."""

    def test_relative_path_inside_cwd(self, tmp_cwd, codex_search):
        cs = codex_search()
        assert cs._relative_path(tmp_cwd / "docs" / "img.svg") == "docs/img.svg"

    def test_relative_path_outside_cwd(self, tmp_cwd, codex_search):
        cs = codex_search()
        assert cs._relative_path("/somewhere/else/img.svg") == "/somewhere/else/img.svg"

    def test_path_link_uses_the_relative_path(self, tmp_cwd, codex_search):
        cs = codex_search()
        link = cs._path_link(tmp_cwd / "img.svg")
        assert f"[link=file:{tmp_cwd}/img.svg]" in link
        assert "img.svg[/][/]" in link

    def test_path_link_with_a_custom_label(self, tmp_cwd, codex_search):
        cs = codex_search()
        assert "]my label[/]" in cs._path_link(tmp_cwd / "img.svg", "my label")


class TestConfirmCommands:
    """Tests for CodexSearch.confirm_commands()."""

    def test_no_commands_needs_no_confirmation(self, tmp_cwd, codex_search, monkeypatch):
        monkeypatch.setattr(codex_search_module.Prompt, "ask", lambda *a, **kw: pytest.fail("prompted"))
        cs = codex_search()
        cs.rich_imgs = [RichImg(snippet="hi", img_paths=["a.svg"])]
        cs.confirm_commands()
        assert [img.snippet for img in cs.rich_imgs] == ["hi"]

    def test_no_confirm_skips_the_prompt(self, tmp_cwd, codex_search, monkeypatch):
        monkeypatch.setattr(codex_search_module.Prompt, "ask", lambda *a, **kw: pytest.fail("prompted"))
        cs = codex_search(no_confirm=True)
        cs.rich_imgs = [RichImg(command="echo hi", img_paths=["a.svg"], source="README.md")]
        cs.confirm_commands()
        assert [img.command for img in cs.rich_imgs] == ["echo hi"]

    def test_table_is_printed(self, tmp_cwd, codex_search, console):
        # The codex_search factory already injects this same console
        cs = codex_search(no_confirm=True)
        cs.rich_imgs = [RichImg(command="echo hi", img_paths=["a.svg"], source="README.md", source_line=7)]
        cs.confirm_commands()
        output = console.file.getvalue()
        assert "echo hi" in output
        assert "README.md:7" in output

    def test_answering_all(self, tmp_cwd, codex_search, monkeypatch):
        monkeypatch.setattr(codex_search_module.Prompt, "ask", lambda *a, **kw: "a")
        cs = codex_search(no_confirm=False)
        cs.rich_imgs = [RichImg(command="echo hi", img_paths=["a.svg"], source="README.md")]
        cs.confirm_commands()
        assert len(cs.rich_imgs) == 1

    def test_answering_none_drops_commands(self, tmp_cwd, codex_search, monkeypatch):
        monkeypatch.setattr(codex_search_module.Prompt, "ask", lambda *a, **kw: "n")
        cs = codex_search(no_confirm=False)
        cs.rich_imgs = [
            RichImg(command="echo hi", img_paths=["a.svg"], source="README.md"),
            RichImg(snippet="hi", img_paths=["b.svg"], source="README.md"),
        ]
        cs.confirm_commands()
        assert [img.snippet for img in cs.rich_imgs] == ["hi"]

    def test_answering_some_asks_per_command(self, tmp_cwd, codex_search, monkeypatch):
        monkeypatch.setattr(codex_search_module.Prompt, "ask", lambda *a, **kw: "s")
        answers = iter([True, False])
        monkeypatch.setattr(codex_search_module.rich_img.Confirm, "ask", lambda *a, **kw: next(answers))
        cs = codex_search(no_confirm=False)
        cs.rich_imgs = [
            RichImg(command="echo yes", img_paths=["a.svg"], source="README.md"),
            RichImg(command="echo no", img_paths=["b.svg"], source="README.md"),
        ]
        cs.confirm_commands()
        assert [img.command for img in cs.rich_imgs] == ["echo yes"]


class TestCheckDuplicatePaths:
    """Tests for CodexSearch.check_duplicate_paths()."""

    def test_no_duplicates(self, tmp_cwd, codex_search, caplog):
        cs = codex_search()
        cs.rich_imgs = [
            RichImg(command="echo a", img_paths=["a.svg"], source="README.md"),
            RichImg(command="echo b", img_paths=["b.svg"], source="README.md"),
        ]
        cs.check_duplicate_paths()
        assert "Duplicate output file path" not in caplog.text

    def test_duplicate_paths_warn(self, tmp_cwd, codex_search, caplog):
        cs = codex_search()
        cs.rich_imgs = [
            RichImg(command="echo a", img_paths=["dup.svg"], source="one.md"),
            RichImg(command="echo b", img_paths=["dup.svg"], source="two.md"),
        ]
        cs.check_duplicate_paths()
        assert "Duplicate output file path 'dup.svg'" in caplog.text
        assert "one.md" in caplog.text
        assert "two.md" in caplog.text


class TestSaveAllImages:
    """Tests for CodexSearch.save_all_images()."""

    def test_totals_are_accumulated(self, tmp_cwd, codex_search):
        cs = codex_search()
        cs.rich_imgs = [
            RichImg(snippet="one", snippet_syntax="text", img_paths=[str(tmp_cwd / "one.svg")]),
            RichImg(snippet="two", snippet_syntax="text", img_paths=[str(tmp_cwd / "two.svg")]),
        ]
        cs.save_all_images()
        assert cs.num_img_saved == 2
        assert cs.num_img_skipped == 0
        assert sorted(Path(p).name for p in cs.saved_img_paths) == ["one.svg", "two.svg"]

    def test_skipped_images_are_counted(self, tmp_cwd, codex_search):
        for _ in range(2):
            cs = codex_search()
            cs.rich_imgs = [RichImg(snippet="one", snippet_syntax="text", img_paths=[str(tmp_cwd / "one.svg")])]
            cs.save_all_images()
        assert cs.num_img_saved == 0
        assert cs.num_img_skipped == 1


class TestOutputBlocks:
    """Tests for writing command output into '[!output]' code blocks."""

    @staticmethod
    def run(cs):
        """Run a search through to saving, the same way as the CLI."""
        errors = cs.search_files()
        cs.collapse_duplicates()
        cs.confirm_commands()
        cs.check_duplicate_paths()
        return errors + cs.save_all_images()

    def test_output_is_written_between_the_markers(self, tmp_cwd, codex_search):
        md = write(
            tmp_cwd / "README.md",
            """
            <!-- RICH-CODEX terminal_width: 80 -->
            ```sh
            printf 'one   \\n\\ntwo\\n\\n\\n'
            # [!output]
            old output
            # [!output end]
            ```
            """,
        )
        cs = codex_search()
        assert self.run(cs) == 0
        assert cs.rich_imgs[0].hide_command is True
        assert md.read_text().splitlines()[3:8] == ["# [!output]", "one", "", "two", "# [!output end]"]
        assert cs.num_img_saved == 1
        assert cs.saved_img_paths == [str(md)]

    def test_region_ends_at_the_closing_fence(self, tmp_cwd, codex_search):
        md = tmp_cwd / "README.md"
        write(md, "<!-- RICH-CODEX -->\n~~~~\necho hi\n// [!output lang=ansi]\nold\n~~~\n~~~~\n")
        self.run(codex_search())
        assert md.read_text() == "<!-- RICH-CODEX -->\n~~~~\necho hi\n// [!output lang=ansi]\nhi\n~~~~\n"

    def test_block_without_marker_is_left_alone(self, tmp_cwd, codex_search):
        content = "<!-- RICH-CODEX terminal_width: 60 -->\n```sh\necho hi\n```\n![`echo img`](img.svg)\n"
        md = write(tmp_cwd / "README.md", content)
        cs = codex_search()
        cs.search_files()
        assert md.read_text() == content
        assert [(img.command, img.terminal_width, img.output_blocks) for img in cs.rich_imgs] == [("echo img", 60, [])]

    def test_block_needs_a_config_comment(self, tmp_cwd, codex_search):
        write(tmp_cwd / "README.md", "```sh\necho hi\n# [!output]\n```\n")
        cs = codex_search()
        cs.search_files()
        assert cs.rich_imgs == []

    def test_command_from_config_wins(self, tmp_cwd, codex_search):
        md = tmp_cwd / "README.md"
        write(md, "<!-- RICH-CODEX\ncommand: echo real\n-->\n\n```sh\nmy-tool\n# [!output]\n```\n")
        self.run(codex_search())
        assert md.read_text().splitlines()[-2:] == ["real", "```"]

    def test_multiline_command(self, tmp_cwd, codex_search):
        md = write(tmp_cwd / "README.md", "<!-- RICH-CODEX -->\n```sh\n\n  echo one\n\n  echo two\n# [!output]\n```\n")
        cs = codex_search()
        self.run(cs)
        assert cs.rich_imgs[0].command == "echo one\n\necho two"
        assert md.read_text().splitlines()[-3:] == ["one", "two", "```"]

    def test_command_keeps_its_indentation(self, tmp_cwd, codex_search):
        md = write(
            tmp_cwd / "README.md",
            "<!-- RICH-CODEX -->\n```sh\npython3 - <<EOF\nfor i in range(2):\n    print(i)\nEOF\n# [!output]\n```\n",
        )
        assert self.run(codex_search()) == 0
        assert md.read_text().endswith("# [!output]\n0\n1\n```\n")

    def test_unclosed_block_is_an_error(self, tmp_cwd, codex_search, caplog):
        content = "<!-- RICH-CODEX -->\n````sh\necho hi\n# [!output]\n```\n\n## Important section\n\nText\n"
        md = write(tmp_cwd / "README.md", content)
        cs = codex_search()
        assert cs.search_files() == 1
        assert cs.rich_imgs == []
        assert "No closing '````'" in caplog.text
        assert md.read_text() == content

    def test_output_that_ends_the_block_is_not_written(self, tmp_cwd, codex_search, caplog):
        for output in ["```", "[!output end]"]:
            content = f"<!-- RICH-CODEX -->\n```sh\nprintf 'a\\n{output}\\nb\\n'\n# [!output]\n```\n"
            md = write(tmp_cwd / "README.md", content)
            assert self.run(codex_search()) == 1
            assert md.read_text() == content
        assert "would end the code block" in caplog.text

    def test_literal_escapes_are_doubled(self, tmp_cwd, codex_search):
        md = write(
            tmp_cwd / "README.md", "<!-- RICH-CODEX -->\n```sh\nprintf '%s\\n' 'C:\\e[1] C:\\env'\n# [!output]\n```\n"
        )
        self.run(codex_search())
        assert "# [!output]\nC:\\\\e[1] C:\\env\n```" in md.read_text()

    def test_block_edited_during_the_run_is_an_error(self, tmp_cwd, codex_search, caplog):
        md = write(tmp_cwd / "README.md", "<!-- RICH-CODEX -->\n```sh\necho hi\n# [!output]\n```\n")
        cs = codex_search()
        cs.search_files()
        edited = "# New title\n\n" + md.read_text()
        md.write_text(edited)
        assert cs.save_all_images() == 1
        assert md.read_text() == edited
        assert "changed during the run" in caplog.text

    def test_skip_does_not_leak(self, tmp_cwd, codex_search):
        write(
            tmp_cwd / "README.md",
            "<!-- RICH-CODEX\nskip: true\n-->\n```sh\necho hi\n# [!output]\n![`echo inside`](in.svg)\n```\n"
            "\n![`echo later`](later.svg)\n",
        )
        cs = codex_search()
        cs.search_files()
        assert [img.command for img in cs.rich_imgs] == ["echo later"]

    def test_skip_change_regex_applies(self, tmp_cwd, codex_search):
        content = "<!-- RICH-CODEX\nskip_change_regex: took\n-->\n```sh\necho took 2s\n# [!output]\ntook 1s\n```\n"
        md = write(tmp_cwd / "README.md", content)
        cs = codex_search()
        assert self.run(cs) == 0
        assert md.read_text() == content
        assert (cs.num_img_saved, cs.num_img_skipped) == (0, 1)

    def test_output_to_file(self, tmp_cwd, codex_search):
        content = (
            "<!-- RICH-CODEX\nimg_paths: [out/hi.ansi, out/hi.svg]\n-->\n```sh\nprintf '\\033[33mhi\\033[0m\\n'\n```\n"
        )
        md = write(tmp_cwd / "docs" / "page.md", content)
        assert self.run(codex_search()) == 0
        assert md.read_text() == content
        assert (tmp_cwd / "docs" / "out" / "hi.ansi").read_text() == "\x1b[33mhi\x1b[0m\n"
        assert "hi" in (tmp_cwd / "docs" / "out" / "hi.svg").read_text()
        assert "echo" not in (tmp_cwd / "docs" / "out" / "hi.svg").read_text()

    def test_shell_prompt_is_stripped(self, tmp_cwd, codex_search):
        md = write(tmp_cwd / "README.md", "<!-- RICH-CODEX -->\n```sh\n  $ echo one\n  $ echo two\n# [!output]\n```\n")
        cs = codex_search()
        assert self.run(cs) == 0
        assert cs.rich_imgs[0].command == "echo one\necho two"
        assert md.read_text().endswith("# [!output]\none\ntwo\n```\n")

    @pytest.mark.parametrize(
        ("lang", "code", "command"),
        [
            # Lines without a prompt are output, unless they continue a command
            ("console", ["$ echo a \\\\", "  b", "a b", "> echo c", "c"], "echo a \\\\\n  b\necho c"),
            ("sh", ["$ cat <<EOF", "> hi", "> EOF", "hi"], "cat <<EOF\nhi\nEOF"),
            # No prompts: all of it is the command
            ("sh", ["echo a", "echo b"], "echo a\necho b"),
            # Prompts only count in terminal languages
            ("text", ["$ echo a", "a"], "$ echo a\na"),
        ],
    )
    def test_shell_prompts_match_starlight_codeblocks(self, lang, code, command):
        lines = [f"```{lang} runnable.static\n", *[f"{line}\n" for line in code], "```\n"]
        assert codex_search_module.parse_code_block(lines, 0).command == command

    @pytest.mark.parametrize("attr", ['"out/hi.ansi"', "'out/hi.ansi'", "out/hi.ansi"])
    def test_output_file_from_the_fence(self, tmp_cwd, codex_search, attr):
        content = f"{{/* RICH-CODEX */}}\n```sh runnable.static runnable.outputFile={attr}\n$ echo hi\n```\n"
        md = write(tmp_cwd / "docs" / "page.mdx", content)
        assert self.run(codex_search()) == 0
        assert md.read_text() == content
        assert (tmp_cwd / "docs" / "out" / "hi.ansi").read_text() == "hi\n"

    def test_output_file_adds_to_img_paths(self, tmp_cwd, codex_search):
        write(
            tmp_cwd / "README.md",
            '<!-- RICH-CODEX\nimg_paths: [hi.svg, hi.ansi]\n-->\n```sh runnable.outputFile="hi.ansi"\necho hi\n```\n',
        )
        cs = codex_search()
        cs.search_files()
        assert [Path(p).name for p in cs.rich_imgs[0].img_paths] == ["hi.svg", "hi.ansi"]

    def test_ansi_file_never_has_the_command(self, tmp_cwd, codex_search):
        write(
            tmp_cwd / "README.md",
            "![`echo hi`](hi.svg)\n<!-- RICH-CODEX\nimg_paths: [hi.ansi]\n-->\n![`echo hi`](hi.svg)\n",
        )
        cs = codex_search()
        assert self.run(cs) == 0
        assert "echo" in (tmp_cwd / "hi.svg").read_text()
        assert (tmp_cwd / "hi.ansi").read_text() == "hi\n"

    def test_code_block_inside_an_example_is_not_run(self, tmp_cwd, codex_search):
        """eg. a CONTRIBUTING.md that shows the syntax, with a path that only works from the docs."""
        content = (
            "````mdx\n{/* RICH-CODEX\nworking_dir: examples\n*/}\n"
            '```sh runnable.outputFile="../images/colors.ansi"\n$ python colors.py\n# [!output]\n```\n````\n'
            "\n![`echo later`](later.svg)\n"
        )
        md = write(tmp_cwd / "CONTRIBUTING.md", content)
        cs = codex_search()
        assert self.run(cs) == 0
        assert md.read_text() == content
        assert not (tmp_cwd.parent / "images").exists()
        # The example's config doesn't leak to the next image
        assert [(img.command, img.working_dir) for img in cs.rich_imgs] == [("echo later", tmp_cwd)]

    def test_image_inside_an_example_still_runs(self, tmp_cwd, codex_search):
        """The rich-codex docs show the markup for each example, and it generates the image."""
        write(tmp_cwd / "README.md", "```markdown\n<!-- RICH-CODEX hide_command: true -->\n![`echo hi`](hi.svg)\n```\n")
        cs = codex_search()
        cs.search_files()
        assert [(img.command, img.hide_command) for img in cs.rich_imgs] == [("echo hi", True)]

    def test_config_file_output_needs_img_paths(self, tmp_cwd, codex_search):
        write(tmp_cwd / ".rich-codex.yml", "outputs:\n  - command: echo hi\n    output_blocks: [[README.md, 2]]\n")
        with pytest.raises(ValidationError):
            codex_search(configs=".rich-codex.yml").parse_configs()

    def test_no_command_is_an_error(self, tmp_cwd, codex_search, caplog):
        write(tmp_cwd / "README.md", "<!-- RICH-CODEX -->\n```sh\n# [!output]\n```\n")
        cs = codex_search()
        assert cs.search_files() == 1
        assert cs.rich_imgs == []
        assert "No command for code block" in caplog.text

    def test_several_blocks_in_one_file(self, tmp_cwd, codex_search):
        md = write(
            tmp_cwd / "README.md",
            """
            <!-- RICH-CODEX -->
            ```sh
            seq 1 3
            # [!output]
            ```
            <!-- RICH-CODEX -->
            ```sh
            echo same
            # [!output]
            a
            b
            c
            ```
            <!-- RICH-CODEX -->
            ```sh
            echo same
            # [!output]
            ```
            """,
        )
        cs = codex_search()
        self.run(cs)
        # Identical commands are run once, but written to every block
        assert len(cs.rich_imgs) == 2
        assert cs.num_img_saved == 3
        assert md.read_text().count("# [!output]\nsame\n```") == 2
        assert "# [!output]\n1\n2\n3\n```" in md.read_text()

    def test_mdx_comment(self, tmp_cwd, codex_search):
        md = write(tmp_cwd / "page.mdx", "{/* RICH-CODEX terminal_width: 60 */}\n```sh\necho hi\n# [!output]\n```\n")
        self.run(codex_search())
        assert "# [!output]\nhi\n```" in md.read_text()

    def test_unchanged_file_is_not_rewritten(self, tmp_cwd, codex_search):
        md = write(tmp_cwd / "README.md", "<!-- RICH-CODEX -->\n```sh\necho hi\n# [!output]\nhi\n```\n")
        os.utime(md, (0, 0))
        cs = codex_search()
        self.run(cs)
        assert md.stat().st_mtime == 0
        assert (cs.num_img_saved, cs.num_img_skipped, cs.saved_img_paths) == (0, 1, [])

    def test_colours_are_written_as_escapes(self, tmp_cwd, codex_search):
        md = tmp_cwd / "README.md"
        write(md, "<!-- RICH-CODEX -->\n```sh\nprintf '\\033[33mhi\\033[0m'\n# [!output]\n```\n")
        self.run(codex_search())
        assert "\\e[33mhi\\e[0m" in md.read_text()
        assert "\x1b" not in md.read_text()

    def test_indented_block_keeps_its_indent(self, tmp_cwd, codex_search):
        md = tmp_cwd / "README.md"
        write(md, "1. Run it\n\n   <!-- RICH-CODEX -->\n   ```sh\n   echo hi\n   # [!output]\n   ```\n")
        self.run(codex_search())
        assert md.read_text().endswith("   # [!output]\n   hi\n   ```\n")

    def test_ignored_commands_are_not_written(self, tmp_cwd, codex_search):
        content = "<!-- RICH-CODEX -->\n```sh\necho hi\nrm -f nothing\n# [!output]\n```\n"
        md = write(tmp_cwd / "README.md", content)
        assert self.run(codex_search()) == 1
        assert md.read_text() == content

    def test_output_is_not_searched(self, tmp_cwd, codex_search):
        write(tmp_cwd / "README.md", "<!-- RICH-CODEX -->\n```md\necho hi\n# [!output]\n![`echo no`](no.svg)\n```\n")
        cs = codex_search()
        cs.search_files()
        assert [img.command for img in cs.rich_imgs] == ["echo hi"]

    def test_confirm_table_shows_the_block(self, tmp_cwd, codex_search, console):
        write(tmp_cwd / "README.md", "# Title\n<!-- RICH-CODEX -->\n```sh\necho hi\n# [!output]\n```\n")
        cs = codex_search()
        cs.search_files()
        cs.confirm_commands()
        assert "README.md:3" in console.file.getvalue()


def test_multiline_snippet_keeps_its_final_newline(tmp_cwd, codex_search):
    write(tmp_cwd / "README.md", "<!-- RICH-CODEX\nsnippet: |\n  hello\n-->\n![](out.svg)\n")
    cs = codex_search()
    cs.search_files()
    assert cs.rich_imgs[0].snippet == "hello\n"


def test_config_comment_styles_are_paired():
    """Each supported comment opener needs a non-empty closer that differs from it."""
    for opener, closer in codex_search_module.CONFIG_COMMENT_STYLES.items():
        assert opener and closer
        assert opener != closer


def test_packaged_schema_is_a_mapping():
    """The schema shipped with the package must parse into a usable dict."""
    assert isinstance(codex_search_module.CONFIG_SCHEMA, dict)
    assert "outputs" in codex_search_module.CONFIG_SCHEMA["properties"]
