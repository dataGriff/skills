---
name: ascii-art
description: >-
  Draw high-quality ASCII and Unicode text art for terminals: hand-drawn
  pictures, mascots, logos, scenes and diagrams, big-letter banners, boxes and
  frames, exact geometric shapes, and image-to-text conversion (character
  ramp, braille, half-block, ANSI colour), with a linter that catches ragged
  widths, tabs and double-width characters before the art is shown. Use when
  the user asks for ASCII art or text art, a terminal or CLI banner, splash
  screen or MOTD, a figlet-style title, a logo or mascot in characters, a
  drawing for a README or code comment, to convert an image or photo to
  ASCII, braille or ANSI art, or to "draw" anything with characters - even a
  casual "draw me a cat" or "make a banner for my tool".
---

# ASCII art

Good terminal art reads at a glance, lines up in every monospace font, and
fits the space it will be shown in. Most failures are mechanical rather than
artistic: a row one character too long, a tab, an emoji that is two cells
wide, a circle drawn as tall as it is wide. The rules below prevent those,
and `scripts/asciiart.py` does the parts that reward exactness: lettering,
frames, curves, image conversion and measuring.

## Workflow

1. **Pin the brief before drawing.** Subject and mood; the box it must fit
   (default 80 columns and about 20 rows; much smaller inside a code
   comment, a log line or a chat reply); the character set (7-bit ASCII
   works everywhere, Unicode box-drawing and block elements look sharper but
   need UTF-8 and a decent font); where it will live (terminal output,
   README, source comment, MOTD, `--help` text) and whether ANSI colour is
   welcome. When the user did not say, choose ASCII, at most 80 columns, no
   colour, and state that choice in one line.
2. **Pick the method** from the table below. Hand-draw pictures; generate
   anything geometric or typographic; convert anything that already exists
   as an image. Mixed pieces are normal: a generated banner with a
   hand-drawn mascot beside it.
3. **Build on a fixed grid.** Decide the width first, draw row by row, and
   keep every row within it. Terminal cells are about twice as tall as they
   are wide, so draw everything about twice as wide as it is high.
4. **Verify before you show it.** When the piece is more than a few rows or
   will be committed or shipped, save it to a file and run
   `python3 scripts/asciiart.py check art.txt [--max-width N] [--unicode]`.
   Fix every ERROR, read every note, then look at the whole piece once more
   as a picture and fix what reads wrong.
5. **Deliver it in a form that survives transport.** In chat and Markdown,
   put it in a fenced code block (` ```text `) so spaces are preserved. In
   source, prefer raw strings or heredocs with a quoted delimiter, because
   `\` is the most common stroke and gets eaten by escaping. Never emit
   tabs or trailing spaces.

| You want                                                   | Do this                                                                                                    |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| A picture: animal, face, object, mascot, logo mark, scene  | Hand-draw with the craft rules below. Open `references/gallery.md` when you want a proven starting shape.  |
| Big text: banner, title, splash, section header            | `asciiart.py banner TEXT [--half] [--fill █]`, or `--font standard\|slant\|big` when figlet/pyfiglet is installed. Never hand-letter more than two or three characters. |
| Frame, panel, callout, table border                        | `asciiart.py box --style ascii\|dots\|single\|rounded\|double\|heavy --title X [--align center]`              |
| Circle, ellipse, diamond, triangle, straight line          | `asciiart.py shape circle 4` (and `ellipse`, `rect`, `diamond`, `triangle`, `line`); paste into the piece. |
| An existing image or photo                                 | `asciiart.py image photo.png --width 80 [--mode braille\|half] [--color] [--bg light]`                       |
| A symmetric figure                                         | Draw the left half, then `asciiart.py mirror --append [--overlap]` (it swaps `/ \ ( ) [ ] { } < >`).       |
| Several parts composed exactly                             | `from asciiart import Canvas, ellipse, line, rect, banner` and `blit` parts at coordinates (see below).   |
| Boxes-and-arrows diagram                                   | Generate the boxes, place them on one grid, connect with `-->`, `<--`, `|`, `v`, `^`; keep boxes in a row the same height. |

## Hand-drawing craft

### Lay out the grid

- Fix width, then height. For anything wider than about 30 columns print a
  ruler with `asciiart.py grid 60` and draw underneath it; counting by eye
  is how rows drift.
- Draw in passes over the whole figure: silhouette, then main interior
  lines, then details and shading, then tidy. Finishing one row perfectly
  before starting the next produces shapes that do not meet.
- Compensate for cell shape. A circle needs about twice as many columns as
  rows. A `/` that steps one column per row looks steeper than 45 degrees;
  two columns per row looks like 45 degrees. Vertical proportions in a
  reference photo must be halved.
- For symmetric subjects draw one half and mirror it; hand-mirroring is
  where `/` and `\` get swapped and widths slip.

### Strokes: pick the right character for the job

| Direction or feature                 | Characters                                                   |
| ------------------------------------ | ------------------------------------------------------------ |
| Horizontal line                      | `-` (middle of the cell), `_` (bottom), `=` or `~` for weight or water |
| Vertical line                        | `\|`; `!` or `:` for a thin or dotted one                    |
| Steep diagonal                       | `/` `\`                                                       |
| Shallow slope                        | Stepped runs: `.-'` rising, `'-.` falling, `__.-'` very flat |
| Curve: sides                         | `(` `)` for small curves, `\|` for large                      |
| Curve: top and bottom                | Top shoulders `.-"""-.`, bottom `'-...-'` or `'---'`         |
| Corners                              | `+` for square boxes, `.` and `'` for rounded ones           |
| Dots, eyes, joints                   | `.` `o` `O` `0` `@` `*`; `^` happy eyes, `-` closed, `x` out cold |
| Mouths                               | `_` `-` `v` `w` `o` `~` `u`                                   |
| Shading, light to dark               | ` .:-=+*#%@` (ASCII) or ` ░▒▓█` (Unicode)                    |
| Textures                             | `~` water, `^` or `"` grass, `*` stars, `%` `&` foliage, `#` brick |

The one rule that most improves hand-drawn curves: `.` sits at the
**bottom** of its cell and `'` at the **top**. Use `.` where a line comes
down and turns, `'` where it goes up and turns. That is why a circle's top
is `.-.` and its bottom `'-'`, and why a falling slope is `'-.` while a
rising one is `.-'`.

```text
      .-"""-.          .-------.         .
     /       \         |       |        / \
    |  o   o  |        |   o   |       /   \
     \   ^   /         |       |      '-----'
      '-...-'          '-------'
```

### Keep it consistent

- One line weight per outline. Thin strokes (`- | / \ . '`) or heavy ones
  (`= # | /`), not both on the same edge.
- Density is depth. `#` next to `.` reads as near versus far; use heavy
  characters deliberately for shadow and mass, never for an outline that
  should be light.
- Do not force a character into a role it does not fit: `|` is not a
  diagonal, `-` is not a curve, `O` in an outline reads as a letter.
- Stray characters read as dirt. Clear the interior of anything that is
  not part of the picture, and trim trailing spaces.
- Letters inside art (labels, a name on a sign) must not touch the
  strokes; give them one empty cell on each side.

### Faces and characters

Eyes first: they decide the expression and the viewer looks there first.
Two eyes should sit on the same row, symmetric about the centre column,
with the mouth centred beneath. Small changes carry the mood: `o o` neutral,
`^ ^` happy, `- -` asleep, `> <` angry, `@ @` startled, `O o` quizzical.
For animals, decide the one feature that identifies the species (cat ears
`/\_/\`, rabbit ears `(\_/)`, owl brows `{o,o}`, fish tail `><`) and build
the rest around it.

## Banners and lettering

Hand-lettering fails because every letter must share the same baseline,
height and stroke rules across the whole word. Generate instead:

```bash
python3 scripts/asciiart.py banner "FORGE"            # 5-row block letters, 2 cells per pixel
python3 scripts/asciiart.py banner "FORGE" --half     # half-block glyphs ▀▄█: 3 rows tall
python3 scripts/asciiart.py banner "FORGE" --fill █   # solid blocks instead of #
python3 scripts/asciiart.py banner "FORGE" --font slant   # classic figlet look, if installed
python3 scripts/asciiart.py banner "v2.1" | python3 scripts/asciiart.py box --style rounded
```

For a splash screen, pair the word with a tagline one row below it,
left-aligned to the first letter or centred under the whole word, and leave
one blank row of air above and below inside any frame. Keep the total under
the width of the narrowest terminal that will show it (80 columns is safe,
60 safer for a tool people run on phones over SSH).

## Converting images

`asciiart.py image PATH` maps luminance to characters at an exact width,
with aspect correction and auto-contrast, when Pillow is importable.

- `--width` is the budget; height follows from the image's aspect ratio
  and `--aspect 0.5` (change it for very tall or wide fonts).
- Default assumes a dark terminal, where ink is light: bright pixels get
  dense characters. Pass `--bg light` for paper, a light theme or a README.
- `--mode ramp` (default) is pure ASCII with the ` .:-=+*#%@` ramp; `--ramp
  long` gives 70 levels, `--ramp blocks` uses ` ░▒▓█`. `--mode braille`
  packs 2×4 dots per cell with dithering for the sharpest monochrome
  result; `--mode half --color` gives two colour pixels per cell with
  ANSI truecolor and is the best-looking option for a live terminal.
- Colour output is for terminals only: it is escape codes, so never put it
  in a file meant for a README or a code comment. The linter measures
  through them and reports how many it ignored; strip them with
  `sed 's/\x1b\[[0-9;]*m//g'` if a plain copy is needed.
- Photos need subjects with strong silhouettes; a busy image at 80 columns
  is mush. Crop to the subject first, or raise the width and tell the user
  it needs a wide terminal.

## Composing scenes in Python

When a piece has several exact parts (a frame, a banner, a shape, hand-drawn
sprites), place them on one canvas instead of hand-merging strings:

```python
import sys; sys.path.insert(0, "skills/ascii-art/scripts")   # or the installed path
from asciiart import Canvas, banner, ellipse, line, rect

c = Canvas(60, 14)
rect(c, 0, 0, 60, 14, style="rounded")
c.blit(3, 2, banner("SOL", fill="#"))
ellipse(c, 46, 6, 8, 4)                 # a 17 x 9 sun: rx = 2 * ry looks round
line(c, 3, 11, 56, 11)                  # horizon
c.blit(20, 9, "  /\\_/\\\n ( o.o )", transparent=None)
print(c.render())
```

`blit` skips spaces by default so sprites overlap cleanly; pass
`transparent=None` to paste a solid block. Coordinates are column, row from
the top-left, and out-of-range writes are dropped, so parts can overhang
while you adjust.

## Pitfalls that ruin otherwise good art

- **Tabs.** Never. They expand to 8, 4 or 2 cells depending on the viewer.
- **Wide and zero-width characters.** Emoji, CJK ideographs, combining
  accents and variation selectors break column alignment; the linter flags
  them. Box-drawing and block characters are one cell in Western terminals
  but two in some CJK locales; mention that caveat when a user ships
  Unicode art widely.
- **Programming-font ligatures.** Fonts such as Fira Code merge `->`, `<=`,
  `||`, `::` and `--` into single glyphs, which shifts strokes. Break them
  with a space or choose other characters when the art will be viewed in
  an editor.
- **Markdown eating whitespace.** Outside a fenced block, Markdown collapses
  runs of spaces and interprets `*`, `_`, `#` and `>`; always fence.
- **Escaping.** In normal strings every `\` must be `\\`; `'` and `"` clash
  with quotes. Prefer raw strings (`r"""..."""`), Go backtick strings, or
  shell `cat <<'EOF'` with the quoted delimiter.
- **Right edges.** A frame, banner or table must be rectangular: equal
  width on every row, including the last. A drawing may be ragged.
- **Attribution.** Classic signed pieces (initials in a corner such as
  `jgs`) are other people's work; draw original art or credit the artist.

## References

- `references/gallery.md` - worked subjects (faces, animals, plants, scenes,
  objects, vehicles, diagrams, charts, dividers) drawn with these rules,
  plus composition and animation notes. Open it when you want a starting
  shape for a common subject or are drawing a scene with several elements.
- `references/terminals.md` - Unicode box-drawing, block, braille and arrow
  character tables; ANSI colour codes; terminal, font and platform caveats;
  how to embed art safely in each language and in Markdown. Open it when
  the piece uses Unicode or colour, must run on Windows, or is going into
  source code.
- `scripts/asciiart.py` - the toolkit used above (`check`, `grid`, `banner`,
  `box`, `shape`, `image`, `mirror`; importable `Canvas`). Run it with
  `--help` or read its docstring when you need an option not listed here.
