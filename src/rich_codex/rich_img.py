import logging
import pathlib
import shlex
import subprocess
from os import devnull, unlink
from tempfile import mkstemp

from cairosvg import svg2pdf, svg2png
from rich.ansi import AnsiDecoder
from rich.console import Console
from rich.syntax import Syntax

log = logging.getLogger("rich-codex")


class RichImg:
    """Image generation for rich-codex.

    Objects from this class are typically used once per screenshot.
    """

    def __init__(self, terminal_width=None, terminal_theme=None):
        """Initialise the RichImg object with core console options."""
        self.terminal_width = terminal_width
        self.terminal_theme = terminal_theme
        self.title = "rich-codex"
        self.console = Console(
            file=open(devnull, "w"),
            force_terminal=True,
            color_system="truecolor",
            highlight=False,
            record=True,
            width=int(terminal_width) if terminal_width else None,
        )

    def pipe_command(self, cmd):
        """Capture output from a supplied command and save to an image."""
        log.debug(f"Running command '{cmd}'")
        self.title = cmd

        # Run the command
        process = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Decode and print the output (captured)
        output = process.stdout.read().decode("utf-8")
        decoder = AnsiDecoder()
        for line in decoder.decode(output):
            self.console.print(line)

    def format_snippet(self, snippet, snippet_format=None):
        """Take a text snippet and format it using rich."""
        log.info("Formatting snippet")

        # JSON is a special case, use rich function
        try:
            if snippet_format == "json" or snippet_format is None:
                self.console.print_json(json=snippet)
                log.debug("Formatting snippet as JSON")
                return
            else:
                raise

        # All other languages, use rich Syntax highlighter (no reformatting whitespace)
        except Exception:
            log.debug(f"Formatting snippet as {snippet_format}")
            syntax = Syntax(snippet, snippet_format)
            self.console.print(syntax)

    def save_images(self, img_paths):
        """Save the images to the specified filenames."""
        # Save image as requested with $IMG_PATHS
        for filename in img_paths.splitlines():
            log.debug(f"Saving [magenta]{filename}")

            # Make directories if necessary
            pathlib.Path(filename).parent.mkdir(parents=True, exist_ok=True)

            # Set filenames
            svg_filename = filename
            if filename.lower().endswith(".png") or filename.lower().endswith(".pdf"):
                svg_filename = mkstemp(suffix=".svg")[1]

            # We always generate an SVG first
            self.console.save_svg(svg_filename, title=self.title)

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
