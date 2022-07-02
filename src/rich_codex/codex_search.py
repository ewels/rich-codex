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
        hide_command,
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
        self.hide_command = hide_command
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
        self.use_pty = use_pty
        self.console = Console() if console is None else console
        self.rich_imgs = []
        self.num_img_saved = 0
        self.num_img_skipped = 0

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
            log.error("No files found to search")
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
                            # Fake a full config file with the local config
                            full_config = {
                                "outputs": [
                                    {"img_paths": ["parsed_later.svg"], "command": "parsed_later", **local_config}
                                ]
                            }
                            validate_config(self.config_schema, full_config, file_rel_fn, line_number)
                        except yaml.YAMLError as e:
                            log.error(f"[red][✗] Error parsing config YAML in '{file_rel_fn}' line {line_number}: {e}")
                            log.debug(f"Config block:\n{local_config_str}")
                            local_config = {}
                            num_errors += 1
                        except ValidationError as e:
                            log.error(e)
                            local_config = {}
                            num_errors += 1
                        local_config_str = ""

                    # Look for images
                    img_cmd_match = img_cmd_re.match(line)
                    img_match = img_snippet_re.match(line)
                    if (img_cmd_match or img_match) and not local_config.get("skip"):

                        # Skip if it's a regular image with no config snippet
                        snippet = local_config.get("snippet", "")
                        if not img_cmd_match and snippet == "":
                            continue

                        # Use the results from either a command or snippet match
                        if img_cmd_match:
                            m = img_cmd_match.groupdict()
                            if snippet != "":
                                log.warn(
                                    f"Found command but already had snippet '{snippet.strip()}' in '{file_rel_fn}'"
                                )
                        elif img_match:
                            # Check that we actually have a snippet ready
                            if not len(snippet):
                                log.debug(
                                    f"Found image tag but no snippet or command: [magenta]{file}[cyan]:L{line_number}"
                                )  # noqa: E501
                                continue
                            m = img_match.groupdict()

                        log.debug(f"Found markdown image in [magenta]{file}[/]: {m}")
                        snippet_syntax = local_config.get("snippet_syntax", self.snippet_syntax)
                        timeout = local_config.get("timeout", self.timeout)
                        hide_command = local_config.get("hide_command", self.hide_command)
                        head = local_config.get("head", self.head)
                        tail = local_config.get("tail", self.tail)
                        trim_after = local_config.get("trim_after", self.trim_after)
                        truncated_text = local_config.get("truncated_text", self.truncated_text)
                        min_pct_diff = local_config.get("min_pct_diff", self.min_pct_diff)
                        skip_change_regex = local_config.get("skip_change_regex", self.skip_change_regex)
                        t_width = local_config.get("terminal_width", self.terminal_width)
                        t_min_width = local_config.get("terminal_min_width", self.terminal_min_width)
                        notrim = local_config.get("notrim", self.notrim)
                        t_theme = local_config.get("terminal_theme", self.terminal_theme)
                        use_pty = local_config.get("use_pty", self.use_pty)
                        img_obj = rich_img.RichImg(
                            snippet_syntax,
                            timeout,
                            hide_command,
                            head,
                            tail,
                            trim_after,
                            truncated_text,
                            min_pct_diff,
                            skip_change_regex,
                            t_width,
                            t_min_width,
                            notrim,
                            t_theme,
                            use_pty,
                        )
                        img_obj.source_type = "search"
                        img_obj.source = file

                        # Save the command
                        if img_cmd_match:
                            img_obj.cwd = Path(file).parent
                            img_obj.cmd = m["cmd"]
                            num_commands += 1

                        # Save the snippet
                        else:
                            img_obj.snippet = snippet
                            num_snippets += 1

                        # Save the image path
                        img_path = Path(file).parent / Path(m["img_path"].strip())
                        img_obj.img_paths = [str(img_path.resolve())]

                        # Save the title if set
                        if m["title"]:
                            img_obj.title = m["title"].strip("'\" ")

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

        for output in config["outputs"]:
            log.debug(f"Found valid output in '{config_fn}': {output}")
            snippet_syntax = output.get("snippet_syntax", self.snippet_syntax)
            timeout = output.get("timeout", self.timeout)
            hide_command = output.get("hide_command", self.hide_command)
            head = output.get("head", self.head)
            tail = output.get("tail", self.tail)
            trim_after = output.get("trim_after", self.trim_after)
            truncated_text = output.get("truncated_text", self.truncated_text)
            min_pct_diff = output.get("min_pct_diff", self.min_pct_diff)
            skip_change_regex = output.get("skip_change_regex", self.skip_change_regex)
            t_width = output.get("terminal_width", self.terminal_width)
            t_min_width = output.get("terminal_min_width", self.terminal_min_width)
            notrim = output.get("notrim", self.notrim)
            t_theme = output.get("terminal_theme", self.terminal_theme)
            use_pty = output.get("use_pty", self.use_pty)
            img_obj = rich_img.RichImg(
                snippet_syntax,
                timeout,
                hide_command,
                head,
                tail,
                trim_after,
                truncated_text,
                min_pct_diff,
                skip_change_regex,
                t_width,
                t_min_width,
                notrim,
                t_theme,
                use_pty,
            )
            img_obj.source_type = "config"
            img_obj.source = config_fn

            # Save the command
            if "command" in output:
                img_obj.cmd = output["command"]

            # Save the snippet
            elif "snippet" in output:
                img_obj.snippet = output["snippet"]

            # Save the image paths
            for img_path_str in output["img_paths"]:
                img_path = Path(img_path_str.strip())
                img_obj.img_paths.append(str(img_path.resolve()))

            # Save the title if set
            if "title" in output:
                img_obj.title = output["title"]

            # Save the image object
            self.rich_imgs.append(img_obj)

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
        self.rich_imgs = sorted(merged_imgs.values(), key=lambda x: str(x.cmd).lower())

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
            if img_obj.cmd is not None:
                rel_source = Path(img_obj.source).relative_to(Path.cwd())
                source = f" [grey42][link=file:{Path(img_obj.source).absolute()}]{rel_source}[/][/]"
                table.add_row(img_obj.cmd, source)

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
            self.rich_imgs = [ri for ri in self.rich_imgs if ri.cmd is None]
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
            self.num_img_saved += img_obj.num_img_saved
            self.num_img_skipped += img_obj.num_img_skipped
