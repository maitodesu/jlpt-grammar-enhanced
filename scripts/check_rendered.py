"""Check the built HTML, not the markdown source.

Some defects are only visible after rendering, and the source-level checker
cannot decide them:

  * `**bold**` fails to open when preceded by a letter and followed by `{`
    (CommonMark left-flanking). But the *same* character sequence is perfectly
    valid as a closing delimiter -- `{f|外|そと}**は**{f|暗|くら}く` is correct.
    Grepping the source for `\\S\\*\\*\\{f\\|` flags both and is useless. Literal
    asterisks surviving into rendered text are unambiguous.
  * Furigana inside a code span renders as escaped `&lt;ruby&gt;` tags.
  * A malformed `{f|...}` group survives the preprocessor as literal text.

Run after `mdbook build`. Exits non-zero on any finding.
"""
import re
import sys
from collections import Counter
from pathlib import Path

BOOK = Path("book")
TAGS = re.compile(r"<[^>]+>")
SCRIPT = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)

CHECKS = [
    ("literal ** in rendered text (bold failed to parse)", re.compile(r"\*\*")),
    ("unconverted {f|...} furigana group", re.compile(r"\{f\|")),
    ("literal 【...】 reading", re.compile(r"【")),
    ("U+301C tilde (should be U+FF5E)", re.compile("〜")),
]

# Checked against raw HTML rather than the text-only view.
RAW_CHECKS = [
    ("escaped <ruby> tag (furigana trapped in a code span)",
     re.compile(r"&lt;ruby|&lt;rt&gt;")),
    ("escaped block tag (callout did not parse)",
     re.compile(r"&lt;div class=|&lt;details&gt;|&lt;pre&gt;")),
]


def main():
    pages = sorted(BOOK.glob("n*/*.html"))
    if not pages:
        print("no rendered pages found -- run `mdbook build` first", file=sys.stderr)
        return 1

    findings = Counter()
    detail = []
    for page in pages:
        html = page.read_text(encoding="utf-8", errors="replace")
        html = SCRIPT.sub("", html)
        text = TAGS.sub("", html)

        for label, pat in CHECKS:
            n = len(pat.findall(text))
            if n:
                findings[label] += n
                detail.append(f"  {page.as_posix()}: {n}x {label}")
        for label, pat in RAW_CHECKS:
            n = len(pat.findall(html))
            if n:
                findings[label] += n
                detail.append(f"  {page.as_posix()}: {n}x {label}")

    for line in detail:
        print(line)

    if findings:
        print("\nrendered-output defects:", file=sys.stderr)
        for label, n in findings.most_common():
            print(f"  {n:5d}  {label}", file=sys.stderr)
        return 1

    print(f"{len(pages)} rendered pages clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
