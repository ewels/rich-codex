import logging
import shlex
import subprocess
from os import devnull, unlink
from tempfile import mkstemp

from cairosvg import svg2pdf, svg2png
from rich.ansi import AnsiDecoder
from rich.console import Console
from rich.logging import RichHandler

logging.basicConfig(level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])

log = logging.getLogger("rich-img")


class RichImg:
    """Main class for rich-img."""

    def __init__(self, terminal_width=None, terminal_theme=None):
        """Initialise the RichImg object with core console options."""
        self.terminal_width = terminal_width
        self.terminal_theme = terminal_theme
        self.console = Console(
            file=open(devnull, "w"),
            force_terminal=True,
            color_system="truecolor",
            highlight=False,
            record=True,
            width=int(terminal_width) if terminal_width else None,
        )

    def pipe_command(self, cmd, img_paths):
        """Capture output from a supplied command and save to an image."""
        log.info(f"Running {cmd}")

        decoder = AnsiDecoder()

        process = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output = process.stdout.read().decode("utf-8")

        for line in decoder.decode(output):
            self.console.print(line)

        # Save image as requested with $IMG_PATHS
        for filename in img_paths.splitlines():
            self.save_image(filename, cmd)

    def save_image(self, filename, title=None):
        """Save the image to the specified filename."""
        log.info(f"Saving {filename}")
        svg_filename = filename
        if filename.lower().endswith(".png") or filename.lower().endswith(".pdf"):
            svg_filename = mkstemp(suffix=".svg")[1]

        # We always generate an SVG first
        self.console.save_svg(svg_filename, title=title)

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
