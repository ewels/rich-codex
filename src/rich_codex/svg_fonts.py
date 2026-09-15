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

Rich sets the window title in Arial, which has the same problem and can't be bundled to
fix it, being proprietary. Inter is embedded in its place, and the title's ``font-family``
rewritten to ask for it.
"""

from __future__ import annotations

import base64
import html
import io
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fontTools.ttLib import TTFont

log = logging.getLogger("rich-codex")

# Fira Code 6.2, the same release that Rich's SVG template links to on cdnjs. Bundled as
# TTF rather than WOFF2 because the PNG renderer can only read TTF, and subsetting gives
# byte-identical output from either.
FONTS_DIR = Path(__file__).parent / "fonts"
FONT_FILES = {400: FONTS_DIR / "FiraCode-Regular.ttf", 700: FONTS_DIR / "FiraCode-Bold.ttf"}

# Rich sets the window title in Arial. Arial can't be bundled (it isn't free) and isn't
# installed on most Linux machines either, so Inter stands in for it. Rich's title rule is
# always bold, so one weight is all that's needed.
TITLE_FONT_FAMILY = "Inter"
TITLE_FONT_FILE = FONTS_DIR / "Inter-Bold.ttf"
TITLE_FONT_WEIGHT = 700

# What Rich's title rule says, and what it's rewritten to. Arial is kept in the stack for
# anything that can't use the embedded face.
TITLE_FAMILY_RULE = "font-family: arial;"
EMBEDDED_TITLE_FAMILY_RULE = f'font-family: "{TITLE_FONT_FAMILY}", arial, sans-serif;'

# Everything the PNG rasteriser needs to be handed, since it can't read embedded fonts
RASTER_FONT_FILES = [*FONT_FILES.values(), TITLE_FONT_FILE]

# OFL 1.1 requires the copyright and licence notice to travel with the font. They are also
# kept in each subset's own name table (see NAME_IDS), but a reader of the SVG shouldn't
# have to decode a base64 blob to find them.
FONT_COPYRIGHTS = {
    "Fira Code": "Copyright (c) 2014, The Fira Code Project Authors (https://github.com/tonsky/FiraCode)",
    TITLE_FONT_FAMILY: "Copyright (c) 2016 The Inter Project Authors (https://github.com/rsms/inter)",
}

# Name table records to keep in the subset: the ones a subset needs to identify itself
# (0-6) plus trademark, licence description and licence URL.
NAME_IDS = [0, 1, 2, 3, 4, 5, 6, 7, 13, 14]

# Rich writes one '@font-face' block per weight, with no nested braces
FONT_FACE_RE = re.compile(r"@font-face\s*\{[^{}]*\}")
# The same thing as raw bytes, for comparing images without decoding them
EMBEDDED_FONT_BYTES_RE = re.compile(rb"(data:font/woff2;base64,)[A-Za-z0-9+/=]+")
TEXT_RE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.DOTALL)
# Rich's own style rules are '.<unique_id>-r<n> { ... }'. The '-title' rule is left out:
# it has its own font, and is always bold.
BOLD_RULE_RE = re.compile(r"-r\d+\s*\{[^{}]*font-weight:\s*bold")


class FontEmbedError(Exception):
    """Raised when the font can't be embedded, leaving the SVG as Rich rendered it."""


def embed_fonts(svg: str) -> str:
    """Replace the SVG's remote '@font-face' rules with embedded font subsets.

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
    families = ["Fira Code"]
    css = [_font_face("Fira Code", weight, FONT_FILES[weight], characters) for weight in weights]

    # Most images have no title, and then there is nothing to set in Inter
    title = title_characters(svg)
    if title:
        families.append(TITLE_FONT_FAMILY)
        css.append(_font_face(TITLE_FONT_FAMILY, TITLE_FONT_WEIGHT, TITLE_FONT_FILE, title))

    svg = svg[: faces[0].start()] + "\n".join(css).lstrip() + svg[faces[1].end() :]
    if title:
        if TITLE_FAMILY_RULE not in svg:
            raise FontEmbedError(f"Could not find '{TITLE_FAMILY_RULE}' to point the window title at a bundled font.")
        svg = svg.replace(TITLE_FAMILY_RULE, EMBEDDED_TITLE_FAMILY_RULE, 1)
    return svg.replace("<style>", _licence_comment(families) + "<style>", 1)


@lru_cache(maxsize=1)
def bundled_codepoints() -> frozenset[int]:
    """Every character the bundled fonts can draw, as a set of code points."""
    from fontTools.ttLib import TTFont

    codepoints: set[int] = set()
    for font_file in RASTER_FONT_FILES:
        codepoints.update(TTFont(font_file).getBestCmap())
    return frozenset(codepoints)


def unrenderable_characters(svg: str) -> str:
    """Visible characters in the image that none of the bundled fonts can draw.

    Whitespace is left out: it has no glyph to miss. Typically this is emoji, which Rich
    output is full of and which no monospace font carries.
    """
    characters = used_characters(svg) + title_characters(svg)
    try:
        drawable = bundled_codepoints()
    except ImportError:  # fontTools missing; the caller has bigger problems than a warning
        return ""
    return "".join(sorted({c for c in characters if not c.isspace() and ord(c) not in drawable}))


def has_embedded_fonts(svg: str) -> bool:
    """Check whether an SVG carries its own fonts, rather than linking to them."""
    return "data:font/woff2;base64," in svg


def _licence_comment(families: list[str]) -> str:
    """Build the SVG comment carrying the copyright notice of each embedded font."""
    notices = "\n".join(f"    {FONT_COPYRIGHTS[family]}" for family in families)
    return (
        "<!--\n"
        f"    Embedded by rich-codex, subset to the characters used above: {', '.join(families)}.\n"
        f"{notices}\n"
        "    Licensed under the SIL Open Font License, Version 1.1 (https://scripts.sil.org/OFL)\n"
        "    -->\n    "
    )


def without_embedded_fonts(image: bytes) -> bytes:
    """Strip embedded font data out of an image, for comparing one render against another.

    The subset is derived from the text, so it carries nothing the text doesn't already
    say: a font that changed means characters that changed. Leaving it in would drown out
    'min_pct_diff' and hand 'skip_change_regex' a changed line it can never match, so an
    ignored timestamp would still rewrite the image whenever its digits changed.

    Takes bytes rather than str because it also gets handed PNGs and PDFs, which it leaves
    alone.
    """
    return EMBEDDED_FONT_BYTES_RE.sub(rb"\1", image)


def used_characters(svg: str) -> str:
    """Collect the characters rendered in the terminal font, as a sorted string.

    Only the text drawn in the terminal matrix counts. The window title has a font of its
    own, and its characters are collected by title_characters().
    """
    characters: set[str] = set()
    for attrs, text in TEXT_RE.findall(svg):
        if "-title" in attrs:
            continue
        characters.update(html.unescape(text))
    return "".join(sorted(characters))


def title_characters(svg: str) -> str:
    """Collect the characters in the window title, as a sorted string.

    Empty when the image has no title, which is the usual case.
    """
    characters: set[str] = set()
    for attrs, text in TEXT_RE.findall(svg):
        if "-title" in attrs:
            characters.update(html.unescape(text))
    return "".join(sorted(characters))


def uses_bold(svg: str) -> bool:
    """Check whether any of the terminal text is bold.

    Most images use no bold at all, and dropping the 700 weight halves what gets embedded.
    If this is ever wrong the browser synthesises bold from the regular face, which is a
    much smaller problem than the wrong font entirely.
    """
    return BOLD_RULE_RE.search(svg) is not None


def _font_face(family: str, weight: int, font_file: Path, characters: str) -> str:
    """Build a single '@font-face' rule with the subset font inlined as a data URI.

    Indented like Rich's own rules, and with no trailing newline, so that what replaces
    them lines up byte for byte with what it replaced. An extra blank line here would
    show up as a diff in every image rich-codex has ever generated.
    """
    subset = subset_font(font_file, characters)
    encoded = base64.b64encode(subset).decode("ascii")
    return (
        "    @font-face {\n"
        f'        font-family: "{family}";\n'
        f'        src: url("data:font/woff2;base64,{encoded}") format("woff2");\n'
        "        font-style: normal;\n"
        f"        font-weight: {weight};\n"
        "    }"
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
        raise FontEmbedError("fontTools is needed to embed fonts in SVGs, but could not be imported.") from e

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
        raise FontEmbedError("The brotli library is needed to embed fonts in SVGs, but could not be imported.") from e
    return buffer.getvalue()
