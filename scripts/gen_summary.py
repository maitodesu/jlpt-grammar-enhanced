"""Regenerate src/SUMMARY.md and the per-level landing pages.

Two orderings, deliberately:

  SUMMARY.md      pedagogical -- grouped by teaching topic, in the sequence a
                  learner should meet them. This is the study path.
  src/nN/index.md kana order -- a flat lookup index for "what does this mean".

The source list is kana-ordered only (its own changelog says "sorted
alphanumerically"), which puts は at position 45 of N5 and opens with いちばん.
That is fine for looking a pattern up and useless for learning, hence the split.

This script is the only thing that writes SUMMARY.md. Writing agents must never
edit it by hand -- two agents finishing at once would clobber each other.
"""
import json
import re
import unicodedata
from pathlib import Path

LEVELS = [
    ("n5", "N5 - Beginner"),
    ("n4", "N4 - Upper Beginner"),
    ("n3", "N3 - Intermediate"),
    ("n2", "N2 - Upper Intermediate"),
    ("n1", "N1 - Advanced"),
]

SMALL_KANA = str.maketrans("ぁぃぅぇぉっゃゅょゎ", "あいうえおつやゆよわ")


def kana_key(term):
    """Collation key for the lookup index: katakana folded to hiragana, dakuten
    and small kana ignored, so が sorts with か and きゃ with きや -- the same
    convention a Japanese dictionary index uses."""
    s = unicodedata.normalize("NFKD", term)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)
    return (s.translate(SMALL_KANA), term)


FURI = re.compile(r"\{f\|([^|{}]*)\|[^|{}]*\}")
BASE = r"\g<1>"  # keep the kanji, drop the reading


def title_of(item):
    """Prefer the page's own H1 -- the writing agent picks a clearer descriptor
    than the source gloss, and a divergent sidebar label is confusing.

    Furigana is stripped to its base text: the preprocessor rewrites chapter
    content only, so a `{f|...}` group reaching SUMMARY.md renders literally in
    the sidebar. Stripping here means a page cannot break the nav."""
    p = Path(item["path"])
    if p.exists():
        m = re.match(r"#\s+(.+)", p.read_text(encoding="utf-8").lstrip())
        if m:
            return FURI.sub(BASE, m.group(1).strip())
    if item.get("sense"):
        return f"{item['term']} - {item['gloss']}"
    return item["term"]


def main():
    data = json.loads(Path("docs/book-syllabus.json").read_text(encoding="utf-8"))
    src = Path("src")

    lines = ["# Summary", "", "[About this book](./about.md)", "", "---", ""]
    written = total = 0

    for level, label in LEVELS:
        items = data.get(level, [])
        total += len(items)
        # Only link pages that exist, so a partially-built book still builds.
        live = [i for i in items if (src / level / Path(i["file"])).exists()]
        written += len(live)

        lines += [f"# {label}", "", f"- [{label}](./{level}/index.md)"]

        group = None
        for item in live:
            if item["group"] != group:
                group = item["group"]
                # Draft entry (empty link): mdBook rejects a SUMMARY that
                # links the same file twice, and a group is a heading, not a page.
                lines.append(f"  - [{group}]()")
            lines.append(f"    - [{title_of(item)}](./{level}/{item['file']})")
        lines.append("")

        landing = [f"# {label}", "",
                   f"{len(live)} of {len(items)} pages written.", "",
                   "Listed here in kana order for lookup. The sidebar follows the",
                   "teaching order instead.", ""]
        for item in sorted(live, key=lambda i: kana_key(i["term"])):
            landing.append(f"- [{title_of(item)}](./{item['file']})")

        (src / level).mkdir(parents=True, exist_ok=True)
        (src / level / "index.md").write_text("\n".join(landing) + "\n", encoding="utf-8")

    (src / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"SUMMARY.md written: {written}/{total} pages exist")


if __name__ == "__main__":
    main()
