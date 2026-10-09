#!/usr/bin/env python3
"""ASCII art toolkit: exact-width primitives and a linter for terminal art.

Usage (run from anywhere; python3, stdlib only - `image` needs Pillow):

  asciiart.py check  [FILE] [--max-width N] [--unicode]   lint widths, tabs, wide chars
  asciiart.py grid   WIDTH [HEIGHT]                        column ruler (+ blank grid)
  asciiart.py banner TEXT [--fill CH] [--half] [--gap N]   block-letter text (5x5 font)
  asciiart.py banner TEXT --font slant [--width N]         via figlet / pyfiglet if installed
  asciiart.py box    [FILE] [--style S] [--title T] [--pad N] [--align left|center]
  asciiart.py shape  circle R | ellipse RX RY | rect W H | diamond W H |
                     triangle W [H] | line X0 Y0 X1 Y1   [--ch CH] [--fill CH]
  asciiart.py image  PATH [--width N] [--mode ramp|braille|half] [--color]
                     [--bg dark|light] [--ramp short|long|blocks|CHARS] [--invert]
                     [--aspect 0.5] [--dither] [--gamma G] [--no-contrast]
  asciiart.py mirror [FILE] [--append] [--overlap]        flip left<->right, swapping / \\ ( ) etc.

Every command writes to stdout, so pipe or redirect freely:
  asciiart.py banner FORGE --half | asciiart.py box --style rounded --title v1.2

Importable from Python (`from asciiart import Canvas, ellipse, line, ...`)
for composing scenes: build a Canvas, blit parts at exact coordinates,
then `print(canvas.render())`.
"""
from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
import unicodedata

# --------------------------------------------------------------------------
# Width measurement and linting
# --------------------------------------------------------------------------

# Characters that terminals do not render as exactly one cell.
_ZERO_WIDTH_CATEGORIES = {"Mn", "Me", "Cf"}  # combining marks, format chars (ZWJ, VS16...)


def char_cells(ch: str) -> int:
    """Terminal cells a character occupies: 0 (combining/format), 1 or 2 (wide)."""
    if ch == "\t":
        return 8  # never reliable; flagged separately
    if unicodedata.category(ch) in _ZERO_WIDTH_CATEGORIES:
        return 0
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    return 1


def display_width(s: str) -> int:
    return sum(char_cells(c) for c in s)


def is_ambiguous(ch: str) -> bool:
    """Ambiguous-width characters (box drawing, block elements, some symbols)
    are 1 cell in Western terminals but 2 in CJK-locale terminals."""
    return ord(ch) > 0x7F and unicodedata.east_asian_width(ch) == "A"


def lint(text: str, max_width: int = 80, allow_unicode: bool = False) -> tuple[list[str], list[str], dict]:
    """Return (errors, notes, stats) for a piece of art."""
    lines = text.split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    errors: list[str] = []
    notes: list[str] = []
    widths = [display_width(l) for l in lines]
    nonblank = [w for w, l in zip(widths, lines) if l.strip()]
    stats = {
        "lines": len(lines),
        "max_width": max(widths) if widths else 0,
        "min_width": min(nonblank) if nonblank else 0,
    }
    unsafe: dict[str, list[int]] = {}
    ambiguous = 0
    non_ascii = 0
    for n, line in enumerate(lines, 1):
        if "\t" in line:
            errors.append(f"line {n}: TAB character - expands differently everywhere; use spaces")
        if line != line.rstrip():
            notes.append(f"line {n}: trailing whitespace (invisible, breaks diffs; trim it)")
        for ch in line:
            if ord(ch) > 0x7F:
                non_ascii += 1
            cells = char_cells(ch)
            if ch != "\t" and cells != 1:
                unsafe.setdefault(f"U+{ord(ch):04X} {unicodedata.name(ch, '?')} ({cells} cells)", []).append(n)
            elif is_ambiguous(ch):
                ambiguous += 1
        if widths[n - 1] > max_width:
            errors.append(f"line {n}: {widths[n - 1]} columns, over the {max_width}-column limit")
    for desc, where in unsafe.items():
        shown = ", ".join(map(str, where[:6])) + (" ..." if len(where) > 6 else "")
        errors.append(f"{desc} on line(s) {shown} - not one cell wide; alignment will break")
    if non_ascii and not allow_unicode:
        errors.append(
            f"{non_ascii} non-ASCII character(s) but pure ASCII was requested "
            "(pass --unicode if box-drawing / block characters are intended)")
    if ambiguous:
        notes.append(
            f"{ambiguous} ambiguous-width character(s) (box drawing, block elements): "
            "fine in most terminals, double width in CJK-locale terminals")
    if nonblank and stats["max_width"] - stats["min_width"] > 0:
        notes.append(
            f"ragged right edge: widths {stats['min_width']}..{stats['max_width']} - "
            "normal for a drawing, wrong for a banner, box or table")
    return errors, notes, stats


def ruler(width: int) -> str:
    tens = "".join(str((i // 10) % 10) if i % 10 == 0 and i else " " for i in range(1, width + 1))
    units = "".join(str(i % 10) for i in range(1, width + 1))
    return tens + "\n" + units


# --------------------------------------------------------------------------
# Canvas and geometric primitives (importable)
# --------------------------------------------------------------------------

class Canvas:
    """Fixed-size character grid. Coordinates are (x=column, y=row), 0-based,
    origin top-left. Out-of-bounds writes are silently dropped so parts can
    overhang while you are composing."""

    def __init__(self, width: int, height: int, fill: str = " "):
        self.w, self.h = width, height
        self.cells = [[fill] * width for _ in range(height)]

    def put(self, x: int, y: int, ch: str) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.cells[y][x] = ch

    def get(self, x: int, y: int) -> str:
        return self.cells[y][x] if 0 <= x < self.w and 0 <= y < self.h else " "

    def text(self, x: int, y: int, s: str) -> None:
        for i, ch in enumerate(s):
            self.put(x + i, y, ch)

    def blit(self, x: int, y: int, art: str, transparent: str | None = " ") -> None:
        """Paste multi-line art with its top-left at (x, y). Cells equal to
        `transparent` are skipped so sprites can overlap."""
        for dy, row in enumerate(art.split("\n")):
            for dx, ch in enumerate(row):
                if transparent is not None and ch == transparent:
                    continue
                self.put(x + dx, y + dy, ch)

    def render(self, strip: bool = True) -> str:
        rows = ("".join(r) for r in self.cells)
        return "\n".join(r.rstrip() if strip else r for r in rows)

    def __str__(self) -> str:
        return self.render()


def _rnd(v: float) -> int:
    return int(math.floor(v + 0.5))


def line(c: Canvas, x0: int, y0: int, x1: int, y1: int, ch: str | None = None) -> None:
    """Straight line. With ch=None the strokes follow hand-drawing practice:
    `-` flat, `|` steep, `/` `\\` diagonals, and shallow slopes as stepped runs
    (`--.` / `'-.`) so no row ever shows a doubled stroke. With ch given,
    every cell on the line gets that character."""
    dx, dy = x1 - x0, y1 - y0
    if ch is not None:
        steps = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            c.put(_rnd(x0 + dx * i / steps), _rnd(y0 + dy * i / steps), ch)
        return
    if dy == 0:
        for x in range(min(x0, x1), max(x0, x1) + 1):
            c.put(x, y0, "-")
        return
    if abs(dy) * 1.5 >= abs(dx):  # steep: one cell per row
        stroke = "|" if abs(dy) > 2.5 * abs(dx) else ("\\" if dx * dy > 0 else "/")
        for i in range(abs(dy) + 1):
            y = y0 + (i if dy > 0 else -i)
            c.put(_rnd(x0 + dx * (y - y0) / dy), y, stroke)
        return
    # Shallow: one cell per column, grouped into horizontal runs per row.
    if x1 < x0:
        x0, y0, x1, y1 = x1, y1, x0, y0
        dx, dy = -dx, -dy
    rows: dict[int, list[int]] = {}
    for x in range(x0, x1 + 1):
        rows.setdefault(_rnd(y0 + dy * (x - x0) / dx), []).append(x)
    descending = dy > 0  # screen y grows downward, so this line falls to the right
    first_row, last_row = _rnd(y0), _rnd(y1)
    for y, xs in rows.items():
        if len(xs) == 1:
            c.put(xs[0], y, "\\" if descending else "/")
            continue
        for x in xs:
            if x == xs[0]:
                m = "-" if y == first_row else ("'" if descending else ".")
            elif x == xs[-1]:
                m = "-" if y == last_row else ("." if descending else "'")
            else:
                m = "-"
            c.put(x, y, m)


BOX_STYLES = {
    # name: (top-left, top-right, bottom-left, bottom-right, horizontal, vertical)
    "ascii":   ("+", "+", "+", "+", "-", "|"),
    "plus":    ("+", "+", "+", "+", "=", "|"),
    "dots":    (".", ".", "'", "'", "-", "|"),
    "single":  ("┌", "┐", "└", "┘", "─", "│"),
    "rounded": ("╭", "╮", "╰", "╯", "─", "│"),
    "double":  ("╔", "╗", "╚", "╝", "═", "║"),
    "heavy":   ("┏", "┓", "┗", "┛", "━", "┃"),
    "block":   ("█", "█", "█", "█", "█", "█"),
    "shade":   ("░", "░", "░", "░", "░", "░"),
}


def rect(c: Canvas, x: int, y: int, w: int, h: int, style: str = "ascii", fill: str | None = None) -> None:
    tl, tr, bl, br, hz, vt = BOX_STYLES[style]
    if w < 2 or h < 2:
        return
    for i in range(x + 1, x + w - 1):
        c.put(i, y, hz)
        c.put(i, y + h - 1, hz)
    for j in range(y + 1, y + h - 1):
        c.put(x, j, vt)
        c.put(x + w - 1, j, vt)
        if fill is not None:
            for i in range(x + 1, x + w - 1):
                c.put(i, j, fill)
    c.put(x, y, tl)
    c.put(x + w - 1, y, tr)
    c.put(x, y + h - 1, bl)
    c.put(x + w - 1, y + h - 1, br)


def ellipse(c: Canvas, cx: int, cy: int, rx: int, ry: int, ch: str | None = None, fill: str | None = None) -> None:
    """Connected ellipse outline, rx/ry in cells, centre (cx, cy). ch=None
    draws hand-style strokes (`.-'` shoulders, `/\\|` or `( )` sides); pass
    ch='*' etc. for a uniform outline. Terminal cells are about twice as
    tall as wide, so a round-looking circle needs rx = 2 * ry."""
    if rx <= 0 or ry <= 0:
        line(c, cx - rx, cy - ry, cx + rx, cy + ry, ch)
        return

    def half_width(row: int) -> int:
        # Sample at the band edge nearest the centre so cap rows keep width.
        ye = max(0.0, abs(row) - 0.5)
        return _rnd(rx * math.sqrt(max(0.0, 1 - (ye / ry) ** 2)))

    ext = {y: half_width(y) for y in range(-ry, ry + 1)}
    if fill is not None:
        for y, h in ext.items():
            for x in range(cx - h + 1, cx + h):
                c.put(x, cy + y, fill)
    for y, h in ext.items():
        top = y < 0
        if abs(y) == ry:  # cap row: full span with turned ends
            cells = list(range(cx - h, cx + h + 1))
            for x in cells:
                if ch:
                    m = ch
                elif x in (cells[0], cells[-1]):
                    m = "." if top else "'"
                else:
                    m = "-"
                c.put(x, cy + y, m)
            continue
        outer = ext[y - 1] if top else (ext[y + 1] if y > 0 else h)
        run = 1 if y == 0 else max(1, h - outer)
        for side in (-1, 1):
            for k in range(run):
                x = cx - h + k if side < 0 else cx + h - k
                if ch:
                    m = ch
                elif run == 1:
                    ye = max(0.0, abs(y) - 0.5)
                    slope = (ry * ry * h) / (rx * rx * ye) if ye > 0 else math.inf
                    if slope > 2.5:
                        m = "|" if ry >= 3 else ("(" if side < 0 else ")")
                    else:
                        m = "/" if (side < 0) == top else "\\"
                elif k == 0:  # outer end of a shoulder run
                    m = "." if top else "'"
                elif k == run - 1:  # inner end
                    m = "'" if top else "."
                else:
                    m = "-"
                c.put(x, cy + y, m)


def _mirror_into(c: Canvas, half: Canvas, x: int, y: int, axis_col: int) -> None:
    """Blit `half` at (x, y) and its mirror image across column `axis_col`
    (a column of `half`), so symmetric shapes are exactly symmetric."""
    for dy, row in enumerate(half.cells):
        for dx, ch in enumerate(row):
            if ch == " ":
                continue
            if dx == axis_col and ch in "/\\":
                ch = "|"  # both halves meet here; a diagonal would clash with its mirror
            c.put(x + dx, y + dy, ch)
            c.put(x + 2 * axis_col - dx, y + dy, MIRROR_PAIRS.get(ch, ch))


def diamond(c: Canvas, cx: int, cy: int, rx: int, ry: int, ch: str | None = None) -> None:
    """Diamond with vertices rx/ry cells from the centre. Hand-style strokes
    get `.` `'` `<` `>` vertices where the sides meet at an angle."""
    half = Canvas(rx + 1, 2 * ry + 1)
    line(half, rx, 0, 0, ry, ch)
    line(half, 0, ry, rx, 2 * ry, ch)
    _mirror_into(c, half, cx - rx, cy - ry, rx)
    if ch is None:
        if c.get(cx, cy - ry) in "/\\|":
            c.put(cx, cy - ry, ".")
        if c.get(cx, cy + ry) in "/\\|":
            c.put(cx, cy + ry, "'")
        c.put(cx - rx, cy, "<")
        c.put(cx + rx, cy, ">")


def triangle(c: Canvas, apex_x: int, apex_y: int, base_w: int, h: int, ch: str | None = None) -> None:
    """Isosceles triangle, apex at (apex_x, apex_y), base `base_w` wide and
    `h` rows tall. Hand-style strokes get a `.` apex and `'` base corners."""
    half_w = base_w // 2
    half = Canvas(half_w + 1, h)
    line(half, half_w, 0, 0, h - 1, ch)
    _mirror_into(c, half, apex_x - half_w, apex_y, half_w)
    by = apex_y + h - 1
    for x in range(apex_x - half_w + 1, apex_x + half_w):
        c.put(x, by, ch or "-")
    if ch is None:
        if c.get(apex_x, apex_y) in "/\\|":
            c.put(apex_x, apex_y, ".")
        c.put(apex_x - half_w, by, "'")
        c.put(apex_x + half_w, by, "'")


# --------------------------------------------------------------------------
# Banner text: a 5-row bitmap font rendered at exact widths
# --------------------------------------------------------------------------

FONT: dict[str, list[str]] = {
    "A": [".###.", "#...#", "#####", "#...#", "#...#"],
    "B": ["####.", "#...#", "####.", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "####.", "#....", "#####"],
    "F": ["#####", "#....", "####.", "#....", "#...."],
    "G": [".####", "#....", "#..##", "#...#", ".####"],
    "H": ["#...#", "#...#", "#####", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "###..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "####.", "#....", "#...."],
    "Q": [".###.", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "####.", "#..#.", "#...#"],
    "S": [".####", "#....", ".###.", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
    "Y": ["#...#", ".#.#.", "..#..", "..#..", "..#.."],
    "Z": ["#####", "...#.", "..#..", ".#...", "#####"],
    "0": [".###.", "#..##", "#.#.#", "##..#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "...#.", "..#..", "#####"],
    "3": ["####.", "....#", ".###.", "....#", "####."],
    "4": ["#...#", "#...#", "#####", "....#", "....#"],
    "5": ["#####", "#....", "####.", "....#", "####."],
    "6": [".###.", "#....", "####.", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", "..#.."],
    "8": [".###.", "#...#", ".###.", "#...#", ".###."],
    "9": [".###.", "#...#", ".####", "....#", ".###."],
    " ": ["..", "..", "..", "..", ".."],
    "!": ["#", "#", "#", ".", "#"],
    "?": [".###.", "#...#", "...#.", ".....", "..#.."],
    ".": [".", ".", ".", ".", "#"],
    ",": ["..", "..", "..", ".#", "#."],
    ":": [".", "#", ".", "#", "."],
    ";": ["..", ".#", "..", ".#", "#."],
    "-": ["...", "...", "###", "...", "..."],
    "_": [".....", ".....", ".....", ".....", "#####"],
    "'": ["#", "#", ".", ".", "."],
    '"': ["#.#", "#.#", "...", "...", "..."],
    "(": [".#", "#.", "#.", "#.", ".#"],
    ")": ["#.", ".#", ".#", ".#", "#."],
    "[": ["##", "#.", "#.", "#.", "##"],
    "]": ["##", ".#", ".#", ".#", "##"],
    "<": ["..#", ".#.", "#..", ".#.", "..#"],
    ">": ["#..", ".#.", "..#", ".#.", "#.."],
    "+": ["...", ".#.", "###", ".#.", "..."],
    "=": ["...", "###", "...", "###", "..."],
    "/": ["....#", "...#.", "..#..", ".#...", "#...."],
    "\\": ["#....", ".#...", "..#..", "...#.", "....#"],
    "*": [".....", "#.#.#", ".###.", "#.#.#", "....."],
    "#": [".#.#.", "#####", ".#.#.", "#####", ".#.#."],
    "&": [".##..", "#..#.", ".##.#", "#..#.", ".##.#"],
    "@": [".###.", "#...#", "#.###", "#....", ".####"],
    "%": ["##..#", "##.#.", "..#..", ".#.##", "#..##"],
}


def banner_bitmap(text: str, gap: int = 1) -> list[str]:
    """Rows of '#'/'.' pixels for the text (uppercased; unknown chars -> '?')."""
    rows = [""] * 5
    for i, ch in enumerate(text.upper()):
        glyph = FONT.get(ch) or FONT["?"]
        for r in range(5):
            rows[r] += ("." * gap if i else "") + glyph[r]
    return rows


def banner(text: str, fill: str = "#", half: bool = False, gap: int = 1, scale_x: int | None = None) -> str:
    """Render block letters. Default: each pixel is two `fill` chars wide
    (cells are ~2:1, so this keeps letters square). --half uses the upper/
    lower half-block characters to pack two pixel rows per text row."""
    bitmap = banner_bitmap(text, gap)
    if half:
        bitmap = bitmap + ["." * len(bitmap[0])]  # pad to even row count
        out = []
        for top, bottom in zip(bitmap[0::2], bitmap[1::2]):
            row = ""
            for t, b in zip(top, bottom):
                row += {(True, True): "█", (True, False): "▀", (False, True): "▄", (False, False): " "}[(t == "#", b == "#")]
            out.append(row.rstrip())
        return "\n".join(out)
    sx = scale_x if scale_x is not None else (2 if display_width(fill) == 1 else 1)
    return "\n".join("".join((fill * sx) if p == "#" else (" " * sx * display_width(fill)) for p in row).rstrip() for row in bitmap)


def figlet(text: str, font: str, width: int) -> str | None:
    """Classic figlet lettering through the `figlet` binary or pyfiglet;
    None when neither is installed."""
    if shutil.which("figlet"):
        res = subprocess.run(["figlet", "-f", font, "-w", str(width), text], capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.rstrip("\n")
    try:
        import pyfiglet  # type: ignore
        return pyfiglet.figlet_format(text, font=font, width=width).rstrip("\n")
    except Exception:
        return None


# --------------------------------------------------------------------------
# Boxes and mirroring
# --------------------------------------------------------------------------

def box(text: str, style: str = "ascii", title: str | None = None, pad: int = 1, align: str = "left") -> str:
    tl, tr, bl, br, hz, vt = BOX_STYLES[style]
    lines = text.rstrip("\n").split("\n")
    inner = max([display_width(l) for l in lines] + [display_width(title or "") + 2]) + 2 * pad
    out = []
    top = hz * inner
    if title:
        t = f" {title} "
        top = hz + t + hz * (inner - 1 - display_width(t))
    out.append(tl + top + tr)
    for l in lines:
        space = inner - 2 * pad - display_width(l)
        left = space // 2 if align == "center" else 0
        out.append(vt + " " * pad + " " * left + l + " " * (space - left) + " " * pad + vt)
    out.append(bl + hz * inner + br)
    return "\n".join(out)


MIRROR_PAIRS = {"/": "\\", "\\": "/", "(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{", "<": ">", ">": "<",
                "d": "b", "b": "d", "p": "q", "q": "p", "╭": "╮", "╮": "╭", "╰": "╯", "╯": "╰", "┌": "┐", "┐": "┌",
                "└": "┘", "┘": "└", "▌": "▐", "▐": "▌", "◤": "◥", "◥": "◤", "◣": "◢", "◢": "◣"}


def mirror(text: str, append: bool = False, overlap: bool = False) -> str:
    """Flip art horizontally. append=True glues the flipped copy to the right
    of the original (draw a left half, get a symmetric whole); overlap=True
    shares the centre column."""
    lines = text.rstrip("\n").split("\n")
    width = max(display_width(l) for l in lines)
    out = []
    for l in lines:
        padded = l + " " * (width - display_width(l))
        flipped = "".join(MIRROR_PAIRS.get(ch, ch) for ch in reversed(padded))
        if append:
            out.append((padded + (flipped[1:] if overlap else flipped)).rstrip())
        else:
            out.append(flipped.rstrip())
    return "\n".join(out)


# --------------------------------------------------------------------------
# Image conversion
# --------------------------------------------------------------------------

RAMPS = {
    "short": " .:-=+*#%@",
    "long": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "blocks": " ░▒▓█",
}
ANSI_RESET = "\x1b[0m"


def _load_image(path: str, width: int, height: int | None, aspect: float, mode: str,
                invert: bool, gamma: float, contrast: bool):
    try:
        from PIL import Image, ImageOps  # type: ignore
    except ImportError:
        sys.exit("asciiart image: needs Pillow - `python3 -m pip install pillow` (or convert the image "
                 "with `chafa`, `jp2a` or `img2txt` if one of those is installed)")
    img = Image.open(path)
    if getattr(img, "n_frames", 1) > 1:
        img.seek(0)
    img = img.convert("RGBA")
    bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
    img = Image.alpha_composite(bg, img).convert("RGB")
    px_w, px_h = {"ramp": (1, 1), "half": (1, 2), "braille": (2, 4)}[mode]
    if height is None:
        height = max(1, round(img.height * (width / img.width) * aspect * px_w / px_h))
    img = img.resize((width * px_w, height * px_h), Image.BOX)  # area average: no ringing halos
    gray = ImageOps.grayscale(img)
    if contrast:
        gray = ImageOps.autocontrast(gray, cutoff=1)
    lum = [[(gray.getpixel((x, y)) / 255.0) ** gamma for x in range(gray.width)] for y in range(gray.height)]
    if invert:
        lum = [[1 - v for v in row] for row in lum]
    return img, lum


def _dither(lum: list[list[float]], levels: int, gate: float = 0.08) -> list[list[int]]:
    """Floyd-Steinberg error diffusion to `levels` discrete values. Values
    within `gate` of black or white are clamped first, so flat dark
    backgrounds do not fill with stray dots."""
    h, w = len(lum), len(lum[0])
    buf = [[0.0 if v < gate else 1.0 if v > 1 - gate else v for v in row] for row in lum]
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            old = min(1.0, max(0.0, buf[y][x]))
            q = round(old * (levels - 1))
            out[y][x] = q
            err = old - q / (levels - 1)
            if x + 1 < w:
                buf[y][x + 1] += err * 7 / 16
            if y + 1 < h:
                if x > 0:
                    buf[y + 1][x - 1] += err * 3 / 16
                buf[y + 1][x] += err * 5 / 16
                if x + 1 < w:
                    buf[y + 1][x + 1] += err * 1 / 16
    return out


def _fg(rgb) -> str:
    return "\x1b[38;2;%d;%d;%dm" % rgb


def _bg(rgb) -> str:
    return "\x1b[48;2;%d;%d;%dm" % rgb


def image_to_text(path: str, width: int = 80, height: int | None = None, mode: str = "ramp",
                  ramp: str = "short", color: bool = False, bg: str = "dark", invert: bool = False,
                  aspect: float = 0.5, dither: bool | None = None, gamma: float = 1.0,
                  contrast: bool = True) -> str:
    # On a dark terminal, ink = light, so bright pixels get dense characters.
    # On paper or a light terminal the mapping flips.
    flip = (bg == "light") != invert
    img, lum = _load_image(path, width, height, aspect, mode, flip, gamma, contrast)
    chars = RAMPS.get(ramp, ramp)
    if dither is None:
        dither = mode == "braille"
    out_lines: list[str] = []
    if mode == "ramp":
        idx = _dither(lum, len(chars)) if dither else [[round(v * (len(chars) - 1)) for v in row] for row in lum]
        for y, row in enumerate(idx):
            parts = []
            for x, q in enumerate(row):
                ch = chars[min(q, len(chars) - 1)]
                parts.append((_fg(img.getpixel((x, y))) + ch) if color else ch)
            out_lines.append("".join(parts).rstrip() + (ANSI_RESET if color else ""))
    elif mode == "half":
        for y in range(0, img.height - 1, 2):
            parts = []
            for x in range(img.width):
                top, bottom = img.getpixel((x, y)), img.getpixel((x, y + 1))
                if color:
                    parts.append(_fg(top) + _bg(bottom) + "▀")
                else:
                    t, b = lum[y][x] > 0.5, lum[y + 1][x] > 0.5
                    parts.append({(True, True): "█", (True, False): "▀", (False, True): "▄", (False, False): " "}[(t, b)])
            out_lines.append("".join(parts) + (ANSI_RESET if color else ""))
    elif mode == "braille":
        bits = _dither(lum, 2) if dither else [[1 if v > 0.5 else 0 for v in row] for row in lum]
        dots = [(0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (0, 3, 0x40), (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (1, 3, 0x80)]
        for cy in range(0, len(bits) - 3, 4):
            parts = []
            for cx in range(0, len(bits[0]) - 1, 2):
                code = 0x2800
                for dx, dy, bit in dots:
                    if bits[cy + dy][cx + dx]:
                        code |= bit
                ch = chr(code)
                if color:
                    r = g = b = n = 0
                    for dx, dy, _ in dots:
                        pr, pg, pb = img.getpixel((cx + dx, cy + dy))
                        r, g, b, n = r + pr, g + pg, b + pb, n + 1
                    parts.append(_fg((r // n, g // n, b // n)) + ch)
                else:
                    parts.append(ch)
            out_lines.append("".join(parts) + (ANSI_RESET if color else ""))
    else:
        sys.exit(f"asciiart image: unknown mode {mode!r}")
    return "\n".join(out_lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _read(path: str | None) -> str:
    if path and path != "-":
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    return sys.stdin.read()


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Unicode art on Windows consoles too
    p = argparse.ArgumentParser(prog="asciiart.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("check", help="lint art for width, tabs, wide/zero-width characters")
    s.add_argument("file", nargs="?")
    s.add_argument("--max-width", type=int, default=80)
    s.add_argument("--unicode", action="store_true", help="non-ASCII characters are intended")
    s.add_argument("--ruler", action="store_true", help="print the art under a column ruler")

    s = sub.add_parser("grid", help="column ruler and optional blank grid")
    s.add_argument("width", type=int)
    s.add_argument("height", type=int, nargs="?", default=0)

    s = sub.add_parser("banner", help="block-letter text")
    s.add_argument("text")
    s.add_argument("--font", default="block", help="block (built-in) or a figlet font name, e.g. standard, slant, big")
    s.add_argument("--fill", default="#", help="pixel character for the block font (try █ or ▓)")
    s.add_argument("--half", action="store_true", help="half-block rendering: 5 cols x 3 rows per letter")
    s.add_argument("--gap", type=int, default=1, help="pixel columns between letters")
    s.add_argument("--scale-x", type=int, default=None, help="cells per pixel horizontally (default 2 for 1-cell fills)")
    s.add_argument("--width", type=int, default=80, help="wrap width for figlet fonts")

    s = sub.add_parser("box", help="frame stdin or a file")
    s.add_argument("file", nargs="?")
    s.add_argument("--style", default="ascii", choices=sorted(BOX_STYLES))
    s.add_argument("--title")
    s.add_argument("--pad", type=int, default=1)
    s.add_argument("--align", default="left", choices=["left", "center"])

    s = sub.add_parser("shape", help="geometric outline")
    s.add_argument("kind", choices=["circle", "ellipse", "rect", "diamond", "triangle", "line"])
    s.add_argument("nums", type=int, nargs="*", help="circle R | ellipse RX RY | rect W H | diamond W H | triangle W [H] | line X0 Y0 X1 Y1")
    s.add_argument("--ch", help="force one stroke character (default: slope-aware strokes)")
    s.add_argument("--fill", help="interior character")
    s.add_argument("--style", default="ascii", choices=sorted(BOX_STYLES), help="rect border style")

    s = sub.add_parser("image", help="convert an image file to text")
    s.add_argument("path")
    s.add_argument("--width", type=int, default=80, help="output columns")
    s.add_argument("--height", type=int, help="output rows (default: keep aspect)")
    s.add_argument("--mode", default="ramp", choices=["ramp", "braille", "half"])
    s.add_argument("--ramp", default="short", help="short | long | blocks | literal characters dark->light")
    s.add_argument("--color", action="store_true", help="ANSI truecolor output (terminal only, not for files/README)")
    s.add_argument("--bg", default="dark", choices=["dark", "light"], help="where it will be viewed; flips the density mapping")
    s.add_argument("--invert", action="store_true")
    s.add_argument("--aspect", type=float, default=0.5, help="cell width / cell height of the target font")
    s.add_argument("--dither", action="store_true", help="error-diffusion dithering (default on for braille)")
    s.add_argument("--gamma", type=float, default=1.0, help=">1 darkens midtones, <1 lightens")
    s.add_argument("--no-contrast", action="store_true", help="skip auto-contrast stretch")

    s = sub.add_parser("mirror", help="flip art left<->right")
    s.add_argument("file", nargs="?")
    s.add_argument("--append", action="store_true", help="append the mirrored half to the original")
    s.add_argument("--overlap", action="store_true", help="with --append: share the centre column")

    a = p.parse_args(argv)

    if a.cmd == "check":
        text = _read(a.file)
        errors, notes, stats = lint(text, a.max_width, a.unicode)
        if a.ruler:
            print(ruler(max(stats["max_width"], 10)))
            print(text.rstrip("\n"))
            print()
        print(f"{stats['lines']} lines, widths {stats['min_width']}..{stats['max_width']} (limit {a.max_width})")
        for e in errors:
            print(f"ERROR  {e}")
        for n in notes:
            print(f"note   {n}")
        if not errors:
            print("OK: every line is one cell per character and within width")
        return 1 if errors else 0

    if a.cmd == "grid":
        print(ruler(a.width))
        for _ in range(a.height):
            print("." * a.width)
        return 0

    if a.cmd == "banner":
        if a.font == "block":
            print(banner(a.text, a.fill, a.half, a.gap, a.scale_x))
            return 0
        out = figlet(a.text, a.font, a.width)
        if out is None:
            sys.exit("asciiart banner: no figlet or pyfiglet installed (`pip install pyfiglet` / `apt install figlet`); "
                     "use --font block for the built-in font")
        print(out)
        return 0

    if a.cmd == "box":
        print(box(_read(a.file), a.style, a.title, a.pad, a.align))
        return 0

    if a.cmd == "shape":
        n = a.nums
        need = {"circle": 1, "ellipse": 2, "rect": 2, "diamond": 2, "triangle": 1, "line": 4}[a.kind]
        if len(n) < need:
            sys.exit(f"asciiart shape {a.kind}: needs {need} number(s)")
        if a.kind == "circle":
            rx, ry = 2 * n[0], n[0]
            c = Canvas(2 * rx + 1, 2 * ry + 1)
            ellipse(c, rx, ry, rx, ry, a.ch, a.fill)
        elif a.kind == "ellipse":
            rx, ry = n[0], n[1]
            c = Canvas(2 * rx + 1, 2 * ry + 1)
            ellipse(c, rx, ry, rx, ry, a.ch, a.fill)
        elif a.kind == "rect":
            c = Canvas(n[0], n[1])
            rect(c, 0, 0, n[0], n[1], a.style, a.fill)
        elif a.kind == "diamond":
            rx, ry = n[0] // 2, n[1] // 2
            c = Canvas(2 * rx + 1, 2 * ry + 1)
            diamond(c, rx, ry, rx, ry, a.ch)
        elif a.kind == "triangle":
            w = n[0]
            h = n[1] if len(n) > 1 else (w // 2 + w % 2) // 1
            h = max(2, h)
            c = Canvas(w + (1 - w % 2), h)
            triangle(c, w // 2, 0, w, h, a.ch)
        else:
            x0, y0, x1, y1 = n[:4]
            c = Canvas(max(x0, x1) + 1, max(y0, y1) + 1)
            line(c, x0, y0, x1, y1, a.ch)
        print(c.render())
        return 0

    if a.cmd == "image":
        print(image_to_text(a.path, a.width, a.height, a.mode, a.ramp, a.color, a.bg, a.invert,
                            a.aspect, True if a.dither else None, a.gamma, not a.no_contrast))
        return 0

    if a.cmd == "mirror":
        print(mirror(_read(a.file), a.append, a.overlap))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
