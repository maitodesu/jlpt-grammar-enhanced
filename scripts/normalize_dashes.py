"""Replace em dashes with spaced hyphens across the book.

    python scripts/normalize_dashes.py --dry-run    # report only
    python scripts/normalize_dashes.py              # apply

Only U+2014 EM DASH and U+2013 EN DASH are touched. Characters that look
similar but are not dashes are left strictly alone -- getting this wrong would
corrupt Japanese text rather than just restyle it:

    U+30FC  ー   katakana prolonged sound mark (コーヒー, ビール)
    U+4E00  一   the kanji for "one"
    U+2212  −   minus sign
    U+FF0D  －   fullwidth hyphen-minus

Whitespace around the dash is normalised to a single space either side, so
"word — word", "word—word" and "word  —  word" all become "word - word".
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

DASHES = "—–"                      # em dash, en dash
PROTECTED = "ー一−－‐"  # must never be altered

DASH_RE = re.compile(rf"[ \t]*[{DASHES}][ \t]*")

# A markdown table delimiter row (|---|---|) is hyphens already, but guard
# against a dash inside one being padded into "| - --|".
TABLE_DELIM = re.compile(r"^\s*\|[\s|:-]+\|\s*$")


def convert_line(line):
    if TABLE_DELIM.match(line):
        return line
    return DASH_RE.sub(" - ", line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--root", default="src")
    args = ap.parse_args()

    files = sorted(Path(args.root).rglob("*.md"))
    total = changed_files = 0
    protected_before = protected_after = 0

    for f in files:
        text = f.read_text(encoding="utf-8")
        protected_before += sum(text.count(c) for c in PROTECTED)

        n = sum(text.count(c) for c in DASHES)
        if not n:
            protected_after += sum(text.count(c) for c in PROTECTED)
            continue

        new = "\n".join(convert_line(l) for l in text.split("\n"))
        total += n
        changed_files += 1
        protected_after += sum(new.count(c) for c in PROTECTED)

        if args.dry_run:
            for i, (a, b) in enumerate(zip(text.split("\n"), new.split("\n")), 1):
                if a != b and changed_files <= 3:
                    print(f"  {f.as_posix()}:{i}")
                    print(f"    - {a.strip()[:88]}")
                    print(f"    + {b.strip()[:88]}")
                    break
        else:
            f.write_text(new, encoding="utf-8")

    if protected_before != protected_after:
        print(f"ABORT: protected character count changed "
              f"({protected_before} -> {protected_after})", file=sys.stderr)
        return 1

    verb = "would convert" if args.dry_run else "converted"
    print(f"\n{verb} {total} dashes across {changed_files} files")
    print(f"protected chars (ー 一 − － ‐) intact: {protected_before}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
