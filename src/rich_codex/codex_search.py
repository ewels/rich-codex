import logging
import re
from pathlib import Path
from typing import Any

import yaml
from jsonschema.exceptions import ValidationError
from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from rich_codex import rich_img
from rich_codex.utils import clean_list, relative_path, validate_config

log = logging.getLogger("rich-codex")

# Config comment styles: HTML comments for markdown, JSX comments for MDX
# (MDX v2+ does not allow HTML comments)
# eg. <!-- RICH-CODEX terminal_width: 60 -->
# eg. {/* RICH-CODEX terminal_width: 60 */}
CONFIG_COMMENT_STYLES = {"<!--": "-->", "{/*": "*/}"}

# Parse the config schema file once, it's the same for every search
config_schema_fn = Path(__file__).parent / "config-schema.yml"
with config_schema_fn.open() as fh:
    CONFIG_SCHEMA = yaml.safe_load(fh)


class CodexSearch:
    """File search class for rich-codex.

    Looks through a set of source files for sets of configuration
    needed to generate screenshots.
    """

    def __init__(
        self,
        search_include: str | None,
        search_exclude: str | None,
        configs: str | None,
        no_confirm: bool,
        no_dedupe: bool,
        extra_env: dict[str, str] | None,
        snippet_syntax: str | None,
        timeout: int,
        working_dir: str | None,
        before_command: str | None,
        after_command: str | None,
        hide_command: bool,
        title_command: bool,
        head: int | None,
        tail: int | None,
        trim_after: str | None,
        truncated_text: str | None,
        min_pct_diff: float,
        skip_change_regex: str | None,
        terminal_width: int | None,
        terminal_min_width: int | None,
        notrim: bool,
        terminal_theme: str | None,
        snippet_theme: str | None,
        use_pty: bool,
        console: Console | None,
    ) -> None:
        """Initialize the search object."""
        if search_include is None:
            self.search_include = ["**/*.md", "**/*.mdx"]
        else:
            self.search_include = clean_list(search_include.splitlines())
        self.search_exclude = ["**/.git*", "**/.git*/**", "**/node_modules/**"]
        if search_exclude is not None:
            self.search_exclude.extend(clean_list(search_exclude.splitlines()))
        self.configs = [
            ".rich-codex.yml",
            ".rich-codex.yaml",
            ".github/rich-codex.yml",
            ".github/rich-codex.yaml",
            "docs/img/rich-codex.yml",
            "docs/img/rich-codex.yaml",
        ]
        if configs is not None:
            self.configs.extend(clean_list(configs.splitlines()))
        self.no_confirm = no_confirm
        self.no_dedupe = no_dedupe
        self.extra_env = extra_env
        self.snippet_syntax = snippet_syntax
        self.timeout = timeout
        self.working_dir = working_dir
        self.before_command = before_command
        self.after_command = after_command
        self.hide_command = hide_command
        self.title_command = title_command
        self.head = head
        self.tail = tail
        self.trim_after = trim_after
        self.truncated_text = truncated_text
        self.min_pct_diff = min_pct_diff
        self.skip_change_regex = skip_change_regex
        self.terminal_width = terminal_width
        self.terminal_min_width = terminal_min_width
        self.notrim = notrim
        self.terminal_theme = terminal_theme
        self.snippet_theme = snippet_theme
        self.use_pty = use_pty
        self.console = Console() if console is None else console
        self.cwd = Path.cwd().resolve()
        self.rich_imgs: list[rich_img.RichImg] = []
        self.saved_img_paths: list[str] = []
        self.num_img_saved = 0
        self.num_img_skipped = 0
        self.class_config_attrs = [
            "extra_env",
            "snippet_syntax",
            "timeout",
            "working_dir",
            "before_command",
            "after_command",
            "hide_command",
            "title_command",
            "head",
            "tail",
            "trim_after",
            "truncated_text",
            "min_pct_diff",
            "skip_change_regex",
            "terminal_width",
            "terminal_min_width",
            "notrim",
            "terminal_theme",
            "snippet_theme",
            "use_pty",
        ]
        # Config options that combine with more specific config, instead of being replaced by it
        self.merged_config_attrs = ["extra_env"]

        # Look in .gitignore to add to search_exclude
        try:
            with open(".gitignore") as fh:
                log.debug("Appending contents of .gitignore to 'SEARCH_EXCLUDE'")
                self.search_exclude.extend(clean_list(fh.readlines()))
        except OSError:
            pass

        self.config_schema = CONFIG_SCHEMA

    def _merge_local_class_attrs(self, local_config: dict[str, Any]) -> dict[str, Any]:
        """Update local config with class params.

        Only if not set locally and if not None at class level.
        """
        for conf in self.class_config_attrs:
            if getattr(self, conf) is None:
                continue
            # Global config applies to every image, but local keys win
            if conf in self.merged_config_attrs:
                local_config[conf] = self._merge_config_values(getattr(self, conf), local_config.get(conf))
            elif conf not in local_config:
                local_config[conf] = getattr(self, conf)
        return local_config

    @staticmethod
    def _merge_config_values(base: dict[str, Any] | None, override: dict[str, Any] | None) -> dict[str, Any]:
        """Combine two dicts of config values, with keys in 'override' winning."""
        return {**(base or {}), **(override or {})}

    def search_files(self) -> int:
        """Search through a set of files for codex strings."""
        matched_files: set[Path] = set()
        for pattern in self.search_include:
            for search_file in Path.cwd().glob(pattern):
                matched_files.add(search_file.resolve())
        for pattern in self.search_exclude:
            if pattern.endswith("/"):
                pattern += "**/*"
            try:
                for exclude_file in Path.cwd().glob(pattern):
                    matched_files.discard(exclude_file.resolve())
            except (ValueError, NotImplementedError):
                pass
        files_to_search = sorted(matched_files, key=lambda x: str(x).lower())
        if len(files_to_search) == 0:
            log.debug("No files found to search")
        else:
            log.info(f"Searching {len(files_to_search)} files")

        # eg. <!-- RICH-CODEX TERMINAL_WIDTH=60 -->
        # eg. <!-- RICH-CODEX
        # eg. {/* RICH-CODEX TERMINAL_WIDTH=60 */}  (MDX files can't use HTML comments)
        comment_starts = "|".join(re.escape(start) for start in CONFIG_COMMENT_STYLES)
        config_comment_re = re.compile(rf"\s*(?P<comment_start>{comment_starts})\s*RICH-CODEX\s*(?P<config_str>.*)")

        # eg. ![`rich --help`](rich-cli-help.svg)
        img_cmd_re = re.compile(r"\s*!\[`(?P<cmd>[^`]+)`\]\((?P<img_path>.*?)(?=\"|\))(?P<title>[\"'].*[\"'])?\)")

        # eg. ![custom text](img/example.svg)
        # eg. ![](img/example-named.svg)
        img_snippet_re = re.compile(r"\s*!\[.*\]\((?P<img_path>.*?)(?=\"|\))(?P<title>[\"'].*[\"'])?\)")
        local_config: dict[str, Any] = {}
        num_errors = 0
        num_commands = 0
        num_snippets = 0
        for file in files_to_search:
            file_rel_fn = file.relative_to(self.cwd)
            log.debug(f"Searching: [magenta]{file_rel_fn}[/]")
            with open(file) as fh:
                line_number = 0
                in_config = False
                comment_end: str | None = None
                local_config_str = ""
                for line in fh:
                    line_number += 1

                    # Keep saving config if we're in a config block
                    if in_config:
                        local_config_str += line
                        if comment_end is not None and comment_end in line:
                            in_config = False
                            local_config_str = local_config_str.split(comment_end)[0]
                            continue

                    # Parse +  validate config yaml
                    if local_config_str != "" and not in_config:
                        try:
                            local_config = yaml.safe_load(local_config_str)
                            if not isinstance(local_config, dict):
                                raise ValueError("config YAML is not a dictionary")
                        except (yaml.YAMLError, ValueError) as e:
                            log.error(f"[red][✗] Error parsing config YAML in '{file_rel_fn}' line {line_number}: {e}")
                            log.debug(f"Config block:\n{local_config_str}")
                            local_config = {}
                            num_errors += 1
                        local_config_str = ""

                    # Look for images
                    # Both patterns capture 'img_path' and 'title'; only the command one has 'cmd'
                    img_cmd_match = img_cmd_re.match(line)
                    img_match = img_cmd_match or img_snippet_re.match(line)
                    if img_match and not local_config.get("skip"):
                        # Logging string of original local config
                        local_config_logmsg = f" with config: {local_config}" if len(local_config) > 0 else ""

                        m = img_match.groupdict()

                        # Get the command and title from a command regex match
                        if img_cmd_match:
                            local_config["command"] = m["cmd"]
                            # Save the title if set
                            if m["title"]:
                                local_config["title"] = m["title"].strip("'\" ")

                        # Counters for commands / snippets
                        if "command" in local_config:
                            num_commands += 1
                            img_type = "[blue]command[/]"
                        elif local_config.get("snippet", "") != "":
                            num_snippets += 1
                            img_type = "[red]snippet[/]"
                        # Just a regular image with no command / snippet - carry on
                        else:
                            log.debug(f"[dim]Skipped markdown image, line {line_number}: {m}")
                            if len(local_config) > 0:
                                log.warning(f"Skipped image but local_config was not empty: {local_config}")
                            local_config = {}
                            local_config_str = ""
                            continue

                        # Set the image path (append in case any others were in the config)
                        img_path = Path(file).parent / Path(m["img_path"].strip())
                        local_config["img_paths"] = local_config.get("img_paths", []) + [str(img_path.resolve())]

                        # Set other config defaults if not supplied
                        local_config["working_dir"] = local_config.get("working_dir", str(Path(file).parent))
                        local_config["source_type"] = local_config.get("source_type", "search")
                        local_config["source"] = local_config.get("source", str(file))
                        local_config["source_line"] = line_number

                        local_config = self._merge_local_class_attrs(local_config)

                        # Validate the config we have via the schema
                        try:
                            validate_config(self.config_schema, {"outputs": [local_config]}, file_rel_fn, line_number)
                        except ValidationError as e:
                            log.error(e)
                            local_config_str = ""
                            local_config = {}
                            num_errors += 1
                            continue

                        quote = "'" if local_config.get("command") else ""
                        log.debug(
                            f"Found markdown {img_type}, line {line_number}: "
                            f"{quote}{local_config.get('command', '')}{quote}{local_config_logmsg}"
                        )
                        img_obj = rich_img.RichImg(**local_config)

                        # Save the image object
                        self.rich_imgs.append(img_obj)

                        # Clear local config
                        local_config = {}
                        local_config_str = ""

                        continue

                    # Look for a local config
                    config_match = config_comment_re.match(line)
                    if config_match:
                        m = config_match.groupdict()
                        comment_end = CONFIG_COMMENT_STYLES[m["comment_start"]]

                        # If we don't end the comment on this line, must be a snippet
                        if comment_end not in line:
                            in_config = True

                        # Save config
                        local_config_str = m.get("config_str", "").split(comment_end)[0] + "\n"

        if num_commands > 0:
            log.info(f"Search: Found {num_commands} commands")
        if num_snippets > 0:
            log.info(f"Search: Found {num_snippets} snippets")
        return num_errors

    def parse_configs(self) -> None:
        """Loop through rich-codex config files to send for parsing."""
        configs: list[Path] = []
        for config_fn in self.configs:
            config = Path(config_fn)
            if config.exists():
                log.debug(f"Found config '{config_fn}'")
                configs.append(config)
            else:
                log.debug(f"[dim]Couldn't find '{config_fn}'")

        if len(configs) > 0:
            log.info(f"Found {len(configs)} config file{'s' if len(configs) > 1 else ''}")
        for config in configs:
            with config.open() as fh:
                # An empty config file is valid, it just doesn't configure anything
                self.parse_config(config, yaml.safe_load(fh) or {})

    def parse_config(self, config_fn: Path, config: dict[str, Any]) -> None:
        """Parse a single rich-codex config file."""
        validate_config(self.config_schema, config, config_fn)

        # Overwrite class-level configs
        for cls in self.class_config_attrs:
            if cls in config:
                # Merged options are added to anything already set, rather than replacing it
                if cls in self.merged_config_attrs:
                    setattr(self, cls, self._merge_config_values(getattr(self, cls), config[cls]))
                else:
                    setattr(self, cls, config[cls])

        # 'outputs' is optional - a config file can just set global defaults
        if "outputs" not in config:
            log.debug(f"No 'outputs' found in '{config_fn}', using it for global config only")

        for output in config.get("outputs") or []:
            log.debug(f"Found valid output in '{config_fn}': {output}")
            output["img_paths"] = [str(Path(img_path_str.strip()).resolve()) for img_path_str in output["img_paths"]]
            output["source_type"] = "config"
            output["source"] = config_fn
            local_config = self._merge_local_class_attrs(output)
            self.rich_imgs.append(rich_img.RichImg(**local_config))

    def collapse_duplicates(self) -> None:
        """Collapse duplicate commands."""
        # Remove exact duplicates - identical requests would only overwrite one another
        dedup_imgs = list(dict.fromkeys(self.rich_imgs))

        # Commands run in series can give different output each time, so merging can be disabled
        if self.no_dedupe:
            log.debug(f"Running all {len(dedup_imgs)} image requests separately, as deduplication is disabled")
            self.rich_imgs = dedup_imgs
            return

        # Merge dups that are the same except for output filename
        merged_imgs: dict[int, rich_img.RichImg] = {}
        for ri in dedup_imgs:
            ri_hash = ri._hash_no_fn()
            if ri_hash in merged_imgs:
                merged_imgs[ri_hash].img_paths.extend(ri.img_paths)
            else:
                merged_imgs[ri_hash] = ri
        log.debug(f"Collapsing {len(self.rich_imgs)} image requests to {len(merged_imgs)} deduplicated")
        self.rich_imgs = list(merged_imgs.values())

    def _relative_path(self, path: str | Path | None) -> str:
        """Path relative to the working directory, if it's inside it."""
        return relative_path(path, self.cwd)

    def _path_link(self, path: str | Path | None, label: str | None = None) -> str:
        """Rich markup for a file path, hyperlinked to the file itself."""
        text = label or self._relative_path(path)
        if path is None:
            return text
        return f"[grey42][link=file:{Path(path).resolve()}]{text}[/][/]"

    def confirm_commands(self) -> bool | None:
        """Prompt the user to confirm running the commands."""
        table = Table(
            title_style="blue",
            title_justify="left",
            box=box.ROUNDED,
            safe_box=True,
            header_style="bold blue",
            border_style="blue",
            row_styles=["green on grey3", "magenta on grey15"],
        )
        table.add_column("Commands to run:")
        table.add_column("Output")
        table.add_column("Source")
        for img_obj in self.rich_imgs:
            if img_obj.command is not None:
                rel_source = self._relative_path(img_obj.source)
                if img_obj.source_line:
                    rel_source = f"{rel_source}:{img_obj.source_line}"
                outputs = "\n".join(self._path_link(p) for p in img_obj.img_paths)
                table.add_row(img_obj.command, outputs, self._path_link(img_obj.source, rel_source))

        if table.row_count == 0:
            return True

        self.console.print(table)

        if self.no_confirm:
            return True

        confirm = Prompt.ask(
            "Do you want to run these commands? (All / Some / None)", choices=["a", "s", "n"], console=self.console
        )
        if confirm == "a":
            log.info("Running all commands")
            return True
        elif confirm == "n":
            log.info("Skipping all outputs that require running a command")
            self.rich_imgs = [ri for ri in self.rich_imgs if ri.command is None]
            return False
        else:
            log.info("Please select commands individually")
            self.rich_imgs = [ri for ri in self.rich_imgs if ri.confirm_command()]
            return None

    def check_duplicate_paths(self) -> None:
        """Check that we don't have any duplicate output file paths."""
        img_paths_src: dict[str, list[Path]] = {}
        for ri in self.rich_imgs:
            if ri.source is None:
                continue
            for img_path in ri.img_paths:
                img_paths_src.setdefault(img_path, []).append(ri.source)
        for img_path, src in img_paths_src.items():
            if len(src) > 1:
                img_path_rel = self._relative_path(img_path)
                src_paths = "', '".join({self._relative_path(s) for s in src})
                log.warning(f"Duplicate output file path '{img_path_rel}' found in '{src_paths}'")

    def save_all_images(self) -> None:
        """Save the images that we have collected."""
        for img_obj in self.rich_imgs:
            img_obj.get_output()
            img_obj.save_images()
            self.saved_img_paths += img_obj.saved_img_paths
            self.num_img_saved += img_obj.num_img_saved
            self.num_img_skipped += img_obj.num_img_skipped
