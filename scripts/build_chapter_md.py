"""Build chapter-wise plain-Markdown files for a JLPT level, for feeding to
LLM agents (small, structured, no HTML/PDF overhead).

Reads src/SUMMARY.md for the level's chapter groups and pages, concatenates
each chapter's raw .md source in SUMMARY order, and flattens the furigana
macro `{f|漢字|かな}` to `漢字(かな)` since ruby markup has no plain-text
equivalent an LLM benefits from.

Usage:
    python scripts/build_chapter_md.py n5
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "src" / "SUMMARY.md"
SRC = ROOT / "src"

LINK_RE = re.compile(r"^(\s*)- \[(.*?)\]\((.*?)\)\s*$")
FURIGANA_RE = re.compile(r"\{f\|([^|}]*)\|([^}]*)\}")


def parse_level(level: str):
    """Return [(chapter_title, [(page_title, md_path), ...]), ...] for one level."""
    lines = SUMMARY.read_text(encoding="utf-8").splitlines()
    header = f"# {level.upper()} -"
    start = next(i for i, l in enumerate(lines) if l.startswith(header))
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("# "):
            end = i
            break

    chapters = []
    current = None
    for line in lines[start:end]:
        m = LINK_RE.match(line)
        if not m:
            continue
        indent, title, href = m.groups()
        depth = len(indent) // 2
        if depth == 1:
            current = (title, [])
            chapters.append(current)
        elif depth == 2 and href:
            md_path = SRC / Path(href).as_posix().replace("./", "")
            current[1].append((title, md_path))
    return chapters


def flatten_furigana(text: str) -> str:
    return FURIGANA_RE.sub(lambda m: f"{m.group(1)}({m.group(2)})", text)


def slugify(title: str, n: int) -> str:
    safe = re.sub(r"[\\/:*?\"<>|]", "", title).strip()
    return f"{n:02d} - {safe}.md"


def main():
    if len(sys.argv) != 2:
        print("usage: build_chapter_md.py <level, e.g. n5>", file=sys.stderr)
        sys.exit(1)
    level = sys.argv[1].lower()

    chapters = parse_level(level)
    if not chapters:
        print(f"no chapters found for level {level!r}", file=sys.stderr)
        sys.exit(1)

    out_dir = ROOT / "md" / level
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, (chapter_title, pages) in enumerate(chapters, start=1):
        parts = [f"# {level.upper()} - {chapter_title}\n"]
        for page_title, md_path in pages:
            if not md_path.exists():
                print(f"  ! missing {md_path}", file=sys.stderr)
                continue
            body = flatten_furigana(md_path.read_text(encoding="utf-8")).rstrip()
            parts.append(body)
        content = "\n\n---\n\n".join(parts) + "\n"
        out_path = out_dir / slugify(chapter_title, i)
        out_path.write_text(content, encoding="utf-8")
        print(f"[{i:02d}/{len(chapters)}] {chapter_title} -> {out_path.relative_to(ROOT)} ({len(pages)} pages)")


if __name__ == "__main__":
    main()
