"""Build the syllabus index from a local snapshot of jlptgrammarlist.neocities.org.

Only the *scope* is taken from the source: which grammar pattern belongs to which
JLPT level, and the short gloss that disambiguates homographs (が 1 vs が 2).
Nothing else is carried over -- every explanation, example sentence and practice
question in this book is written from scratch. See docs/STYLE.md.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

LEVELS = ("n5", "n4", "n3", "n2", "n1")

ITEM = re.compile(r'<div class="item">(.*?)(?=<div class="item">|$)', re.S)
TERM = re.compile(r'<span class="term">(.*?)</span>', re.S)
SUP = re.compile(r"<sup>(\d+)</sup>")
TAGS = re.compile(r"<[^>]+>")


def strip_tags(s):
    return TAGS.sub("", s).replace("&amp;", "&").strip()


def slugify(term, sense):
    """Filesystem-safe, stable, and readable-ish. Kana/kanji are kept as-is:
    mdBook serves UTF-8 paths fine and it keeps the tree greppable."""
    s = unicodedata.normalize("NFKC", term)
    s = s.replace("～", "").replace("〜", "").replace("~", "")
    s = re.sub(r"[\s/／]+", "-", s.strip())
    # U+25CB is not punctuation here: the source writes "しか○○ない"
    # to mean material intervenes. Dropping it collides with N3's plain
    # "しかない", and "つ○○つ" (N1) with "つつ" (N2).
    s = re.sub(r"[^\w぀-ヿ一-鿿○-]", "", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return f"{s}-{sense}" if sense else s


def parse(html):
    out = {}
    parts = re.split(r'class="grammar-list (n[54321])"', html)
    for i in range(1, len(parts), 2):
        level, body = parts[i], parts[i + 1]
        items = []
        for chunk in ITEM.findall(body):
            m = TERM.search(chunk)
            if not m:
                continue
            raw = m.group(1)
            sense = SUP.search(raw)
            term = strip_tags(SUP.sub("", raw))
            # The gloss is the bare text between </span> and the first <div>.
            after = chunk[m.end():]
            after = re.sub(r'^\s*<span class="common">.*?</span>', "", after, flags=re.S)
            gloss = strip_tags(after.split("<div")[0])
            if not term:
                continue
            items.append({
                "term": term,
                "sense": int(sense.group(1)) if sense else None,
                "gloss": gloss,
                "slug": slugify(term, sense.group(1) if sense else None),
            })
        out[level] = items
    return out


def main():
    src = Path(sys.argv[1])
    data = parse(src.read_text(encoding="utf-8"))

    # A few entries ("Volitional Form", "Transitive & Intransitive Verbs") are
    # topic headers that cross-link out instead of carrying a gloss. They are
    # still real grammar to teach, so keep them and flag them for the writer.
    for items in data.values():
        for item in items:
            item["topic_page"] = not item["gloss"]

    # Deliberately no file/path here. This file records what the source lists,
    # nothing more. Output paths depend on the editorial overlay and are decided
    # by build_syllabus.py -- duplicating stale ones here invites someone to
    # follow them and create pages at dead filenames.
    for level, items in data.items():
        for n, item in enumerate(items, 1):
            item["source_index"] = n

    dupes = {
        level: [q for q in {i["slug"] for i in items}
                if sum(1 for i in items if i["slug"] == q) > 1]
        for level, items in data.items()
    }
    for level, ds in dupes.items():
        for d in ds:
            print(f"WARN duplicate slug in {level}: {d}", file=sys.stderr)

    Path("docs/syllabus.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    for level in LEVELS:
        print(f"{level}: {len(data.get(level, []))}")


if __name__ == "__main__":
    main()
