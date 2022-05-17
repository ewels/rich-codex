"""
rich-img is a minimal Python module for generating terminal screenshots from shell commands and text snippets.

It should work as a standalone command-line tool, however it is primarily intended
for use with the rich-img-action GitHub Action.
"""

__version__ = "1.0.dev0"

import shlex
import subprocess
from os import getenv, unlink
from tempfile import mkstemp

from cairosvg import svg2pdf, svg2png
from rich.ansi import AnsiDecoder
from rich.console import Console


def main():
    """Run rich-img as a standalone command-line tool."""
    cmd = getenv("COMMAND")

    console = Console(
        force_terminal=True,
        color_system="truecolor",
        highlight=False,
        record=True,
        width=int(getenv("TERMINAL_WIDTH")) if getenv("TERMINAL_WIDTH") else None,
    )
    decoder = AnsiDecoder()

    process = subprocess.Popen(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output = process.stdout.read().decode("utf-8")

    for line in decoder.decode(output):
        console.print(line)

    # Save image as requested with $IMG_PATHS
    for filename in getenv("IMG_PATHS", "").splitlines():
        save_image(console, filename, cmd)


def save_image(console, filename, title=None):
    """Save the image to the specified filename."""
    svg_filename = filename
    if filename.lower().endswith(".png") or filename.lower().endswith(".pdf"):
        svg_filename = mkstemp(suffix=".svg")[1]

    # We always generate an SVG first
    console.save_svg(svg_filename, title=title)

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
