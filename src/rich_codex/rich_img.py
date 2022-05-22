import logging
import pathlib
import shlex
import subprocess
from os import devnull, unlink
from tempfile import mkstemp

from rich.ansi import AnsiDecoder
from rich.console import Console
from rich.syntax import Syntax

log = logging.getLogger("rich-codex")

# Attributes of RichImg which are important for equality
RICH_IMG_ATTRS = [
    "terminal_width",
    "terminal_theme",
    "title",
    "cmd",
    "snippet",
    "snippet_format",
    "img_paths",
]


class RichImg:
    """Image generation for rich-codex.

    Objects from this class are typically used once per screenshot.
    """

    def __init__(self, terminal_width=None, terminal_theme=None):
        """Initialise the RichImg object with core console options."""
        self.terminal_width = terminal_width
        self.terminal_theme = terminal_theme
        self.title = None
        self.console = Console(
            file=open(devnull, "w"),
            force_terminal=True,
            color_system="truecolor",
            highlight=False,
            record=True,
            width=int(terminal_width) if terminal_width else None,
        )
        self.cmd = None
        self.snippet = None
        self.snippet_format = None
        self.img_paths = []

    def __eq__(self, other):
        """Compare RichImg objects for equality."""
        if not isinstance(other, RichImg):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return all(getattr(self, attr) == getattr(other, attr) for attr in RICH_IMG_ATTRS)

    def __hash__(self):
        """Hash stable identifier of RichImg object based on important attributes."""
        return hash(getattr(self, attr) for attr in RICH_IMG_ATTRS)

    def pipe_command(self):
        """Capture output from a supplied command and save to an image."""
        if self.cmd is None:
            log.debug("Tried to generate image with no command")
            return

        log.debug(f"Running command '{self.cmd}'")
        if self.title is None:
            self.title = self.cmd

        # Run the command
        process = subprocess.Popen(
            shlex.split(self.cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Decode and print the output (captured)
        output = process.stdout.read().decode("utf-8")
        decoder = AnsiDecoder()
        for line in decoder.decode(output):
            self.console.print(line)

    def format_snippet(self):
        """Take a text snippet and format it using rich."""
        if self.snippet is None:
            log.debug("Tried to format snippet with no snippet")
            return

        log.info("Formatting snippet")

        # JSON is a special case, use rich function
        try:
            if self.snippet_format == "json" or self.snippet_format is None:
                self.console.print_json(json=self.snippet)
                log.debug("Formatting snippet as JSON")
                return
            else:
                raise

        # All other languages, use rich Syntax highlighter (no reformatting whitespace)
        except Exception:
            log.debug(f"Formatting snippet as {self.snippet_format}")
            syntax = Syntax(self.snippet, self.snippet_format)
            self.console.print(syntax)

    def get_output(self):
        """Either pipe command or format snippet, depending on what is set."""
        if self.cmd is not None:
            self.pipe_command()
        elif self.snippet is None:
            self.format_snippet()
        else:
            log.debug("Tried to get output with no command or snippet")

    def save_images(self):
        """Save the images to the specified filenames."""
        if len(self.img_paths) == 0:
            log.debug("Tried to save images with no paths")
            return

        # Save image as requested with $IMG_PATHS
        for filename in self.img_paths:
            log.debug(f"Saving [magenta]{filename}")

            # Make directories if necessary
            pathlib.Path(filename).parent.mkdir(parents=True, exist_ok=True)

            # Set filenames
            svg_filename = filename
            if filename.lower().endswith(".png") or filename.lower().endswith(".pdf"):
                svg_filename = mkstemp(suffix=".svg")[1]

            # We always generate an SVG first
            self.console.save_svg(svg_filename, title=self.title)

            # Lazy-load PNG / PDF libraries if needed
            if filename.lower().endswith(".png") or filename.lower().endswith(".pdf"):
                from cairosvg import svg2pdf, svg2png

            # Convert to PNG if requested
            if filename.lower().endswith(".png"):
                svg2png(
                    file_obj=open(svg_filename, "rb"),
                    write_to=filename,
                    dpi=300,
                    output_width=4000,
                )
                unlink(svg_filename)

            # Convert to PDF if requested
            if filename.lower().endswith(".pdf"):
                svg2pdf(
                    file_obj=open(svg_filename, "rb"),
                    write_to=filename,
                )
                unlink(svg_filename)
