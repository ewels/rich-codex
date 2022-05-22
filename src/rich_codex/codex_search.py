import logging
import pathlib
import re
from glob import glob

from rich_codex import rich_img

log = logging.getLogger("rich-codex")


class CodexSearch:
    """File search class for rich-codex.

    Looks through a set of source files for sets of configuration
    needed to generate screenshots.
    """

    def __init__(self, search_paths, search_include, search_exclude, terminal_width, terminal_theme):
        """Initialize the search object."""
        self.search_paths = [None] if len(search_paths) == 0 else search_paths
        self.search_include = ["**/*.md"] if search_include is None else self._clean_list(search_include.splitlines())
        self.search_exclude = ["**/.git*", "**/.git*/**", "**/node_modules/**"]
        if search_exclude is not None:
            self.search_exclude.extend(self._clean_list(search_exclude.splitlines()))
        self.terminal_width = terminal_width
        self.terminal_theme = terminal_theme
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
            log.debug(f"Searching {len(search_files)} files")

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

    def save_all_images(self):
        """Save the images that we have collected."""
        dedup_imgs = set(self.rich_imgs)
        log.debug(f"Collapsing {len(self.rich_imgs)} image requests to {len(dedup_imgs)} deduplicated")
        for img_obj in dedup_imgs:
            img_obj.get_output()
            img_obj.save_images()
