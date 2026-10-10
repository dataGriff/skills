# Gallery: worked subjects and composition

Starting shapes for common requests, all drawn with the rules in SKILL.md
(`.` low, `'` high, shoulders `.-"-.` / `'-.-'`, widths about twice the
heights). Adapt them: resize, change the expression, add a prop. They are
original to this skill, so they can be used without attribution.

## Contents

- Faces and expressions
- Animals
- Plants and landscape
- Objects and vehicles
- Diagrams, charts and dividers
- Composing a scene
- Animation in the terminal

## Faces and expressions

```text
  .-"""-.        .-"""-.        .-"""-.        .-"""-.
 /       \      /       \      /       \      /       \
|  o   o  |    |  ^   ^  |    |  >   <  |    |  @   @  |
|    .    |    |    .    |    |    .    |    |    .    |
 \   -   /      \  \_/  /      \  .-.  /      \   o   /
  '-...-'        '-...-'        '-...-'        '-...-'
  neutral          happy          angry         startled
```

Mouth shapes do most of the work: `-` flat, `\_/` smile, `'-'` gentle
smile, `.-.` frown, `o` surprise, `~` queasy. Keep both eyes on one row.

## Animals

```text
    /\_/\             (\_/)            .---.
   ( o.o )            ( o.o )         ( o o )
    > ^ <             (")_(")         (  v  )
   /     \                           .'     '.
  (  |_|  )        rabbit: the ears   \|     |/
   \_/ \_/         carry the species   '-----'
  sitting cat                           "   "
                                       penguin
```

```text
        .-"""""-.                      .--.      .--.
   \   /      o  \                    /    '----'    \
    \ (           >                  |  o        o   |
    / (           >                  |      ___      |
   /   \         /                    \    (___)    /
        '-.....-'                      '--.      .--'
  fish: tail left, mouth right             '----'
                                       dog: drooping ears
```

Swap eyes to change state: `-.-` asleep (add ` z Z` to the right), `x.x`
knocked out, `O.o` puzzled. A tail is one stroke: `~` or `_/` trailing
from the body's bottom corner.

## Plants and landscape

```text
        .-"-.                 ^
     .-(     )-.             / \
    (           )           /   \
     '-(     )-'           /_____\
        '-.-'               /   \
          |                /     \
          |               /_______\
     _____|_____           /     \
   round-crown tree       /       \
                         /_________\
                             | |
                             |_|
                           pine
```

```text
       \  |  /                      _.--._
        .---.                    .-'      '-.
     --(     )--              .-'            '-.
        '---'              .-'                  '-.
       /  |  \          .-'                        '-.
         sun           hills: stepped runs, never a doubled stroke
```

```text
            /\
           /  \        /\
          / /\ \      /  \
    /\   / /  \ \    / /\ \
   /  \ /_/    \_\  / /  \ \
  /    V          \/_/    \_\
 /                            \
 mountains: foreground peak lowest and widest, background peaks higher
```

## Objects and vehicles

```text
   ) )              _____             .------------------.
  ( (              /     \            | $ build --fast   |
 .......          /_______\           | ok, 3 passed     |
 |     |]         |  __   |           | $ _              |
 \     /          | |  |  |           |__________________|
  '---'         __|_|__|__|__        /______________________\
  mug             house               laptop
```

```text
       ^              .-"-.   .-"-.              .
      / \            /     '-'     \            / \
     /   \          |               |      .---'   '---.
    |     |          \             /        '-.     .-'
    |  o  |           '.         .'           /  .  \
    |     |             '.     .'            /.-' '-.\
   /|     |\              '. .'              star
  / |     | \               '
 /__|_____|__\             heart
    /_/ \_\
     \ ^ /
      \ /
       V
     rocket
```

```text
        _                     |\
     .-[_]-.                  | \
     | o o |                  |  \
    [|  -  |]                 |   \
     '-----'                  |____\
   .--|   |--.      ~~~~~~~~~~\________/~~~~~~~~~~
   |  |___|  |                sailboat
  [_] |_|_| [_]
     robot
```

## Diagrams, charts and dividers

```text
+----------+      +----------+      +----------+
|  client  | ---> |   api    | ---> |    db    |
+----------+      +----------+      +----------+
                        |
                        v
                  +----------+
                  |  cache   |
                  +----------+
```

```text
┌──────────┐      ┌──────────┐      ┌──────────┐
│  client  │ ───> │   api    │ ───> │    db    │
└──────────┘      └─────┬────┘      └──────────┘
                        │
                        ▼
                  ┌──────────┐
                  │  cache   │
                  └──────────┘
```

Boxes in one row share a height and a top edge; arrows leave and enter at
the vertical middle of a box or the horizontal middle of an edge, through
a junction character (`┬`, `┴`, `+`) rather than a gap.

```text
 requests/s                      python  ########################  48%
 400 |            ####           go      ############              24%
 300 |      ####  ####           rust    ########                  16%
 200 |      ####  ####  ####     other   ######                    12%
 100 |####  ####  ####  ####
     +------------------------   cpu  ▁▂▃▅▆▇█▆▅▃▂▁▂▃▅  disk ████████▌
       mon   tue   wed   thu
```

Bars are integer widths, so round consistently and say so if precision
matters; a `█` is 8 eighths, so `▏▎▍▌▋▊▉` give sub-cell resolution.

```text
 .------------------.
 |  build passing!  |
 '---.  .-----------'
      \/
```

```text
-----------------------------------------
=========================================
- - - - - - - - - - - - - - - - - - - - -
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
*   *   *   *   *   *   *   *   *   *   *
────────────────────────────────────────
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
════════════════════════════════════════
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
```

## Composing a scene

1. Decide the frame (width × height) and a ground line; most scenes read
   better with the horizon in the lower third.
2. Place the focal element first (the house, the mascot), then the
   background shapes, then texture (`~` water, `"` grass, `*` stars) in the
   empty regions. Texture is sparse: one mark every 3-6 cells, varied.
3. Draw back to front so nearer things overwrite farther ones; with the
   `Canvas` in `scripts/asciiart.py`, `blit` each part at its coordinates
   and let its transparency handle the overlap.
4. Keep one light source: shading (`.` light to `#` dark) always on the same
   side of every object.
5. One scale: a door is a third of a house, a person is half a door; a sun
   or moon is small and far.

```text
                 *            .---.          *
      *                    --(     )--              *
                              '---'
            _.--._                                 _.--._
         .-'      '-.           _____          .-'      '-.
      .-'            '-.       /     \      .-'            '-.
   .-'                  '-.   /_______\  .-'                  '-.
                              |  __   |
   "   "     "        "       | |  |  |     "    "       "    "
______________________________|_|__|__|__________________________
```

## Animation in the terminal

- Frames must all have the same width and height; pad short rows with
  spaces and add blank rows, or the previous frame shows through.
- Redraw in place with the cursor-home escape `\x1b[H` (or move up N rows
  with `\x1b[NA`), not by clearing the screen each frame, which flickers.
- Hide the cursor while animating (`\x1b[?25l`) and restore it on exit
  (`\x1b[?25h`), including on Ctrl-C.
- 8-15 frames per second is plenty; sleep about 0.08 s.

```python
import sys, time
open_eyes, blink = "( o.o )", "( -.- )"
frames = [open_eyes] * 20 + [blink] * 2   # 22 frames at 12 fps: a blink every ~2 s
sys.stdout.write("\x1b[?25l")
try:
    for f in frames * 3:
        sys.stdout.write("\r" + f)
        sys.stdout.flush()
        time.sleep(0.08)
finally:
    sys.stdout.write("\x1b[?25h\n")
```
