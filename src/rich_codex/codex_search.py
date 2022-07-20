import logging
import re
from pathlib import Path

import yaml
from jsonschema.exceptions import ValidationError
from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from rich_codex import rich_img
from rich_codex.utils import validate_config

log = logging.getLogger("rich-codex")


class CodexSearch:
    """File search class for rich-codex.

    Looks through a set of source files for sets of configuration
    needed to generate screenshots.
    """

    def __init__(
        self,
        search_include,
        search_exclude,
        configs,
        no_confirm,
        snippet_syntax,
        timeout,
        before_command,
        after_command,
        hide_command,
        title_command,
        head,
        tail,
        trim_after,
        truncated_text,
        min_pct_diff,
        skip_change_regex,
        terminal_width,
        terminal_min_width,
        notrim,
        terminal_theme,
        snippet_theme,
        use_pty,
        console,
    ):
        """Initialize the search object."""
        self.search_include = ["**/*.md"] if search_include is None else self._clean_list(search_include.splitlines())
        self.search_exclude = ["**/.git*", "**/.git*/**", "**/node_modules/**"]
        if search_exclude is not None:
            self.search_exclude.extend(self._clean_list(search_exclude.splitlines()))
        self.configs = [".rich-codex.yml", ".github/rich-codex.yml", "docs/img/rich-codex.yml"]
        if configs is not None:
            self.configs.extend(self._clean_list(configs.splitlines()))
        self.no_confirm = no_confirm
        self.snippet_syntax = snippet_syntax
        self.timeout = timeout
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
        self.rich_imgs = []
        self.saved_img_paths = []
        self.num_img_saved = 0
        self.num_img_skipped = 0
        self.class_config_attrs = [
            "snippet_syntax",
            "timeout",
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

        # Look in .gitignore to add to search_exclude
        try:
            with open(".gitignore", "r") as fh:
                log.debug("Appending contents of .gitignore to 'SEARCH_EXCLUDE'")
                self.search_exclude.extend(self._clean_list(fh.readlines()))
        except IOError:
            pass

        # Parse the config schema file
        config_schema_fn = Path(__file__).parent / "config-schema.yml"
        with config_schema_fn.open() as fh:
            self.config_schema = yaml.safe_load(fh)

    def _clean_list(self, unclean_lines):
        """Remove empty strings from a list."""
        clean_lines = []
        for line in unclean_lines:
            line = line.strip()
            if not line.startswith("#") and line:
                clean_lines.append(line)
        return clean_lines

    def _merge_local_class_attrs(self, local_config):
        """Update local config with class params.
        Only if not set locally and if not None at class level
        """
        for conf in self.class_config_attrs:
            if conf not in local_config and getattr(self, conf) is not None:
                local_config[conf] = getattr(self, conf)
        return local_config

    def search_files(self):
        """Search through a set of files for codex strings."""
        search_files = set()
        for pattern in self.search_include:
            for search_file in Path.cwd().glob(pattern):
                search_files.add(search_file.resolve())
        for pattern in self.search_exclude:
            if pattern.endswith("/"):
                pattern += "**/*"
            try:
                for exclude_file in Path.cwd().glob(pattern):
                    search_files.discard(exclude_file.resolve())
            except (ValueError, NotImplementedError):
                pass
        if len(search_files) == 0:
            log.debug("No files found to search")
        else:
            log.info(f"Searching {len(search_files)} files")

        # eg. <!-- RICH-CODEX TERMINAL_WIDTH=60 -->
        # eg. <!-- RICH-CODEX
        config_comment_re = re.compile(r"\s*<!\-\-\s*RICH-CODEX\s*(?P<config_str>.*)")

        # eg. ![`rich --help`](rich-cli-help.svg)
        img_cmd_re = re.compile(r"\s*!\[`(?P<cmd>[^`]+)`\]\((?P<img_path>.*?)(?=\"|\))(?P<title>[\"'].*[\"'])?\)")

        # eg. ![custom text](img/example.svg)
        # eg. ![](img/example-named.svg)
        img_snippet_re = re.compile(r"\s*!\[.*\]\((?P<img_path>.*?)(?=\"|\))(?P<title>[\"'].*[\"'])?\)")
        local_config = {}
        num_errors = 0
        num_commands = 0
        num_snippets = 0
        for file in search_files:
            file_rel_fn = Path(file).relative_to(Path.cwd())
            log.debug(f"Searching: [magenta]{file_rel_fn}[/]")
            with open(file, "r") as fh:
                line_number = 0
                in_config = False
                local_config_str = ""
                for line in fh:
                    line_number += 1

                    # Keep saving config if we're in a config block
                    if in_config:
                        local_config_str += line
                        if "-->" in line:
                            in_config = False
                            local_config_str = local_config_str.split("-->")[0]
                            continue

                    # Parse +  validate config yaml
                    if local_config_str != "" and not in_config:
                        try:
                            local_config = yaml.safe_load(local_config_str)
                            if not isinstance(local_config, dict):
                                raise ValidationError(
                                    f"Config YAML is not a dictionary: '{file_rel_fn}', line {line_number}"
                                )
                        except yaml.YAMLError as e:
                            log.error(f"[red][✗] Error parsing config YAML in '{file_rel_fn}' line {line_number}: {e}")
                            log.debug(f"Config block:\n{local_config_str}")
                            local_config = {}
                            num_errors += 1
                        local_config_str = ""

                    # Look for images
                    img_cmd_match = img_cmd_re.match(line)
                    img_match = img_snippet_re.match(line)
                    if (img_cmd_match or img_match) and not local_config.get("skip"):

                        # Logging string of original local config
                        local_config_logmsg = f" with config: {local_config}" if len(local_config) > 0 else ""

                        # Get the command and title from a command regex match
                        if img_cmd_match:
                            m = img_cmd_match.groupdict()
                            local_config["command"] = m["cmd"]
                            # Save the title if set
                            if m["title"]:
                                local_config["title"] = m["title"].strip("'\" ")
                        else:
                            m = img_match.groupdict()

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
                                log.warn(f"Skipped image but local_config was not empty: {local_config}")
                            local_config = {}
                            local_config_str = ""
                            continue

                        # Set the image path (append in case any others were in the config)
                        img_path = Path(file).parent / Path(m["img_path"].strip())
                        local_config["img_paths"] = local_config.get("img_paths", []) + [str(img_path.resolve())]

                        # Set other config defaults if not supplied
                        local_config["working_dir"] = (
                            Path(local_config["working_dir"]) if "working_dir" in local_config else Path(file).parent
                        )
                        local_config["source_type"] = local_config.get("source_type", "search")
                        local_config["source"] = Path(local_config["source"]) if "source" in local_config else file

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

                        log.debug(
                            "Found markdown {0}, line {1}: {3}{2}{3}{4}".format(
                                img_type,
                                line_number,
                                local_config.get("command", ""),
                                "'" if local_config.get("command") else "",
                                local_config_logmsg,
                            )
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

                        # If we don't end the comment on this line, must be a snippet
                        if "-->" not in line:
                            in_config = True

                        # Save config
                        local_config_str = m.get("config_str", "").split("-->")[0] + "\n"

        if num_commands > 0:
            log.info(f"Search: Found {num_commands} commands")
        if num_snippets > 0:
            log.info(f"Search: Found {num_snippets} snippets")
        return num_errors

    def parse_configs(self):
        """Loop through rich-codex config files to send for parsing."""
        configs = []
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
                self.parse_config(config_fn, yaml.safe_load(fh))

    def parse_config(self, config_fn, config):
        """Parse a single rich-codex config file."""
        validate_config(self.config_schema, config, config_fn)

        # Overwrite class-level configs
        for cls in self.class_config_attrs:
            if cls in config:
                setattr(self, cls, config["cls"])

        for output in config["outputs"]:
            log.debug(f"Found valid output in '{config_fn}': {output}")
            output["img_paths"] = [str(Path(img_path_str.strip()).resolve()) for img_path_str in output["img_paths"]]
            output["source_type"] = "config"
            output["source"] = config_fn
            local_config = self._merge_local_class_attrs(output)
            self.rich_imgs.append(rich_img.RichImg(**local_config))

    def collapse_duplicates(self):
        """Collapse duplicate commands."""
        # Remove exact duplicates
        dedup_imgs = set(self.rich_imgs)
        # Merge dups that are the same except for output filename
        merged_imgs = {}
        for ri in dedup_imgs:
            ri_hash = ri._hash_no_fn()
            if ri_hash in merged_imgs:
                merged_imgs[ri_hash].img_paths.extend(ri.img_paths)
            else:
                merged_imgs[ri_hash] = ri
        log.debug(f"Collapsing {len(self.rich_imgs)} image requests to {len(merged_imgs)} deduplicated")
        self.rich_imgs = sorted(merged_imgs.values(), key=lambda x: str(x.command).lower())

    def confirm_commands(self):
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
        table.add_column("Source", justify="right")
        for img_obj in self.rich_imgs:
            if img_obj.command is not None:
                rel_source = Path(img_obj.source).relative_to(Path.cwd())
                source = f" [grey42][link=file:{Path(img_obj.source).absolute()}]{rel_source}[/][/]"
                table.add_row(img_obj.command, source)

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

    def save_all_images(self):
        """Save the images that we have collected."""
        for img_obj in self.rich_imgs:
            img_obj.get_output()
            img_obj.save_images()
            self.saved_img_paths += img_obj.saved_img_paths
            self.num_img_saved += img_obj.num_img_saved
            self.num_img_skipped += img_obj.num_img_skipped
