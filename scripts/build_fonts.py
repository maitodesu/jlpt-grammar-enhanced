"""Subset Noto Sans JP to the Japanese the decks actually contain.

The decks are Latin prose around Japanese examples, and the two want different
faces: Libron for reading the English, Noto Sans JP for every kana and kanji.
Loading all of Noto Sans JP would be megabytes, so this cuts it down to the
characters this corpus uses — a fixed set, since the book is the corpus.

The emitted `unicode-range` is what keeps the split honest: scoped to Japanese
only, the face is skipped for Latin, so Libron keeps the prose no matter which
deckrun theme is on.

Usage:
    python scripts/build_fonts.py            # uses the cached source download
    python scripts/build_fonts.py --refresh  # re-download Noto Sans JP first
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "fonts" / "noto-sans-jp"
SOURCE = OUT_DIR / "source" / "NotoSansJP[wght].ttf"
SOURCE_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf"

# Japanese, plus the symbols the book sets alongside it (arrows in formation
# tables, ≒, ○). Emoji are left to the system's colour font.
KEEP_RANGES = [
    (0x3000, 0x303F),  # CJK punctuation
    (0x3040, 0x309F),  # hiragana
    (0x30A0, 0x30FF),  # katakana
    (0x4E00, 0x9FFF),  # CJK unified ideographs
    (0xFF00, 0xFFEF),  # fullwidth forms
]
KEEP_SYMBOLS = "→−≒○…—·"


def corpus_chars() -> set:
    chars = set()
    for path in (ROOT / "decks").glob("*/[0-9][0-9] - *.md"):
        chars |= set(path.read_text(encoding="utf-8"))
    keep = {c for c in chars
            if any(lo <= ord(c) <= hi for lo, hi in KEEP_RANGES) or c in KEEP_SYMBOLS}
    return keep


def unicode_range(chars: set) -> str:
    """Collapse the kept codepoints into a CSS unicode-range list."""
    points = sorted(ord(c) for c in chars)
    spans, start, prev = [], points[0], points[0]
    for p in points[1:]:
        if p != prev + 1:
            spans.append((start, prev))
            start = p
        prev = p
    spans.append((start, prev))
    return ", ".join(f"U+{a:04X}" if a == b else f"U+{a:04X}-{b:04X}" for a, b in spans)


def main():
    if "--refresh" in sys.argv or not SOURCE.exists():
        SOURCE.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {SOURCE_URL}")
        urllib.request.urlretrieve(SOURCE_URL, SOURCE)

    chars = corpus_chars()
    if not chars:
        print("no deck Markdown found — build the decks first", file=sys.stderr)
        sys.exit(1)

    from fontTools import subset

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_font = OUT_DIR / "NotoSansJP-subset.woff2"
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.notdef_outline = True
    options.recalc_bounds = True
    # Keep the weight axis: the decks set bold for the pattern under discussion.
    options.retain_gids = False

    font = subset.load_font(str(SOURCE), options)
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=[ord(c) for c in chars])
    subsetter.subset(font)
    subset.save_font(font, str(out_font), options)

    meta = {"unicodeRange": unicode_range(chars), "characters": len(chars),
            "file": out_font.name, "bytes": out_font.stat().st_size}
    (OUT_DIR / "subset.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"{out_font.relative_to(ROOT)}  {len(chars)} chars, {meta['bytes'] // 1024} KB")


if __name__ == "__main__":
    main()
