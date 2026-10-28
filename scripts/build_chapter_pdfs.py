"""Build chapter-wise PDFs for a JLPT level from the built mdbook site.

Reads src/SUMMARY.md to find each level's chapter groups (the unlinked
`- [Group Name]()` headings) and the pages under them, prints each page's
already-built HTML (book/<level>/NNN-xxx.html) to a temp PDF via headless
Edge (relies on mdbook's own print.css for a clean layout), then merges each
chapter's page PDFs into one PDF per chapter.

Requires `mdbook build` to have been run first (book/ must exist).

Usage:
    python scripts/build_chapter_pdfs.py n5
"""
import re
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "src" / "SUMMARY.md"
BOOK = ROOT / "book"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

LINK_RE = re.compile(r"^(\s*)- \[(.*?)\]\((.*?)\)\s*$")


def parse_level(level: str):
    """Return [(chapter_title, [(page_title, html_path), ...]), ...] for one level."""
    lines = SUMMARY.read_text(encoding="utf-8").splitlines()
    header = f"# {level.upper()} -"
    start = next(i for i, l in enumerate(lines) if l.startswith(header))
    # find next top-level heading after start
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
            # chapter group heading, e.g. "  - [Saying what something is]()"
            current = (title, [])
            chapters.append(current)
        elif depth == 2 and href:
            # page under current chapter group
            html_path = BOOK / Path(href).with_suffix(".html").as_posix().replace("./", "")
            current[1].append((title, html_path))
    return chapters


def print_to_pdf(html_path: Path, pdf_path: Path):
    uri = "file:///" + urllib.parse.quote(str(html_path).replace("\\", "/"))
    subprocess.run(
        [
            EDGE,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            uri,
        ],
        check=True,
        capture_output=True,
    )


def slugify(title: str, n: int) -> str:
    safe = re.sub(r"[\\/:*?\"<>|]", "", title).strip()
    return f"{n:02d} - {safe}.pdf"


def main():
    if len(sys.argv) != 2:
        print("usage: build_chapter_pdfs.py <level, e.g. n5>", file=sys.stderr)
        sys.exit(1)
    level = sys.argv[1].lower()

    if not BOOK.exists():
        print("book/ not found — run `mdbook build` first", file=sys.stderr)
        sys.exit(1)

    chapters = parse_level(level)
    if not chapters:
        print(f"no chapters found for level {level!r}", file=sys.stderr)
        sys.exit(1)

    out_dir = ROOT / "pdf" / level
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for i, (chapter_title, pages) in enumerate(chapters, start=1):
            merger = pypdf.PdfWriter()
            for j, (page_title, html_path) in enumerate(pages):
                if not html_path.exists():
                    print(f"  ! missing {html_path}", file=sys.stderr)
                    continue
                page_pdf = tmp_dir / f"{i:02d}-{j:03d}.pdf"
                print_to_pdf(html_path, page_pdf)
                reader = pypdf.PdfReader(page_pdf)
                for page in reader.pages:
                    merger.add_page(page)
            merger.add_metadata({"/Title": f"{level.upper()} - {chapter_title}"})
            out_path = out_dir / slugify(chapter_title, i)
            with open(out_path, "wb") as f:
                merger.write(f)
            print(f"[{i:02d}/{len(chapters)}] {chapter_title} -> {out_path.relative_to(ROOT)} ({len(merger.pages)} pages)")


if __name__ == "__main__":
    main()
