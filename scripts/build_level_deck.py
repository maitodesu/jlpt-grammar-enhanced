"""Stitch a level's chapter decks into one deck, behind an orientation slide.

A level runs to a few thousand slides, which reads as daunting until you know
the shape of it: every grammar point walks the same short path, and nobody
reads a level front to back. The opening slide says so, in the level's own
numbers, counted from the chapter decks rather than written down here.

Usage:
    python scripts/build_level_deck.py n5
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

STYLE_RE = re.compile(r"^<style>.*?</style>\s*", re.S)

# The path every grammar point takes, in the order the book lays it out.
SECTIONS = [
    ("Formation", "what it attaches to, and how"),
    ("Examples", "the pattern in real sentences"),
    ("Nuance & register", "when it fits, and who says it"),
    ("Contrast", "how it differs from its lookalikes"),
    ("Common mistakes", "the errors worth pre-empting"),
    ("Practice", "questions, with answers you reveal"),
]


def chapter_decks(level: str) -> list[Path]:
    return sorted((ROOT / "decks" / level).glob("[0-9][0-9] - *.md"))


def overview(level: str, decks: list[Path], slides: int, points: int) -> str:
    per_point = round(slides / points) if points else 0
    return "\n\n".join([
        f"# {level.upper()} — what's inside",
        f"**{len(decks)} chapters · {points} grammar points · {slides:,} slides**",
        "\n".join(f"- **{name}** — {gloss}" for name, gloss in SECTIONS),
        f"That path is every grammar point, so a point runs about {per_point} slides "
        f"and a chapter is one sitting. Nothing here is read front to back — "
        f"jump to the point you need.",
    ])


def main():
    if len(sys.argv) != 2:
        print("usage: build_level_deck.py <level, e.g. n5>", file=sys.stderr)
        sys.exit(1)
    level = sys.argv[1].lower()

    decks = chapter_decks(level)
    if not decks:
        print(f"no chapter decks under decks/{level}", file=sys.stderr)
        sys.exit(1)

    bodies = [p.read_text(encoding="utf-8").strip() for p in decks]
    slides = sum(b.count("\n---\n") + 1 for b in bodies)
    # A grammar point opens on an h1 that is not a chapter title ("# N5 - ...").
    points = sum(len(re.findall(rf"^# (?!{level.upper()} - ).+$", b, re.M)) for b in bodies)

    # The font-scale style rides on chapter one's first slide; lift it onto the
    # overview so the deck still opens with its own styling applied.
    style = ""
    if match := STYLE_RE.match(bodies[0]):
        style = match.group(0).strip() + "\n\n"
        bodies[0] = STYLE_RE.sub("", bodies[0])

    out = ROOT / "decks" / level / f"{level.upper()} - all chapters.md"
    out.write_text(style + "\n\n---\n\n".join([overview(level, decks, slides, points)] + bodies) + "\n",
                   encoding="utf-8")
    print(f"{out.relative_to(ROOT)} ({len(decks)} chapters, {points} points, {slides + 1} slides)")


if __name__ == "__main__":
    main()
