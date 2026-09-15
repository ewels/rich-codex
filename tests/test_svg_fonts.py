import base64
import html
import io
import logging
import re

import pytest
from rich._export_format import CONSOLE_SVG_FORMAT
from rich.console import Console

from rich_codex import svg_fonts

DATA_URI_RE = re.compile(r'src: url\("data:font/woff2;base64,([A-Za-z0-9+/=]+)"\)')


def render(text="hello world", title="", **kwargs):
    """Render some text to an SVG the way RichImg does, without touching the filesystem.

    Rich titles the window 'Rich' by default; rich-codex passes no title unless one is set,
    which is the usual case, so that is what this defaults to as well.
    """
    console = Console(record=True, file=io.StringIO(), width=40, force_terminal=True)
    console.print(text, **kwargs)
    return console.export_svg(title=title, unique_id="test")


def embedded_fonts(svg):
    """Pull the embedded WOFF2 fonts back out of an SVG."""
    return [base64.b64decode(match) for match in DATA_URI_RE.findall(svg)]


def after_the_font_rules(svg):
    """Everything past the last '@font-face' rule, which embedding shouldn't touch."""
    return svg[list(svg_fonts.FONT_FACE_RE.finditer(svg))[-1].end() :]


def families(svg):
    """The font families named by the SVG's '@font-face' rules, in order."""
    return re.findall(r'@font-face \{\s*font-family: "([^"]+)"', svg)


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

        assert after_the_font_rules(embedded) == after_the_font_rules(svg)
        assert embedded.count("<!--") == svg.count("<!--") + 1

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


class TestTitleFont:
    """Rich sets the window title in Arial, which can't be bundled and isn't everywhere."""

    def test_no_title_means_no_title_font(self):
        svg = svg_fonts.embed_fonts(render())
        assert families(svg) == ["Fira Code"]
        assert svg_fonts.TITLE_FAMILY_RULE in svg

    def test_a_title_gets_inter(self):
        svg = svg_fonts.embed_fonts(render(title="My Title"))
        assert families(svg) == ["Fira Code", "Inter"]

    def test_the_title_rule_asks_for_the_embedded_font(self):
        svg = svg_fonts.embed_fonts(render(title="My Title"))
        assert svg_fonts.EMBEDDED_TITLE_FAMILY_RULE in svg
        assert svg_fonts.TITLE_FAMILY_RULE not in svg

    def test_arial_is_kept_as_a_fallback(self):
        """Anything that can't use the embedded face should land where it used to."""
        assert "arial" in svg_fonts.EMBEDDED_TITLE_FAMILY_RULE

    def test_only_the_title_characters_are_embedded(self):
        from fontTools.ttLib import TTFont

        svg = svg_fonts.embed_fonts(render("zzz", title="abc"))
        inter = TTFont(io.BytesIO(embedded_fonts(svg)[-1]))
        codepoints = set(inter.getBestCmap())
        assert codepoints >= set(map(ord, "abc"))
        assert ord("z") not in codepoints

    def test_the_title_licence_notice_is_added(self):
        svg = svg_fonts.embed_fonts(render(title="My Title"))
        assert "The Inter Project Authors" in svg
        assert "The Fira Code Project Authors" in svg

    def test_a_missing_title_rule_is_an_error(self):
        svg = render(title="My Title").replace(svg_fonts.TITLE_FAMILY_RULE, "font-family: helvetica;", 1)
        with pytest.raises(svg_fonts.FontEmbedError, match="window title"):
            svg_fonts.embed_fonts(svg)

    def test_nothing_else_in_the_svg_changes(self):
        svg = render(title="My Title")
        embedded = svg_fonts.embed_fonts(svg)
        assert after_the_font_rules(embedded) == after_the_font_rules(svg).replace(
            svg_fonts.TITLE_FAMILY_RULE, svg_fonts.EMBEDDED_TITLE_FAMILY_RULE, 1
        )


class TestTitleCharacters:
    """Tests for svg_fonts.title_characters()."""

    def test_no_title(self):
        assert svg_fonts.title_characters(render()) == ""

    def test_a_title(self):
        assert svg_fonts.title_characters(render(title="cab")) == "abc"

    def test_terminal_text_is_ignored(self):
        svg = '<text class="x-title">ab</text><text class="x-r1">zzz</text>'
        assert svg_fonts.title_characters(svg) == "ab"


class TestUnrenderableCharacters:
    """Tests for svg_fonts.unrenderable_characters()."""

    def test_ordinary_text_is_all_covered(self):
        assert svg_fonts.unrenderable_characters(render("hello world 123")) == ""

    def test_emoji_are_not(self):
        assert svg_fonts.unrenderable_characters(render("done \u2728\U0001f92b")) == "\u2728\U0001f92b"

    def test_a_title_counts_too(self):
        assert svg_fonts.unrenderable_characters(render("plain", title="done \u2728")) == "\u2728"

    def test_whitespace_is_not_reported(self):
        """Rich's text elements carry newlines, which have no glyph to miss."""
        assert "\n" not in svg_fonts.unrenderable_characters(render("two\nlines"))


class TestSplitUnrenderableText:
    """Tests for svg_fonts.split_unrenderable_text().

    resvg chooses a fallback font per '<text>' element and draws the whole element in it,
    so a character it has to fall back for needs an element of its own.
    """

    def element(self, content, x=0.0, text_length=None):
        length = len(html.unescape(content)) * 12.2 if text_length is None else text_length
        return (
            f'<text class="t-r1" x="{x:g}" y="20" textLength="{length:g}" clip-path="url(#t-line-0)">{content}</text>'
        )

    def elements(self, svg):
        return re.findall(r"<text\b[^>]*>.*?</text>", svg, re.DOTALL)

    def test_text_the_fonts_cover_is_untouched(self):
        svg = self.element("hello")
        assert svg_fonts.split_unrenderable_text(svg) == svg

    def test_a_whole_rendered_svg_is_untouched(self):
        svg = render("hello world")
        assert svg_fonts.split_unrenderable_text(svg) == svg

    def test_an_emoji_gets_an_element_of_its_own(self):
        split = svg_fonts.split_unrenderable_text(self.element("ab\u2728cd"))
        assert [re.search(r">(.*)</text>", e).group(1) for e in self.elements(split)] == ["ab", "\u2728", "cd"]

    def test_the_pieces_land_where_the_characters_were(self):
        split = svg_fonts.split_unrenderable_text(self.element("ab\u2728cd", x=10))
        positions = [float(re.search(r'x="([\d.]+)"', e).group(1)) for e in self.elements(split)]
        lengths = [float(re.search(r'textLength="([\d.]+)"', e).group(1)) for e in self.elements(split)]
        assert positions == pytest.approx([10, 10 + 2 * 12.2, 10 + 3 * 12.2], abs=0.01)
        assert lengths == pytest.approx([2 * 12.2, 12.2, 2 * 12.2], abs=0.01)

    def test_consecutive_unrenderable_characters_share_an_element(self):
        split = svg_fonts.split_unrenderable_text(self.element("a\u2728\U0001f92bb"))
        assert len(self.elements(split)) == 3

    def test_spaces_do_not_split_anything(self):
        """Whitespace has no glyph to miss, so it stays with the text around it."""
        split = svg_fonts.split_unrenderable_text(self.element("a&#160;b"))
        assert split == self.element("a&#160;b")

    def test_the_fallback_family_goes_only_on_what_needs_it(self):
        split = svg_fonts.split_unrenderable_text(self.element("ab\u2728cd"), "Noto Color Emoji")
        styled = [e for e in self.elements(split) if "font-family" in e]
        assert len(styled) == 1
        assert "Noto Color Emoji" in styled[0]
        assert "\u2728" in styled[0]

    def test_no_fallback_family_means_no_style_attribute(self):
        split = svg_fonts.split_unrenderable_text(self.element("ab\u2728cd"))
        assert "font-family" not in split

    def test_the_text_survives_the_round_trip(self):
        original = "a&lt;b&#160;\u2728&amp;c"
        split = svg_fonts.split_unrenderable_text(self.element(original))
        rejoined = "".join(re.search(r">(.*)</text>", e).group(1) for e in self.elements(split))
        assert html.unescape(rejoined) == html.unescape(original)

    def test_an_element_without_a_position_is_left_alone(self):
        """The window title is centred rather than placed, so its pieces can't be put back."""
        svg = '<text class="t-title" text-anchor="middle" x="50" y="27">done \u2728</text>'
        assert svg_fonts.split_unrenderable_text(svg) == svg

    def test_an_empty_element_is_left_alone(self):
        svg = self.element("", text_length=0)
        assert svg_fonts.split_unrenderable_text(svg) == svg


class TestHasEmbeddedFonts:
    """Tests for svg_fonts.has_embedded_fonts()."""

    def test_an_embedded_svg(self):
        assert svg_fonts.has_embedded_fonts(svg_fonts.embed_fonts(render())) is True

    def test_richs_own_output(self):
        assert svg_fonts.has_embedded_fonts(render()) is False


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
