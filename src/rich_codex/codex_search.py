import logging
import pathlib
import re
from glob import glob

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from rich_codex import rich_img

log = logging.getLogger("rich-codex")


class CodexSearch:
    """File search class for rich-codex.

    Looks through a set of source files for sets of configuration
    needed to generate screenshots.
    """

    def __init__(
        self, search_paths, search_include, search_exclude, no_confirm, terminal_width, terminal_theme, console
    ):
        """Initialize the search object."""
        self.search_paths = [None] if len(search_paths) == 0 else search_paths
        self.search_include = ["**/*.md"] if search_include is None else self._clean_list(search_include.splitlines())
        self.search_exclude = ["**/.git*", "**/.git*/**", "**/node_modules/**"]
        if search_exclude is not None:
            self.search_exclude.extend(self._clean_list(search_exclude.splitlines()))
        self.no_confirm = no_confirm
        self.terminal_width = terminal_width
        self.terminal_theme = terminal_theme
        self.console = Console() if console is None else console
        self.rich_imgs = []

        # Look in .gitignore to add to search_exclude
        try:
            with open(".gitignore", "r") as fh:
                log.debug("Appending contents of .gitignore to 'SEARCH_EXCLUDE'")
                self.search_exclude.extend(self._clean_list(fh.readlines()))
        except IOError:
            pass

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
        for search_path in self.search_paths:
            for pattern in self.search_include:
                search_files |= set(glob(pattern, root_dir=search_path, recursive=True))
            for pattern in self.search_exclude:
                search_files = search_files - set(glob(pattern, root_dir=search_path, recursive=True))
        if len(search_files) == 0:
            log.error("No files found to search")
        else:
            log.info(f"Searching {len(search_files)} files")

        # eg. ![`rich --help`](rich-cli-help.svg)
        img_cmd_re = re.compile(r"!\[`(?P<cmd>[^`]+)`\]\((?P<img_path>.*?)(?=\"|\))(?P<title>[\"'].*[\"'])?\)")
        for file in search_files:
            with open(file, "r") as fh:
                for line in fh:
                    for match in img_cmd_re.finditer(line):
                        m = match.groupdict()

                        log.debug(f"Found markdown image in [magenta]{file}[/]: {m}")
                        img_obj = rich_img.RichImg(self.terminal_width, self.terminal_theme)

                        # Save the command
                        img_obj.cmd = m["cmd"]

                        # Save the image path
                        img_path = pathlib.Path(file).parent / pathlib.Path(m["img_path"].strip())
                        img_obj.img_paths = [str(img_path)]

                        # Save the title if set
                        if m["title"]:
                            img_obj.title = m["title"].strip("'\" ")

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
        self.rich_imgs = merged_imgs.values()

    def confirm_commands(self):
        """Prompt the user to confirm running the commands."""
        # Collect the unique commands
        commands = set()
        for img_obj in self.rich_imgs:
            if img_obj.cmd is not None:
                commands.add(img_obj.cmd)

        if len(commands) == 0:
            return True

        table = Table(box=None, show_header=False, row_styles=["bold green", "green"])
        for cmd in commands:
            table.add_row(cmd)

        self.console.print(Panel(table, title="Commands to run", title_align="left", border_style="blue"))

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
