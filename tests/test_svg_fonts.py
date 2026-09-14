import base64
import io
import logging
import re

import pytest
from rich._export_format import CONSOLE_SVG_FORMAT
from rich.console import Console

from rich_codex import svg_fonts

DATA_URI_RE = re.compile(r'src: url\("data:font/woff2;base64,([A-Za-z0-9+/=]+)"\)')


def render(text="hello world", **kwargs):
    """Render some text to an SVG the way RichImg does, without touching the filesystem."""
    console = Console(record=True, file=io.StringIO(), width=40, force_terminal=True)
    console.print(text, **kwargs)
    return console.export_svg(unique_id="test")


def embedded_fonts(svg):
    """Pull the embedded WOFF2 fonts back out of an SVG."""
    return [base64.b64decode(match) for match in DATA_URI_RE.findall(svg)]


class TestRichTemplate:
    """The assumptions about Rich's SVG template that the embedding relies on.

    Rich has changed this template before. These fail loudly if it changes again, rather
    than letting a silently unpatched SVG get committed.
    """

    def test_two_font_face_rules(self):
        assert CONSOLE_SVG_FORMAT.count("@font-face {{") == 2

    def test_fira_code_by_name(self):
        assert CONSOLE_SVG_FORMAT.count('font-family: "Fira Code";') == 2
        assert 'local("FiraCode-Regular")' in CONSOLE_SVG_FORMAT
        assert 'local("FiraCode-Bold")' in CONSOLE_SVG_FORMAT

    def test_font_faces_are_adjacent(self):
        between = CONSOLE_SVG_FORMAT.split("@font-face {{")[1].split("}}")[1]
        assert not between.strip()

    def test_vendored_weights_cover_the_template(self):
        assert set(svg_fonts.FONT_FILES) == {400, 700}
        for font_file in svg_fonts.FONT_FILES.values():
            assert font_file.is_file()


class TestEmbedFonts:
    """Tests for svg_fonts.embed_fonts()."""

    def test_no_remote_font_is_left(self):
        svg = svg_fonts.embed_fonts(render())
        for rule in svg_fonts.FONT_FACE_RE.findall(svg):
            assert "https://" not in rule
            assert "local(" not in rule
        assert "cdnjs.cloudflare.com" not in svg

    def test_font_is_embedded_as_a_data_uri(self):
        fonts = embedded_fonts(svg_fonts.embed_fonts(render()))
        assert len(fonts) == 1
        assert fonts[0][:4] == b"wOF2"

    def test_licence_notice_travels_with_the_font(self):
        svg = svg_fonts.embed_fonts(render())
        assert "SIL Open Font License" in svg
        assert "The Fira Code Project Authors" in svg
        # ...and inside the font binary too, in its name table
        from fontTools.ttLib import TTFont

        names = TTFont(io.BytesIO(embedded_fonts(svg)[0])).get("name")
        assert "Open Font License" in names.getDebugName(13)

    def test_bold_is_embedded_when_used(self):
        assert len(embedded_fonts(svg_fonts.embed_fonts(render("hello", style="bold")))) == 2

    def test_bold_is_left_out_when_unused(self):
        assert len(embedded_fonts(svg_fonts.embed_fonts(render("hello")))) == 1

    def test_the_rest_of_the_svg_is_untouched(self):
        """Only the font rules change, down to the whitespace.

        A stray newline here would land as a diff line in every image a user regenerates,
        on top of the font itself.
        """
        svg = render()
        embedded = svg_fonts.embed_fonts(svg)

        def after_the_font_rules(text):
            return text[list(svg_fonts.FONT_FACE_RE.finditer(text))[-1].end() :]

        assert after_the_font_rules(embedded) == after_the_font_rules(svg)
        assert embedded.split("<style>")[0].replace(svg_fonts.LICENCE_COMMENT, "") == svg.split("<style>")[0]

    def test_no_font_face_rules_is_an_error(self):
        with pytest.raises(svg_fonts.FontEmbedError, match="found 0"):
            svg_fonts.embed_fonts("<svg><style></style></svg>")

    def test_a_third_font_face_rule_is_an_error(self):
        svg = render().replace("<style>", "<style>\n@font-face { font-family: Comic Sans; }", 1)
        with pytest.raises(svg_fonts.FontEmbedError, match="found 3"):
            svg_fonts.embed_fonts(svg)

    def test_separated_font_face_rules_are_an_error(self):
        svg = render().replace("}\n    @font-face", "}\n    .interloper { fill: red }\n    @font-face", 1)
        with pytest.raises(svg_fonts.FontEmbedError, match="no longer adjacent"):
            svg_fonts.embed_fonts(svg)

    def test_no_text_is_an_error(self):
        svg = re.sub(r"<text.*?</text>", "", render(), flags=re.DOTALL)
        with pytest.raises(svg_fonts.FontEmbedError, match="no text"):
            svg_fonts.embed_fonts(svg)

    def test_missing_fonttools_is_an_error(self, block_import):
        block_import("fontTools.subset", "fontTools.ttLib")
        with pytest.raises(svg_fonts.FontEmbedError, match="fontTools is needed"):
            svg_fonts.embed_fonts(render())

    def test_fonttools_is_not_chatty(self, caplog):
        """rich-codex logs through the root logger, so a noisy library ends up in its output."""
        caplog.set_level(logging.DEBUG)
        svg_fonts.embed_fonts(render())
        assert [record for record in caplog.records if record.name.startswith("fontTools")] == []


class TestDeterminism:
    """Generated SVGs get committed, so identical input has to give identical bytes.

    Anything less and every CI run would rewrite every image.
    """

    def test_repeated_embedding_is_identical(self):
        svg = render("determinism matters")
        assert svg_fonts.embed_fonts(svg) == svg_fonts.embed_fonts(svg)

    def test_repeated_subsetting_is_identical(self):
        font_file = svg_fonts.FONT_FILES[400]
        assert svg_fonts.subset_font(font_file, "abc") == svg_fonts.subset_font(font_file, "abc")

    def test_character_order_does_not_matter(self):
        font_file = svg_fonts.FONT_FILES[400]
        assert svg_fonts.subset_font(font_file, "abc") == svg_fonts.subset_font(font_file, "cba")


class TestWithoutEmbeddedFonts:
    """Tests for svg_fonts.without_embedded_fonts()."""

    def test_the_payload_goes(self):
        svg = svg_fonts.embed_fonts(render()).encode()
        stripped = svg_fonts.without_embedded_fonts(svg)
        assert b"data:font/woff2;base64," in stripped
        assert not DATA_URI_RE.findall(stripped.decode())

    def test_two_renders_differing_only_in_font_compare_equal(self):
        """'a' and 'b' need different subsets, so only stripping makes the rest comparable."""
        one = svg_fonts.embed_fonts(render("a")).encode()
        other = svg_fonts.embed_fonts(render("b")).encode()
        assert one != other
        stripped_one = svg_fonts.without_embedded_fonts(one)
        stripped_other = svg_fonts.without_embedded_fonts(other)
        assert len(stripped_one) == len(stripped_other)
        assert stripped_one.count(b"base64,") == 1

    def test_an_svg_with_no_embedded_font_is_untouched(self):
        svg = render().encode()
        assert svg_fonts.without_embedded_fonts(svg) == svg

    def test_binary_files_are_untouched(self):
        png = b"\x89PNG\r\n\x1a\n" + bytes(range(256))
        assert svg_fonts.without_embedded_fonts(png) == png


class TestUsedCharacters:
    """Tests for svg_fonts.used_characters()."""

    def test_characters_are_sorted_and_deduplicated(self):
        svg = '<text class="x-r1">banana</text>'
        assert svg_fonts.used_characters(svg) == "abn"

    def test_entities_are_decoded(self):
        svg = "<text>a&#160;b&amp;c</text>"
        assert svg_fonts.used_characters(svg) == "&abc\xa0"

    def test_the_window_title_is_ignored(self):
        svg = '<text class="x-title">QQQ</text><text class="x-r1">a</text>'
        assert svg_fonts.used_characters(svg) == "a"

    def test_only_used_characters_are_kept(self):
        svg = svg_fonts.embed_fonts(render("abc"))

        from fontTools.ttLib import TTFont

        codepoints = set(TTFont(io.BytesIO(embedded_fonts(svg)[0])).getBestCmap())
        assert codepoints >= set(map(ord, "abc"))
        assert ord("z") not in codepoints


class TestUsesBold:
    """Tests for svg_fonts.uses_bold()."""

    def test_bold_terminal_text(self):
        assert svg_fonts.uses_bold(render("hello", style="bold")) is True

    def test_plain_terminal_text(self):
        assert svg_fonts.uses_bold(render("hello")) is False

    def test_the_bold_window_title_does_not_count(self):
        """Rich's template always sets the title in bold Arial, which needs no embedding."""
        assert "font-weight: bold" in render("hello")
        assert svg_fonts.uses_bold(render("hello")) is False
