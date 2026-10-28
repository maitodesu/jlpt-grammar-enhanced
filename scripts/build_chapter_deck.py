"""Build a deckrun presentation deck from one chapter of the book.

Reads the chapter's pages straight from src/ in SUMMARY.md order, turns the
book's HTML-flavoured prose into plain deckrun Markdown, and packs the blocks
onto 16:9 slides. deckrun clips anything that overflows a slide, so blocks are
measured in display columns and a slide is closed before it can run over.

Reading from src/ rather than md/ is what keeps furigana: md/ flattens the
`{f|漢字|かな}` macro to `漢字(かな)` for LLM use, while a slide can carry real
ruby text above the kanji.

Usage:
    python scripts/build_chapter_deck.py n5 1 1.25
"""
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_chapter_md import parse_level  # noqa: E402  (same SUMMARY walk)

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

# Body text fits roughly this many half-width columns per line, and this many
# lines per slide, at deckrun's default type scale on a 1600x900 canvas.
LINE_COLS = 100
# Calibrated against the roomiest themes rather than the tightest: deckrun
# clips overflow silently, and a deck outlives the theme it was written under.
SLIDE_LINES = 18
HEADING_MAX = 70
# deckrun's own lint calls more than this many bullets on one slide too dense.
MAX_BULLETS = 8


FURIGANA_RE = re.compile(r"\{f\|([^{}|\n]+)\|([^{}|\n]+)\}")
RT_RE = re.compile(r"<rt>.*?</rt>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def rubify(text: str) -> str:
    """The book's furigana macro, as the ruby the mdBook build also emits."""
    return FURIGANA_RE.sub(r"<ruby>\1<rt>\2</rt></ruby>", text)


def width(text: str) -> int:
    # Markup takes no space on screen, and a reading sits above its kanji
    # rather than beside it, so neither counts toward the line.
    visible = TAG_RE.sub("", RT_RE.sub("", text))
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in visible)


def lines_for(text: str) -> float:
    # A line carrying ruby is taller, since the reading needs room above it.
    tall = 1.45 if "<ruby>" in text else 1.0
    return max(1.0, -(-width(text) // LINE_COLS)) * tall


def inline(text: str) -> str:
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.S)
    # Backticks escape their contents, so a code span holding ruby has to stay
    # raw HTML or the reader sees the tags themselves.
    text = re.sub(r"<code>((?:(?!</code>).)*?)</code>",
                  lambda m: f"<code>{m.group(1)}</code>" if "<ruby>" in m.group(1) else f"`{m.group(1)}`",
                  text, flags=re.S)
    text = re.sub(r"</?(?:details|summary|div|pre)[^>]*>", "", text)
    return text.strip()


# ---------------------------------------------------------------- block parse

class Block:
    """One renderable unit: its Markdown text and its cost in slide lines."""

    def __init__(self, text: str, cost: float, bullets: int = 0):
        self.text = text
        self.cost = cost
        self.bullets = bullets


def example_block(jp: str, en: str) -> Block:
    jp, en = inline(jp), inline(en)
    return Block(f"{jp}<br>*{en}*", lines_for(jp) + lines_for(en) + 0.3)


def para_block(text: str) -> Block:
    text = inline(text)
    return Block(text, lines_for(text) + 0.3)


def quote_block(text: str) -> Block:
    text = inline(text)
    return Block("> " + text.replace("\n", " "), lines_for(text) + 0.8)


def row_cost(row: str) -> float:
    """A row as tall as its widest cell needs; columns share the slide width."""
    return max(1.0, -(-width(row) // LINE_COLS)) * 1.1


def table_blocks(rows: list[str], budget: float) -> list[Block]:
    """Split a table across slides when it is taller than one, header and all."""
    head, body = rows[:2], rows[2:]
    head_cost = sum(row_cost(r) for r in head) + 0.5
    out, chunk, cost = [], [], head_cost
    for row in body:
        if chunk and cost + row_cost(row) > budget:
            out.append(Block("\n".join(head + chunk), cost))
            chunk, cost = [], head_cost
        chunk.append(row)
        cost += row_cost(row)
    out.append(Block("\n".join(head + chunk), cost))
    return out


def list_block(items: list[str]) -> Block:
    text = "\n".join(f"- {i}" for i in items)
    return Block(text, sum(lines_for(i) for i in items) + 0.3 * len(items), len(items))


def is_block_markup(line: str) -> bool:
    return line.strip().startswith(("<pre>", "<div", "</", "<details", "<summary"))


def is_list_start(line: str) -> bool:
    """A real list item starts at column 0; an indented dash is a wrapped dash."""
    return bool(re.match(r"^[-*] ", line))


def parse_blocks(lines: list[str], budget: float) -> list[Block]:
    blocks: list[Block] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
        elif stripped == "<pre>":
            blocks.append(example_block(lines[i + 1], lines[i + 2]))
            i += 4
        elif stripped.startswith("<div"):
            j = i + 1
            body = []
            while j < len(lines) and lines[j].strip() != "</div>":
                body.append(lines[j])
                j += 1
            inner = " ".join(l.strip() for l in body if l.strip())
            blocks.append(quote_block(inner))
            i = j + 1
        elif stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(inline(lines[i].strip()))
                i += 1
            blocks.extend(table_blocks(rows, budget - 1.6))
        elif is_list_start(line):
            items = []
            while i < len(lines) and (is_list_start(lines[i]) or
                                      (items and lines[i].startswith("  ") and lines[i].strip())):
                text = lines[i].strip()
                if is_list_start(lines[i]):
                    items.append([text[2:]])
                else:
                    items[-1].append(text)
                i += 1
            # The book wraps an explanation under each bullet; keep it as a
            # second, quieter line rather than running it into the bullet.
            items = [inline(x[0] if len(x) == 1 else f"{x[0]}<br>*{' '.join(x[1:])}*") for x in items]
            for start in range(0, len(items), MAX_BULLETS):
                blocks.append(list_block(items[start:start + MAX_BULLETS]))
        elif stripped.startswith(("</", "<details", "<summary")):
            i += 1  # wrapper markup the book uses for layout only
        else:
            buf = [stripped]
            i += 1
            while i < len(lines) and lines[i].strip() and not is_block_markup(lines[i]) \
                    and not lines[i].strip().startswith("|") and not is_list_start(lines[i]):
                buf.append(lines[i].strip())
                i += 1
            blocks.append(para_block(" ".join(buf)))
    return blocks


# ---------------------------------------------------------------- deck layout

class Deck:
    def __init__(self, budget: float = SLIDE_LINES):
        self.slides: list[str] = []
        self.budget = budget

    def add(self, heading: str, blocks: list[Block], level: str = "##"):
        """Emit blocks under one heading, opening a new slide before overflow."""
        if not blocks:
            return
        head_cost = 1.6
        current: list[str] = []
        used = head_cost
        bullets = 0
        emitted = 0

        def flush():
            nonlocal current, used, bullets, emitted
            title = heading if emitted == 0 else f"{heading} (cont.)"
            self.slides.append(f"{level} {title}\n\n" + "\n\n".join(current))
            current, used, bullets, emitted = [], head_cost, 0, emitted + 1

        for block in blocks:
            if current and (used + block.cost > self.budget
                            or bullets + block.bullets > MAX_BULLETS):
                flush()
            current.append(block.text)
            used += block.cost
            bullets += block.bullets
        flush()

    def add_raw(self, text: str):
        self.slides.append(text)

    def render(self) -> str:
        return "\n\n---\n\n".join(self.slides) + "\n"


def style_block(font_scale: float) -> str:
    """Type scale, plus the room ruby needs and the switch that hides it.

    deckrun's own line-height leaves no space above a line, so a reading would
    otherwise overlap the line above it. `data-furigana="off"` drops the
    readings and takes that room back.
    """
    size = f"  html {{ font-size: {16 * font_scale:.1f}px; }}\n" if font_scale != 1.0 else ""
    return f"""<style>
{size}  .slide__content p, .slide__content li,
  .slide__content td, .slide__content th {{ line-height: 2.05; }}
  rt {{ font-size: 0.5em; line-height: 1.1; opacity: 0.72; font-weight: 400; }}
  :root[data-furigana="off"] rt {{ display: none; }}
  :root[data-furigana="off"] .slide__content p, :root[data-furigana="off"] .slide__content li,
  :root[data-furigana="off"] .slide__content td, :root[data-furigana="off"] .slide__content th
    {{ line-height: 1.5; }}
</style>"""


def deruby(text: str) -> str:
    """Headings keep the kanji but drop the reading: deckrun sets headings in
    tight leading, where a reading would land on top of the line above, and the
    same term carries its furigana in the body a moment later."""
    return RT_RE.sub("", text).replace("<ruby>", "").replace("</ruby>", "")


def heading_for(point: str, section: str) -> str:
    combined = f"{deruby(point)} · {deruby(section)}"
    return combined if width(combined) <= HEADING_MAX else deruby(section)


# ---------------------------------------------------------------- conversion

SECTION_RE = re.compile(r"^(#{1,4}) (.+?)\s*$")


def split_sections(lines: list[str]):
    """Yield (level, title, body_lines) for each heading in a grammar point."""
    out = []
    current = None
    for line in lines:
        m = SECTION_RE.match(line)
        if m:
            current = (len(m.group(1)), m.group(2), [])
            out.append(current)
        elif current:
            current[2].append(line)
    return out


def practice_items(body: list[str]):
    """Split a Practice section into (question_lines, answer_lines) pairs."""
    items = []
    q, a, in_answer = [], [], False
    for line in body:
        if re.match(r"^\*\*\d+\.\*\*", line.strip()):
            if any(l.strip() for l in q):
                items.append((q, a))
            q, a, in_answer = [line], [], False
        elif "<details>" in line:
            in_answer = True
        elif "</details>" in line:
            in_answer = False
        elif in_answer:
            a.append(line)
        else:
            q.append(line)
    if any(l.strip() for l in q):
        items.append((q, a))
    return items


def convert(level: str, chapter_title: str, pages: list, font_scale: float = 1.0) -> str:
    chapter_title = f"{level.upper()} - {chapter_title}"

    points = []
    for _, md_path in pages:
        if not md_path.exists():
            print(f"  ! missing {md_path}", file=sys.stderr)
            continue
        lines = rubify(md_path.read_text(encoding="utf-8")).strip().splitlines()
        m = SECTION_RE.match(lines[0]) if lines else None
        if not m:
            continue
        points.append((m.group(2), lines))

    deck = Deck(SLIDE_LINES / font_scale)
    names = [name for name, _ in points]
    deck.add(chapter_title,
             [list_block(names[i:i + MAX_BULLETS]) for i in range(0, len(names), MAX_BULLETS)],
             level="#")

    for point, lines in points:
        sections = split_sections(lines)
        _, _, intro_lines = sections[0]
        intro = parse_blocks(intro_lines, deck.budget)
        opener = [b.text for b in intro[:3]]
        deck.add_raw(f"# {deruby(point)}\n\n" + "\n\n".join(opener))
        for block in intro[3:]:
            deck.add(heading_for(point, "Overview"), [block])

        current_h2 = ""
        for lvl, title, body in sections[1:]:
            if lvl == 2:
                current_h2 = title
            if current_h2 == "Practice":
                if lvl != 2:
                    continue
                for n, (q, a) in enumerate(practice_items(body), start=1):
                    qb = parse_blocks(q, deck.budget)
                    ab = parse_blocks(a, deck.budget)
                    cost = sum(b.cost for b in qb) + sum(b.cost for b in ab) + 1.6
                    if cost <= deck.budget:
                        body_md = "\n\n".join(b.text for b in qb) + "\n\n" + \
                                  "\n\n".join("{reveal}\n" + b.text for b in ab)
                        deck.add_raw(f"## {heading_for(point, f'Practice {n}')}\n\n{body_md}")
                    else:
                        deck.add(heading_for(point, f"Practice {n}"), qb)
                        deck.add(heading_for(point, f"Practice {n} — answer"), ab)
                continue
            blocks = parse_blocks(body, deck.budget)
            if lvl == 2 and not blocks:
                continue
            deck.add(heading_for(point, title), blocks)

    # Raw HTML on slide one reaches the document, so the deck carries its own
    # styling and looks the same served by deckrun as it does exported.
    deck.slides[0] = f"{style_block(font_scale)}\n\n{deck.slides[0]}"
    return deck.render()


def main():
    if len(sys.argv) not in (3, 4):
        print("usage: build_chapter_deck.py <level, e.g. n5> <chapter number> [font scale]",
              file=sys.stderr)
        sys.exit(1)
    level, number = sys.argv[1].lower(), int(sys.argv[2])
    font_scale = float(sys.argv[3]) if len(sys.argv) == 4 else 1.0

    chapters = parse_level(level)
    if not 1 <= number <= len(chapters):
        print(f"{level} has chapters 1-{len(chapters)}", file=sys.stderr)
        sys.exit(1)
    chapter_title, pages = chapters[number - 1]

    out_dir = ROOT / "decks" / level
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[\\/:*?"<>|]', "", chapter_title).strip()
    out_path = out_dir / f"{number:02d} - {safe}.md"
    deck = convert(level, chapter_title, pages, font_scale)
    out_path.write_text(deck, encoding="utf-8")
    print(f"{out_path.name} ({len(pages)} pages, {deck.count(chr(10) + '---' + chr(10)) + 1} slides)")


if __name__ == "__main__":
    main()
