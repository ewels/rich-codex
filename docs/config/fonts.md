## Embedding the terminal font

rich-codex renders terminal text in [Fira Code](https://github.com/tonsky/FiraCode). Rich
does not put the font in the SVG. It writes a `@font-face` rule that points at a local copy
of the font, with a CDN URL as a backup.

That works when you open the file in a browser tab, but not where most people see these
images. Markdown renderers put images in an `<img>` tag, and an SVG inside an `<img>` tag
runs in secure static mode. Secure static mode blocks every external request, whatever the
CSS asks for. GitHub also serves images through its camo proxy, so the CDN URL never loads.

Only the local copy can resolve. The image is therefore correct on a machine that has Fira
Code installed, and wrong everywhere else, because the browser picks a different monospace
font. Rich positions each chunk of text at an absolute `x` coordinate, calculated from the
character width it expects. Another font has different widths, so the glyphs drift inside
each chunk and the box-drawing characters no longer join up.

rich-codex writes the font into the SVG instead, as a base64 data URI. A data URI is not an
external request, so `<img>` mode can use it, and the image renders the same way for every
reader. Only the characters that the image uses are embedded. The bold weight is left out
if the image contains no bold text.

Rich sets the window title in Arial. Arial has the same problem, and it cannot be bundled
because it is proprietary. rich-codex embeds [Inter](https://rsms.me/inter/) for the title
instead and rewrites the title rule to ask for it. The rule keeps `arial, sans-serif` after
it, for anything that cannot use the embedded font.

Embedding is on by default. To turn it off and go back to Rich's linked font, use
`--no-embed-font` / `$EMBED_FONT` / `embed_font` (CLI, env var, action/config):

```yaml
embed_font: false
```

The two images below are the same command, rendered both ways. They look identical if you
have Fira Code installed. If you do not, only the first one still uses it. The ligatures
are the clearest sign, with `->` and `!=` drawn as `→` and `≠`.

<!-- prettier-ignore-start -->
Default:

```markdown
<!-- RICH-CODEX { terminal_width: 70, hide_command: true } -->
![`rich --print "[bold]Fira Code ligatures[/]: -> != >= ... and box drawing" --panel rounded --force-terminal`](../img/embed-font.svg)
```
![rich --print](../img/embed-font.svg)

With `embed_font` set to `false`:

```markdown
<!-- RICH-CODEX { terminal_width: 70, hide_command: true, embed_font: false } -->
![`rich --print "[bold]Fira Code ligatures[/]: -> != >= ... and box drawing" --panel rounded --force-terminal`](../img/embed-font-off.svg)
```
![rich --print](../img/embed-font-off.svg)
<!-- prettier-ignore-end -->

How much the second image degrades depends on the font that the browser substitutes. A
substitute with the same character width looks wrong but stays aligned. A substitute with a
different width pulls the columns out of line and opens gaps between the box-drawing
characters.

<!-- prettier-ignore-start -->
!!! note
    PNG files are rasterised by [resvg](https://github.com/linebender/resvg). No rasteriser
    supports `@font-face`, so none of them can use an embedded font. They all read fonts
    from the machine that renders the image. rich-codex therefore passes resvg its own
    copies of Fira Code, Inter and Noto Color Emoji, and tells resvg to ignore the fonts on
    the machine. The same output then rasterises the same way anywhere. This matters in CI,
    where any change to a file is another commit.
<!-- prettier-ignore-end -->

### Emoji, and anything else the fonts do not have

No monospace font includes emoji, and Rich output often contains them, so rich-codex
bundles [Noto Color Emoji](https://github.com/googlefonts/noto-emoji) as well and draws
them in colour. The three fonts together cover Latin, Greek, Cyrillic, box drawing and
emoji.

Characters outside that set, such as CJK, are blank in PNG output. rich-codex prints a
warning when it finds one:

```
No bundled font can draw 漢 字, so they will be blank in PNG output.
Set '--png-fallback-font' to draw them with a font from this machine.
```

To draw them, set `--png-fallback-font` / `$PNG_FALLBACK_FONT` / `png_fallback_font` (CLI,
env var, action/config) to a font family that is installed on the machine that generates
the images:

```yaml
png_fallback_font: Noto Sans CJK JP
```

This option makes a PNG depend on the machine again, which is why it is off by default.

<!-- prettier-ignore-start -->
!!! note
    resvg substitutes a font for each character that it cannot draw, then keeps that
    substitute for the characters that follow, for as long as the substitute can draw them.
    A substitute that contains letters would redraw the rest of the line. To prevent that,
    rich-codex moves those characters into a `<text>` element of their own before it
    rasterises the image. This applies only to the copy that goes to the rasteriser. The
    SVG that rich-codex writes is unchanged, and browsers handle the same problem correctly
    on their own.
<!-- prettier-ignore-end -->

### Double-width characters

Rich moves along each line in terminal cells, and an emoji or a CJK character fills two
cells. Rich sizes the SVG's `textLength` by counting characters, so an element that holds
one of these characters is a cell too narrow. Browsers obey `textLength`, so the glyph used
to overlap the text after it and the box drawing stopped lining up. rich-codex corrects the
value, in SVG and PNG output alike.

## File size

Embedding adds 10 KB to 30 KB per image. The exact figure depends on how many different
characters the image uses, and on whether any of them are bold. A window title adds about
6 KB more. An image without a title does not include Inter at all.

| Image                                     | `embed_font: false` |  Default |
| ----------------------------------------- | ------------------: | -------: |
| The panel above (31 characters, bold)     |              3.7 KB |  30.1 KB |
| `rich-codex --help` (70 characters, bold) |             73.0 KB | 101.3 KB |

Turn embedding off if you want smaller files and know that your readers have Fira Code, or
if you only use the PNG output.

<!-- prettier-ignore-start -->
!!! tip
    Ligatures are kept, so `!=` and `->` render as `≠` and `→`, the same as in a terminal
    that uses Fira Code. They account for most of the size. Fira Code has several hundred
    of them, and keeping them roughly doubles the embedded subset.
<!-- prettier-ignore-end -->

## Reproducibility

The same command with the same output always produces the same file, so running rich-codex
again in CI does not change images whose content has not changed.

Different `fonttools` releases subset a font differently, so an upgrade changes what
rich-codex would generate. It does not rewrite the saved images. rich-codex ignores the
embedded font when it compares a new image against the saved one, and replaces the file
only when the content has changed. Until then the image keeps the subset that it was built
with. That comparison is also why [`min_pct_diff` and
`skip_change_regex`](ignoring_changes.md) measure the command output rather than the font.

## Licence

rich-codex bundles three fonts: [Fira Code](https://github.com/tonsky/FiraCode),
[Inter](https://github.com/rsms/inter) and
[Noto Color Emoji](https://github.com/googlefonts/noto-emoji). All three use the
[SIL Open Font License, Version 1.1](https://scripts.sil.org/OFL), which permits embedding.
Each subset keeps the copyright and licence notice of its font in the `name` table, and
rich-codex repeats the notice in a comment near the top of every SVG that carries a font.
The full licence texts are in the `fonts` directory of the package.

The fonts account for most of the install size. The package is about 3 MB, and would be
about 0.5 MB without them.
