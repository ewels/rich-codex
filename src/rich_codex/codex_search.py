import logging
import pathlib
from glob import glob

import regex

from rich_codex import rich_img

log = logging.getLogger("rich-codex")


class CodexSearch:
    """File search class for rich-codex.

    Looks through a set of source files for sets of configuration
    needed to generate screenshots.
    """

    def __init__(self, search_include, search_exclude, terminal_width, terminal_theme):
        """Initialize the search object."""
        self.search_include = ["**/*.md"] if search_include is None else self._clean_list(search_include.splitlines())
        self.search_exclude = ["**/.git*", "**/.git*/**", "**/node_modules/**"]
        if search_exclude is not None:
            self.search_exclude.extend(self._clean_list(search_exclude.splitlines()))
        self.terminal_width = terminal_width
        self.terminal_theme = terminal_theme

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
        for pattern in self.search_include:
            search_files |= set(glob(pattern, recursive=True))
        for pattern in self.search_exclude:
            search_files = search_files - set(glob(pattern, recursive=True))

        # eg. ![`rich --help`](rich-cli-help.svg)
        img_cmd_re = regex.compile(r"!\[`([^`]+)`\]\(([^\]]+)\)")
        for file in search_files:
            with open(file, "r") as fh:
                for line in fh:
                    matches = img_cmd_re.findall(line)
                    for match in matches:
                        log.info(f"Found markdown image in [magenta]{file}[/]: {match}")
                        img_obj = rich_img.RichImg(self.terminal_width, self.terminal_theme)
                        command = match[0]
                        file_base = pathlib.Path(file).parent
                        img_base = pathlib.Path(match[1])
                        img_path = str(file_base / img_base)
                        img_obj.pipe_command(command)
                        img_obj.save_images(img_path)
