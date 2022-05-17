"""
rich-img is a minimal Python module for generating terminal screenshots from shell commands and text snippets.

It should work as a standalone command-line tool, however it is primarily intended
for use with the rich-img-action GitHub Action.
"""

import shlex
import subprocess
from os import getenv

from cairosvg import svg2pdf, svg2png
from rich.ansi import AnsiDecoder
from rich.console import Console

cmd = "python /Users/phil/GitHub/ewels/rich-click/examples/click/01_simple.py --help"

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


console.save_svg("test.svg", title=cmd)

svg2png(file_obj=open("test.svg", "rb"), write_to="test.png", dpi=300, output_width=4000)
svg2pdf(file_obj=open("test.svg", "rb"), write_to="test.pdf")
