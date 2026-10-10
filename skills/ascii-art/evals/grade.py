#!/usr/bin/env python3
"""Grade ascii-art eval runs. Usage: grade.py <iteration-dir>.

Expects <iteration-dir>/eval-*/{with_skill,without_skill}/outputs/ as laid
out by scripts/eval_skills.py (run via `task eval:skills NAME=ascii-art`).
Writes grading.json per arm and prints a pass/total summary.

Checks are mechanical properties that separate careful terminal art from
careless art: exact widths, rectangular frames, no tabs or wide characters,
sensible aspect ratio, and - for image conversion - that character density
actually tracks the source image's luminance. Stdlib only (the PNG fixture
is decoded here without Pillow).
"""
import json
import math
import re
import struct
import sys
import unicodedata
import zlib
from pathlib import Path

RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"


def E(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": str(evidence)[:500]}


def read_art(path: Path, keep_blank_rows: bool = False):
    """Lines of an art file. Blank rows at either end are dropped unless
    keep_blank_rows is set (an image conversion's blank rows are picture)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.endswith("\n"):
        text = text[:-1]
    lines = text.split("\n")
    if not keep_blank_rows:
        while lines and not lines[-1].strip():
            lines.pop()
        while lines and not lines[0].strip():
            lines.pop(0)
    return lines


def widths(lines):
    return [len(l) for l in lines]


def common_checks(lines, name, max_width, ascii_only=True):
    ex = []
    text = "\n".join(lines)
    ex.append(E(f"{name}: no tab characters", "\t" not in text, f"{text.count(chr(9))} tabs"))
    if ascii_only:
        bad = sorted({c for c in text if ord(c) > 0x7F})
        ex.append(E(f"{name}: pure ASCII as requested", not bad, f"non-ASCII: {bad[:10]}"))
    wide = [c for c in text if unicodedata.east_asian_width(c) in ("W", "F") or unicodedata.category(c) in ("Mn", "Me", "Cf")]
    ex.append(E(f"{name}: no double-width or zero-width characters", not wide, f"{len(wide)} found"))
    w = widths(lines)
    ex.append(E(f"{name}: every line within {max_width} columns", w and max(w) <= max_width, f"max {max(w) if w else 0}"))
    ex.append(E(f"{name}: no markdown fence or prose in the file",
                not any(l.strip().startswith("```") for l in lines)
                and not re.search(r"\b(here is|here's|this is|i made|note:)\b", text, re.I),
                "grep fences / prose"))
    return ex


def grade_banner(out):
    f = out / "banner.txt"
    if not f.exists():
        return [E("banner.txt exists", False, "missing")]
    lines = read_art(f)
    ex = [E("banner.txt exists with content", len(lines) >= 7, f"{len(lines)} lines")]
    ex += common_checks(lines, "banner", 70)
    w = widths(lines)
    rect = len(set(w)) == 1
    ex.append(E("Framed banner is rectangular: every line the same width (border lines included)",
                rect, f"widths {sorted(set(w))}"))
    top, bottom = lines[0], lines[-1]
    border_chars = set("+-=#*|.'`_~")
    ex.append(E("First and last lines are border lines made of border characters",
                set(top) <= border_chars and set(bottom) <= border_chars and len(top) > 10,
                f"top={top[:20]!r} bottom={bottom[:20]!r}"))
    sides = [l for l in lines[1:-1] if l and l[0] in "|#*:!+" and l[-1] in "|#*:!+"]
    ex.append(E("Every interior line is closed by a side border character at both ends",
                len(sides) == len(lines) - 2, f"{len(sides)}/{len(lines) - 2} closed"))
    ex.append(E("Tagline present and intact", "watch your logs breathe" in "\n".join(lines).lower(),
                "grep tagline"))
    # Block letters: a run of >=4 rows each carrying substantial ink that is not the tagline/border.
    ink_rows = [l for l in lines[1:-1] if "watch your logs" not in l.lower()
                and sum(1 for c in l[1:-1] if c not in " ") >= 8]
    ex.append(E("Letters are block-rendered across at least 4 rows of heavy ink",
                len(ink_rows) >= 4, f"{len(ink_rows)} ink rows"))
    interior = [l[1:-1] for l in lines[1:-1]]
    ex.append(E("Content does not touch the border (one cell of air on both sides)",
                all(not l or (l[0] == " " and l[-1] == " ") for l in interior), "left/right cells blank"))
    return ex


def grade_owl(out):
    f = out / "owl.txt"
    if not f.exists():
        return [E("owl.txt exists", False, "missing")]
    lines = read_art(f)
    ex = [E("owl.txt exists with content", len(lines) >= 5, f"{len(lines)} lines")]
    ex += common_checks(lines, "owl", 40)
    ex.append(E("Between 10 and 18 rows", 10 <= len(lines) <= 18, f"{len(lines)} rows"))
    ex.append(E("No trailing whitespace", all(l == l.rstrip() for l in lines), "rstrip compare"))
    w = widths(lines)
    ex.append(E("Figure is wider than it is tall in cells (2:1 aspect compensation)",
                max(w) >= len(lines) * 1.2, f"{max(w)} cols x {len(lines)} rows"))
    # Eyes: two eye-like glyph groups (`o`, `(O)`, `@@`, `(o,o)` halves...) on
    # one row, symmetric about the row's figure centre.
    eye = re.compile(r"[oO0@*]+")
    eye_row = None
    for l in lines[:10]:
        groups = [(m.start() + m.end() - 1) / 2 for m in eye.finditer(l)]
        if len(groups) == 2 and 2 <= groups[1] - groups[0] <= 16:
            left, right = len(l) - len(l.lstrip()), len(l.rstrip()) - 1
            centre = (left + right) / 2
            if abs((groups[0] + groups[1]) / 2 - centre) <= 1.0:
                eye_row = l
                break
    ex.append(E("Two eyes on one row, symmetric about the figure's centre", eye_row is not None,
                repr(eye_row)))
    ex.append(E("A branch: a horizontal run of 6+ line characters in the lower half",
                any(re.search(r"[-_=~]{6,}", l) for l in lines[len(lines) // 2:]), "grep lower rows"))
    ex.append(E("Beak or face mark below the eyes (v, V, ^, >, <, \\/ or similar)",
                eye_row is None or any(re.search(r"[vV^><]|\\/", l) for l in lines[lines.index(eye_row) + 1: lines.index(eye_row) + 4]),
                "grep rows after eyes"))
    letters = sum(1 for l in lines for c in l if c.isalpha() and c not in "oOvVwWuUxX")
    ex.append(E("No stray letters used as strokes (o/v/w/u/x allowed as features)", letters <= 4,
                f"{letters} stray letters"))
    # Richness: the skill's craft guidance asks for texture, limbs, a prop and
    # use of the allowed space, not just a correct silhouette.
    distinct = {c for l in lines for c in l if c != " "}
    ex.append(E("Stroke variety: at least 9 distinct characters (features, texture, prop)",
                len(distinct) >= 9, f"{len(distinct)}: {''.join(sorted(distinct))}"))
    ex.append(E("Uses the allowed space: at least 12 rows and 24 columns",
                len(lines) >= 12 and max(w) >= 24, f"{len(lines)} rows x {max(w)} cols"))

    def interior_marks(l):
        s = l.strip()
        return sum(1 for c in s[1:-1] if c != " ") if len(s) > 2 else 0

    detail_rows = sum(1 for l in lines if interior_marks(l) >= 2)
    ex.append(E("Interior detail: at least 7 rows carry marks inside the outline (texture, limbs, face)",
                detail_rows >= 7, f"{detail_rows} rows"))
    if eye_row is not None:
        above = lines[:lines.index(eye_row)]
        tufts = any(len(re.findall(r"\S+", l)) >= 2 for l in above)
        ex.append(E("Head detail above the eyes: ear tufts or brows as two separate groups", tufts,
                    repr(above[-1]) if above else "no rows above the eyes"))
    branch_idx = next((i for i, l in enumerate(lines) if i >= len(lines) // 2 and re.search(r"[-_=~]{6,}", l)), None)
    if branch_idx:
        feet_rows = lines[max(0, branch_idx - 2):branch_idx]
        ex.append(E("Feet or talons where the body meets the branch (2+ mark groups just above it)",
                    any(len(re.findall(r"\S+", r)) >= 2 for r in feet_rows), repr(feet_rows)))
    return ex


def read_png_luminance(path: Path):
    """Decode an 8-bit non-interlaced PNG (RGB/RGBA/L) to a 2-D luminance grid 0..1."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, idat, hdr = 8, b"", None
    while pos < len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8: pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
    w, h, depth, ctype_, _, _, interlace = hdr
    assert depth == 8 and interlace == 0, "grader supports 8-bit non-interlaced PNG only"
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[ctype_]
    bpp, stride = channels, w * channels
    raw = zlib.decompress(idat)
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        f, cur = raw[i], bytearray(raw[i + 1: i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = cur[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                cur[x] = (cur[x] + a) & 255
            elif f == 2:
                cur[x] = (cur[x] + b) & 255
            elif f == 3:
                cur[x] = (cur[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                cur[x] = (cur[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(cur)
        prev = cur
    if channels >= 3:
        return [[(0.299 * r[x * bpp] + 0.587 * r[x * bpp + 1] + 0.114 * r[x * bpp + 2]) / 255 for x in range(w)] for r in rows]
    return [[r[x * bpp] / 255 for x in range(w)] for r in rows]


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs)) or 1e-9
    sy = math.sqrt(sum((y - my) ** 2 for y in ys)) or 1e-9
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def grade_image(out):
    f = out / "scene.txt"
    if not f.exists():
        return [E("scene.txt exists", False, "missing")]
    lines = read_art(f, keep_blank_rows=True)
    ex = [E("scene.txt exists with content", len(lines) >= 5, f"{len(lines)} lines")]
    ex += common_checks(lines, "scene", 60)
    w = widths(lines)
    ex.append(E("Exactly 60 columns wide (allowing trailing-space trimming on the longest row)",
                57 <= max(w) <= 60, f"max width {max(w)}"))
    ex.append(E("Row count preserves aspect for 2:1 cells (240x180 image at 60 cols -> about 22 rows)",
                16 <= len(lines) <= 30, f"{len(lines)} rows"))
    png = out / "scene.png"
    if not png.exists():
        ex.append(E("source image available for luminance comparison", False, "scene.png missing from outputs"))
        return ex
    lum = read_png_luminance(png)
    ih, iw = len(lum), len(lum[0])
    # Map output cells onto the image through the row count a 2:1 grid at
    # this width implies, top-aligned, so a converter that trimmed trailing
    # blank rows is not punished with a vertical stretch.
    cols = max(w)
    rows = max(len(lines), round(ih * cols / iw * 0.5))
    lines = lines + [""] * (rows - len(lines))
    dens, src = [], []
    for y, l in enumerate(lines):
        l = l.ljust(cols)
        for x in range(cols):
            ch = l[x]
            d = RAMP.index(ch) / (len(RAMP) - 1) if ch in RAMP else 0.5
            x0, x1 = int(x * iw / cols), max(int(x * iw / cols) + 1, int((x + 1) * iw / cols))
            y0, y1 = int(y * ih / rows), max(int(y * ih / rows) + 1, int((y + 1) * ih / rows))
            cells = [lum[yy][xx] for yy in range(y0, y1) for xx in range(x0, x1)]
            dens.append(d)
            src.append(sum(cells) / len(cells))
    r = pearson(dens, src)
    ex.append(E("Character density correlates with image luminance (dark terminal: bright = dense), r >= 0.6",
                r >= 0.6, f"pearson r = {r:.3f}"))

    def region_density(x0, y0, x1, y1):
        vals = [dens[y * cols + x] for y in range(rows) for x in range(cols)
                if x0 <= (x + 0.5) / cols < x1 and y0 <= (y + 0.5) / rows < y1]
        return sum(vals) / len(vals) if vals else 0

    disc = region_density(0.12, 0.15, 0.38, 0.52)      # pale disc
    red = region_density(0.65, 0.13, 0.9, 0.55)        # red block (mid luminance)
    bg = region_density(0.45, 0.13, 0.6, 0.55)         # dark background between them
    black = region_density(0.18, 0.9, 0.44, 0.97)      # black rectangle
    ex.append(E("Pale disc is clearly denser than the dark background (difference >= 0.25)",
                disc - bg >= 0.25, f"disc {disc:.2f} vs background {bg:.2f}"))
    ex.append(E("Dark background and black rectangle render light (density <= 0.15)",
                bg <= 0.15 and black <= 0.15, f"background {bg:.2f}, black {black:.2f}"))
    ex.append(E("Red block (mid luminance) sits between background and disc in density",
                bg < red < disc, f"bg {bg:.2f} < red {red:.2f} < disc {disc:.2f}"))
    return ex


GRADERS = {"eval-0": grade_banner, "eval-1": grade_owl, "eval-2": grade_image}


def main():
    iteration = Path(sys.argv[1])
    for eval_dir in sorted(iteration.glob("eval-*")):
        key = "-".join(eval_dir.name.split("-", 2)[:2])  # "eval-<id>"
        grader = GRADERS.get(key)
        if grader is None:
            sys.exit(f"grade.py: no grader registered for {eval_dir.name} "
                     f"(known: {sorted(GRADERS)}) - add it to GRADERS")
        for arm in ("with_skill", "without_skill"):
            out = eval_dir / arm / "outputs"
            if not out.is_dir():
                continue
            expectations = grader(out)
            passed = sum(1 for e in expectations if e["passed"])
            (eval_dir / arm / "grading.json").write_text(json.dumps(
                {"expectations": expectations,
                 "summary": {"passed": passed, "failed": len(expectations) - passed,
                             "total": len(expectations),
                             "pass_rate": round(passed / len(expectations), 4)}},
                indent=2))
            print(f"  {eval_dir.name}/{arm}: {passed}/{len(expectations)}")


if __name__ == "__main__":
    sys.exit(main())
