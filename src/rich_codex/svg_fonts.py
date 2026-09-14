"""Embed the terminal font into rendered SVGs.

Rich points the SVG's ``@font-face`` rules at a CDN copy of Fira Code, with a
``local()`` source in front of it. GitHub (and most other markdown renderers) serve
images through an ``<img>`` tag, and SVGs in ``<img>`` render in secure static mode,
where no external resource is ever fetched. That leaves ``local()`` as the only source
that can resolve, so the image only looks right on machines that happen to have Fira
Code installed. Everywhere else the renderer substitutes another font, and because Rich
places every chunk of text at an absolute x coordinate derived from the character width
it expects, the glyphs drift within each chunk and box-drawing characters come apart.

A data URI is not an external fetch, so it works in ``<img>`` mode. This module subsets
Fira Code down to the characters one image actually renders and rewrites the
``@font-face`` rules to point at that, base64 encoded.
"""

from __future__ import annotations

import base64
import html
import io
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fontTools.ttLib import TTFont

log = logging.getLogger("rich-codex")

# Fira Code 6.2.0, the same release that Rich's SVG template links to on cdnjs
FONTS_DIR = Path(__file__).parent / "fonts"
FONT_FILES = {400: FONTS_DIR / "FiraCode-Regular.woff2", 700: FONTS_DIR / "FiraCode-Bold.woff2"}

# OFL 1.1 requires the copyright and licence notice to travel with the font. It is also
# kept in the subset's own name table (see NAME_IDS), but a reader of the SVG shouldn't
# have to decode a base64 blob to find it.
LICENCE_COMMENT = """<!--
    The embedded font is Fira Code, subset by rich-codex to the characters used above.
    Copyright (c) 2014, The Fira Code Project Authors (https://github.com/tonsky/FiraCode)
    Licensed under the SIL Open Font License, Version 1.1 (https://scripts.sil.org/OFL)
    -->
    """

# Name table records to keep in the subset: the ones a subset needs to identify itself
# (0-6) plus trademark, licence description and licence URL.
NAME_IDS = [0, 1, 2, 3, 4, 5, 6, 7, 13, 14]

# Rich writes one '@font-face' block per weight, with no nested braces
FONT_FACE_RE = re.compile(r"@font-face\s*\{[^{}]*\}")
TEXT_RE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.DOTALL)
# Rich's own style rules are '.<unique_id>-r<n> { ... }'; the '-title' rule is Arial, and
# so isn't rendered in the embedded font
BOLD_RULE_RE = re.compile(r"-r\d+\s*\{[^{}]*font-weight:\s*bold")


class FontEmbedError(Exception):
    """Raised when the font can't be embedded, leaving the SVG as Rich rendered it."""


def embed_fonts(svg: str) -> str:
    """Replace the SVG's remote '@font-face' rules with an embedded font subset.

    Returns the rewritten SVG. Raises FontEmbedError if the font tooling is missing or
    if Rich's template has changed shape enough that the rules can't be found.
    """
    faces = list(FONT_FACE_RE.finditer(svg))
    if len(faces) != 2 or not all("Fira Code" in face.group() for face in faces):
        raise FontEmbedError(
            f"Expected 2 Fira Code '@font-face' rules in the rendered SVG, found {len(faces)}. "
            "Rich's SVG template has probably changed."
        )
    if svg[faces[0].end() : faces[1].start()].strip():
        raise FontEmbedError("Rich's two '@font-face' rules are no longer adjacent in the rendered SVG.")

    characters = used_characters(svg)
    if not characters:
        raise FontEmbedError("Found no text to embed a font for in the rendered SVG.")

    weights = [400, 700] if uses_bold(svg) else [400]
    css = "\n".join(_font_face(weight, characters) for weight in weights)

    svg = svg[: faces[0].start()] + css.lstrip() + svg[faces[1].end() :]
    return svg.replace("<style>", LICENCE_COMMENT + "<style>", 1)


def used_characters(svg: str) -> str:
    """Collect the characters rendered in the terminal font, as a sorted string.

    Only the text drawn in the terminal matrix counts: the window title is set in Arial
    by Rich's template, so its characters don't need to be in the subset.
    """
    characters: set[str] = set()
    for attrs, text in TEXT_RE.findall(svg):
        if "-title" in attrs:
            continue
        characters.update(html.unescape(text))
    return "".join(sorted(characters))


def uses_bold(svg: str) -> bool:
    """Check whether any of the terminal text is bold.

    Most images use no bold at all, and dropping the 700 weight halves what gets embedded.
    If this is ever wrong the browser synthesises bold from the regular face, which is a
    much smaller problem than the wrong font entirely.
    """
    return BOLD_RULE_RE.search(svg) is not None


def _font_face(weight: int, characters: str) -> str:
    """Build a single '@font-face' rule with the subset font inlined as a data URI."""
    subset = subset_font(FONT_FILES[weight], characters)
    encoded = base64.b64encode(subset).decode("ascii")
    return (
        "    @font-face {\n"
        '        font-family: "Fira Code";\n'
        f'        src: url("data:font/woff2;base64,{encoded}") format("woff2");\n'
        "        font-style: normal;\n"
        f"        font-weight: {weight};\n"
        "    }\n"
    )


def subset_font(font_file: Path, characters: str) -> bytes:
    """Cut a font down to the given characters and return it as WOFF2.

    The output has to be byte-for-byte reproducible: rich-codex commits its SVGs back to
    the repository, so any wobble here would churn the diff on every run. Hence the
    explicit 'recalc' options, which would otherwise stamp the current time into the
    font's head table.
    """
    try:
        from fontTools import version as fonttools_version
        from fontTools.subset import Options, Subsetter
        from fontTools.ttLib import TTFont
    except ImportError as e:
        raise FontEmbedError(
            "fontTools is needed to embed fonts in SVGs. "
            r"Please install with the fonts extra: 'rich-codex\[fonts]'"
        ) from e

    # rich-codex logs through the root logger, so fontTools' running commentary on the
    # subset (a couple of dozen lines per font) would otherwise end up in its output
    logging.getLogger("fontTools").setLevel(logging.WARNING)

    # Different fontTools releases subset the same font to different bytes, so a version
    # bump rewrites every image with an embedded font. Worth being able to see which one
    # produced a given image when that happens.
    log.debug(f"Subsetting '{font_file.name}' to {len(characters)} characters, fontTools {fonttools_version}")

    options = Options()
    options.name_IDs = NAME_IDS
    # Keep the default layout features, so that ligatures render as they would with
    # Fira Code installed locally
    font: TTFont = TTFont(font_file, recalcTimestamp=False, recalcBBoxes=False)
    subsetter = Subsetter(options=options)
    subsetter.populate(text=characters)
    subsetter.subset(font)

    font.flavor = "woff2"
    buffer = io.BytesIO()
    try:
        font.save(buffer)
    except ImportError as e:  # WOFF2 compression needs brotli, which fontTools doesn't require
        raise FontEmbedError(
            "The brotli library is needed to embed fonts in SVGs. "
            r"Please install with the fonts extra: 'rich-codex\[fonts]'"
        ) from e
    return buffer.getvalue()
