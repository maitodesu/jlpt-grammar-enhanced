"""Apply our editorial overlay to the raw source scope, producing the syllabus
the writing agents actually work from.

Three files, three responsibilities:

    docs/syllabus.json        what jlptgrammarlist.neocities.org lists. Pure
                              extraction, no judgment. Regenerate with
                              extract_syllabus.py; never hand-edit.
    docs/overlay.json         our decisions: what to add, move, merge, split,
                              relabel, and what pedagogical order to teach in.
                              Hand-maintained, reviewable in isolation.
    docs/book-syllabus.json   the result. Generated; never hand-edit.

Keeping them apart matters because the source turned out to be unreliable (it has
no page for を, the direct object particle, at any level). Anyone auditing this
book needs to be able to see exactly which scope decisions were ours.
"""
import json
import sys
import unicodedata
from pathlib import Path

RAW = Path("docs/syllabus.json")
OVERLAY = Path("docs/overlay.json")
OUT = Path("docs/book-syllabus.json")

# Levels this book covers.
LEVELS = ("n5", "n4", "n3", "n2", "n1")


def slugify(term, sense=None):
    """Must stay byte-identical to extract_syllabus.slugify -- overlay entries
    and source entries have to produce the same slug for the same term, or a
    move/merge silently creates a second page instead of relocating one."""
    import re
    s = unicodedata.normalize("NFKC", term)
    s = s.replace("～", "").replace("〜", "").replace("~", "")
    s = re.sub(r"[\s/／]+", "-", s.strip())
    s = re.sub(r"[^\w぀-ヿ一-鿿○-]", "", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return f"{s}-{sense}" if sense else s


def key(term, sense=None, level=None):
    """Pool key. The level MUST be part of it: four headwords appear at two
    levels each (くらい/ぐらい, こと, ということ, という), and keying on term
    alone made the later level silently overwrite the earlier one -- dropping
    four real pages out of the book without any error."""
    base = f"{term}#{sense}" if sense else term
    return f"{level}:{base}" if level else base


def load():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
    return raw, overlay


def build(raw, overlay):
    problems = []

    # index every source entry by term so moves/merges/relabels can find it
    # Index *all* source levels: a move pulls entries down from N2, so the
    # source entry must be findable even though N2 is never emitted.
    pool = {}
    for level in raw:
        for item in raw[level]:
            item = dict(item, level=level, origin="source")
            pool[key(item["term"], item["sense"], level)] = item

    def find(k):
        """Overlay operations name a bare term (optionally 'n3:term' to
        disambiguate). Resolve to the matching pool keys."""
        if ":" in k and k.split(":", 1)[0] in raw:
            return [k] if k in pool else []
        return [pk for pk in pool if pk.split(":", 1)[1] == k]

    def take(k, what):
        hits = find(k)
        if not hits:
            problems.append(f"{what}: no source entry {k!r}")
            return None
        if len(hits) > 1:
            problems.append(f"{what}: {k!r} is ambiguous across levels {sorted(h.split(':')[0] for h in hits)}"
                            f" -- qualify it as 'n3:{k}'")
            return None
        return pool[hits[0]]

    # --- drop: entries we decided not to write a page for --------------------
    for k in overlay.get("drop", []):
        if take(k, "drop"):
            for pk in find(k):
                pool.pop(pk)

    # --- relabel: fix a wrong or misleading gloss ----------------------------
    for k, fix in overlay.get("relabel", {}).items():
        item = take(k, "relabel")
        if item:
            item["gloss"] = fix.get("gloss", item["gloss"])
            if "term" in fix:
                item["term"] = fix["term"]
            item["editorial"] = fix.get("why", "gloss corrected")

    # --- move: source filed it at the wrong level ---------------------------
    for k, target in overlay.get("move", {}).items():
        item = take(k, "move")
        if item:
            item["moved_from"] = item["level"]
            item["level"] = target

    # --- merge: several source entries become one page ----------------------
    for spec in overlay.get("merge", []):
        parts = [take(k, "merge") for k in spec["from"]]
        parts = [p for p in parts if p]
        if not parts:
            continue
        for p in parts:
            pool.pop(key(p["term"], p["sense"], p["level"]), None)
        merged_level = spec.get("level", parts[0]["level"])
        pool[key(spec["term"], None, merged_level)] = {
            "term": spec["term"],
            "sense": None,
            "gloss": spec["gloss"],
            "level": merged_level,
            "origin": "merged",
            "merged_from": [p["term"] + (f" {p['sense']}" if p["sense"] else "")
                            for p in parts],
            "editorial": spec.get("why", ""),
        }

    # --- split: one source entry becomes several pages ----------------------
    for spec in overlay.get("split", []):
        item = take(spec["from"], "split")
        if not item:
            continue
        for pk in find(spec["from"]):
            pool.pop(pk)
        for part in spec["into"]:
            part_level = part.get("level", item["level"])
            pool[key(part["term"], None, part_level)] = {
                "term": part["term"],
                "sense": None,
                "gloss": part["gloss"],
                "level": part_level,
                "origin": "split",
                "split_from": item["term"],
                "editorial": spec.get("why", ""),
            }

    # --- add: patterns the source omits entirely ----------------------------
    for level, items in overlay.get("add", {}).items():
        for entry in items:
            k = key(entry["term"], None, level)
            if k in pool:
                problems.append(f"add: {entry['term']!r} already present, skipped")
                continue
            pool[k] = {
                "term": entry["term"],
                "sense": None,
                "gloss": entry["gloss"],
                "level": level,
                "origin": "added",
                "editorial": entry.get("why", "absent from source list"),
            }

    # --- kind: which template a page uses -----------------------------------
    adverbs = set(overlay.get("adverbs", []))
    # Patterns archaic or register-marked enough that a learner should be told
    # to recognise them and not produce them. Mostly N1 literary forms.
    warn = set(overlay.get("warn", []))
    for k, item in pool.items():
        item["kind"] = "adverb" if item["term"] in adverbs else "grammar"
        item["topic_page"] = not item["gloss"]
        if item["term"] in warn:
            item["recognise_only"] = True

    # --- pedagogical order --------------------------------------------------
    # Groups are taught in the order listed; within a group, source (kana) order
    # is kept. Anything unassigned lands in a trailing group and is reported --
    # silence there would mean a pattern quietly teaching last.
    out = {}
    for level in LEVELS:
        groups = overlay.get("order", {}).get(level, [])
        assigned = {}
        for gi, group in enumerate(groups):
            for ti, term in enumerate(group["terms"]):
                if term in assigned:
                    problems.append(f"order/{level}: {term!r} in two groups")
                assigned[term] = (gi, ti, group["title"])

        items = [i for i in pool.values() if i["level"] == level]
        unplaced = sorted({i["term"] for i in items if i["term"] not in assigned})
        if unplaced:
            problems.append(
                f"order/{level}: {len(unplaced)} unplaced -> trailing group: "
                + ", ".join(unplaced[:12]) + ("..." if len(unplaced) > 12 else ""))

        # Position within the group is the order the terms are listed in the
        # overlay, not the source's kana order -- otherwise the group's teaching
        # sequence is thrown away and か ends up opening the book.
        fallback = (len(groups), 0, "Further patterns")
        for item in items:
            gi, ti, title = assigned.get(item["term"], fallback)
            item["group_index"], item["group_pos"], item["group"] = gi, ti, title

        items.sort(key=lambda i: (i["group_index"], i["group_pos"],
                                  i.get("file", "zzz"), i["term"]))
        for n, item in enumerate(items, 1):
            item["slug"] = slugify(item["term"], item["sense"])
            item["file"] = f"{n:03d}-{item['slug']}.md"
            item["path"] = f"src/{level}/{item['file']}"
        out[level] = items

    return out, problems


def main():
    raw, overlay = load()
    data, problems = build(raw, overlay)

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    for level in LEVELS:
        items = data[level]
        by_origin = {}
        for i in items:
            by_origin[i["origin"]] = by_origin.get(i["origin"], 0) + 1
        adverbs = sum(1 for i in items if i["kind"] == "adverb")
        print(f"{level}: {len(items):3d} pages  "
              f"({', '.join(f'{v} {k}' for k, v in sorted(by_origin.items()))}"
              f"{f', {adverbs} adverb-template' if adverbs else ''})")
    print(f"total: {sum(len(v) for v in data.values())} pages")

    paths = [i["path"] for v in data.values() for i in v]
    if len(paths) != len(set(paths)):
        problems.append("duplicate output paths")

    if problems:
        print("\nproblems:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
