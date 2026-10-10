# Terminals, Unicode and embedding

Character tables and platform facts for art that uses more than 7-bit
ASCII, uses colour, or has to live inside source code.

## Contents

- Character width classes
- Box drawing
- Block elements and bars
- Braille
- Symbols and arrows
- ANSI escape codes
- Terminal and platform caveats
- Embedding art in code and documents

## Character width classes

Column alignment depends on every character being exactly one cell.

| Class                         | Examples                       | Cells | Safe in art?                                |
| ----------------------------- | ------------------------------ | ----- | ------------------------------------------- |
| ASCII printable               | `A - / # @`                    | 1     | Always                                      |
| Latin-1 / Latin ext           | `é ñ ß ø`                      | 1     | Yes, if precomposed (one code point)        |
| Combining marks               | `e` + U+0301                   | 0     | No: width differs by terminal               |
| Box drawing, block elements   | `─ │ ┌ █ ▀ ░`                  | 1 (A) | Yes; 2 cells in CJK-locale terminals        |
| Geometric shapes, arrows      | `● ■ ▲ → ★`                    | 1 (A) | Mostly; some fonts draw them wider          |
| Braille patterns              | `⠁ ⣿`                          | 1     | Yes, where the font has them                |
| East Asian wide/fullwidth     | `日 本 Ａ`                       | 2     | Only in art designed on a 2-cell grid       |
| Emoji                         | `🚀 😀 ❤️`                      | 2*    | No: width and VS16 handling vary wildly     |
| Zero-width / format           | ZWJ, ZWSP, VS15/16, BOM        | 0     | No                                          |

`(A)` is Unicode's "ambiguous" width. `scripts/asciiart.py check` reports
all of these.

## Box drawing

```text
light      ┌ ┬ ┐   ├ ┼ ┤   └ ┴ ┘   ─ │
rounded    ╭ ─ ╮   │   │   ╰ ─ ╯
heavy      ┏ ┳ ┓   ┣ ╋ ┫   ┗ ┻ ┛   ━ ┃
double     ╔ ╦ ╗   ╠ ╬ ╣   ╚ ╩ ╝   ═ ║
mixed      ╒ ╤ ╕   ╞ ╪ ╡   ╘ ╧ ╛   (single vertical, double horizontal)
           ╓ ╥ ╖   ╟ ╫ ╢   ╙ ╨ ╜   (double vertical, single horizontal)
dashed     ┄ ┅ ┆ ┇ ┈ ┉ ┊ ┋ ╌ ╍ ╎ ╏
light/heavy joins   ┍ ┑ ┕ ┙ ┎ ┒ ┖ ┚ ┝ ┥ ┞ ┦ ┯ ┷ ┿
diagonals  ╱ ╲ ╳
```

Mixing weights on one box looks like a rendering bug unless it is a
deliberate emphasis (heavy top edge as a header, say). Rounded corners
only exist in the light weight.

## Block elements and bars

```text
full / halves    █ ▀ ▄ ▌ ▐
shades           ░ ▒ ▓        (light -> dark; background shows through ░)
lower eighths    ▁ ▂ ▃ ▄ ▅ ▆ ▇ █   vertical bars, sparklines
left eighths     ▏ ▎ ▍ ▌ ▋ ▊ ▉ █   horizontal progress bars
quadrants        ▖ ▗ ▘ ▝ ▚ ▞ ▙ ▛ ▜ ▟
```

Half blocks double vertical resolution: with `▀` and a foreground colour
for the top half plus a background colour for the bottom half, each cell
shows two pixels (`asciiart.py image --mode half --color`). Without colour,
`▀ ▄ █` and space give a 1×2 monochrome grid.

## Braille

U+2800 to U+28FF: 256 patterns of a 2-column by 4-row dot grid, so one
cell holds 8 monochrome pixels. Dot bit values:

```text
col:  0    1
row0  0x01 0x08
row1  0x02 0x10
row2  0x04 0x20
row3  0x40 0x80      character = chr(0x2800 + sum of set bits)
```

Braille art (`asciiart.py image --mode braille`) is the sharpest
monochrome rendering but needs a font with the block (most do; the Linux
text console does not) and reads as noise when printed very small. The
blank pattern `⠀` (U+2800) is a visible-width space; use a real space at
line ends.

## Symbols and arrows

```text
geometric   ■ □ ▪ ▫ ▲ △ ▼ ▽ ◆ ◇ ● ○ ◎ ◉ ◐ ◑ ◢ ◣ ◤ ◥ ★ ☆
arrows      ← ↑ → ↓ ↔ ↕ ↖ ↗ ↘ ↙ ⇐ ⇒ ⇑ ⇓ ⇔ ➜ ➔ ▶ ◀
bullets     • · ∙ ◦ ‣ ▸ ▹
marks       ✓ ✔ ✗ ✘ ⚠ ℹ … — – ‖ § ¶ ° ± × ÷ ∞ ≈ ≠ ≤ ≥ √
```

Prefer ASCII arrows (`->`, `=>`, `<-`, `^`, `v`) in anything that may be
viewed in a programming font with ligatures or pasted into a chat client.

## ANSI escape codes

All sequences start with ESC `[` (`\x1b[`, `\033[`, `\e[`) and end with a
letter. Colour and style use `m`:

| Sequence              | Effect                                          |
| --------------------- | ----------------------------------------------- |
| `0`                   | reset everything (always end coloured output)   |
| `1` `2` `3` `4` `7`   | bold, dim, italic, underline, reverse video     |
| `30`-`37`             | foreground: black red green yellow blue magenta cyan white |
| `90`-`97`             | bright foreground, same order                   |
| `40`-`47`, `100`-`107`| background, same order                          |
| `38;5;N` / `48;5;N`   | 256-colour foreground / background (N 0-255)    |
| `38;2;R;G;B` / `48;2;R;G;B` | truecolor foreground / background         |

Combine with `;`: `\x1b[1;32m` is bold green. Cursor control uses other
letters: `\x1b[H` home, `\x1b[2J` clear screen, `\x1b[NA` up N rows,
`\x1b[NB` down, `\x1b[NC` right, `\x1b[ND` left, `\x1b[?25l` / `\x1b[?25h`
hide / show cursor, `\x1b[s` / `\x1b[u` save / restore position.

Rules for shipping coloured art in a program:

- Emit colour only when stdout is a TTY, `NO_COLOR` is unset and `TERM` is
  not `dumb`; honour `FORCE_COLOR` for CI logs. Provide a plain fallback.
- Reset at the end of every line, not just the piece, so a scrollback cut
  or a pager does not bleed colour.
- Truecolor is safe in every modern terminal emulator (Windows Terminal,
  iTerm2, GNOME Terminal, kitty, Alacritty, VS Code) but not macOS
  Terminal.app, which approximates with 256 colours.
- Colour is extra, not structure: the art must still read in monochrome.

## Terminal and platform caveats

- **Windows.** Windows Terminal handles UTF-8, VT sequences and truecolor.
  Legacy conhost (`cmd.exe` window) needs virtual-terminal processing
  enabled (in Python, `os.system("")` or `colorama`) and a UTF-8 code page
  (`chcp 65001`); Python 3.6+ writes UTF-8 to the console API itself.
  Default raster fonts lack most block and box glyphs; Cascadia Mono and
  Consolas have them.
- **macOS Terminal.app** has an "Unicode East Asian Ambiguous characters
  are wide" option that turns box drawing into 2-cell glyphs; iTerm2 has
  the same switch. If a user reports broken boxes on a Mac, ask about it.
- **Linux virtual console** (no X) has a 256- or 512-glyph font: ASCII and
  light box drawing only; no braille, few blocks.
- **tmux / screen** apply their own width tables; old versions mis-measure
  emoji and some symbols. ASCII and box drawing are safe.
- **CI logs and web viewers** (GitHub Actions, GitLab) render ANSI colour
  but collapse nothing; log line length limits can wrap wide art.
- **Editors and IDE terminals** often use ligature fonts (Fira Code,
  JetBrains Mono, Cascadia Code with ligatures on): `->`, `<-`, `=>`, `||`,
  `::`, `--`, `==`, `!=`, `<>`, `//` and `/*` merge. Space them or avoid.
- **Proportional fonts** (chat apps, email, web pages without `<pre>`)
  destroy alignment; always fence or wrap in `<pre>`.
- **Line length.** 80 columns is the universal safe width; 72 for art in
  code comments and commit messages; 40 reads on a phone terminal.

## Embedding art in code and documents

`\` is the most common stroke and the most common escape character, so
pick a literal form that does not interpret it.

| Language / format | Safe form                                            | Watch for                                            |
| ----------------- | ---------------------------------------------------- | ---------------------------------------------------- |
| Python            | `ART = r"""..."""`; `textwrap.dedent` for indentation | A raw string cannot end in `\`; put a newline last    |
| JavaScript / TS   | `String.raw\`...\``                                   | `${` still interpolates; a plain template literal escapes `\` |
| Go                | backtick raw string                                   | Cannot contain a backtick                            |
| Rust              | `r#"..."#`                                            | Choose enough `#` to exceed any `"#` in the art      |
| C / C++           | `R"(...)"`                                            | Pick a delimiter: `R"art(...)art"` if `)"` appears   |
| Java 15+          | text block `"""`                                      | Trailing spaces are stripped; use `\s` to keep them  |
| C# / .NET         | `@"..."` or raw `"""..."""` (C# 11)                   | `"` doubles to `""` in verbatim strings              |
| Shell             | `cat <<'EOF' ... EOF` with the quoted delimiter       | Unquoted `EOF` expands `$` and backslashes            |
| YAML              | block scalar `art: \|`                                 | Keep the indentation uniform                         |
| JSON              | no raw form: escape `\` as `\\` and `"` as `\"`       | Generate it from a file rather than by hand          |
| Markdown          | fenced block with `text`                              | Outside fences, `*`, `_`, `#`, `>` and spaces are markup |
| HTML              | `<pre>` (and escape `<`, `>`, `&`)                    | CSS `white-space: pre; font-family: monospace`       |
| CLI `--help`      | argparse `RawDescriptionHelpFormatter`, click `\b`     | Default formatters reflow paragraphs                 |
| Source comments   | one comment leader per row, art starting at a fixed column | Tabs inserted by editors; keep rows under 72 cols |

Centring in a live terminal: `shutil.get_terminal_size().columns` in
Python, `tput cols` in shell; pad each row by `(cols - width) // 2`, and
fall back to no padding when the width is unknown or smaller than the art.
