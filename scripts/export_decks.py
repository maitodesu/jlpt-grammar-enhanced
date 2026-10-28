"""Export every chapter deck to a standalone HTML page, plus a site index.

deckrun's HTML export inlines its stylesheet and navigation runtime, so each
page is a single file that works off any static host. The export runs through a
local deckrun editor server (`deckrun --no-open -p PORT`), which does the same
build the editor's export button does.

Usage:
    python scripts/export_decks.py <out dir> [port]
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
LEVELS = ("n5", "n4", "n3")
THEME = "paper"

SECTIONS = [
    ("Formation", "what it attaches to, and how"),
    ("Examples", "the pattern in real sentences"),
    ("Nuance &amp; register", "when it fits, and who says it"),
    ("Contrast", "how it differs from its lookalikes"),
    ("Common mistakes", "the errors worth pre-empting"),
    ("Practice", "questions, with answers you reveal"),
]


def export(markdown: str, title: str, port: int) -> str:
    payload = json.dumps({
        "markdown": markdown,
        "theme": THEME,
        "template": "classic",
        "transition": "slide",
        "title": title,
        "standalone": True,
    }).encode("utf-8")
    req = urllib.request.Request(f"http://127.0.0.1:{port}/__present", data=payload,
                                 headers={"Content-Type": "application/json"})
    path = json.loads(urllib.request.urlopen(req, timeout=300).read())["path"]
    html = urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=300).read().decode("utf-8")
    for anchor in ("</body>", "</head>"):
        if anchor not in html:
            raise RuntimeError(f"no {anchor} in export of {title}; cannot place the page chrome")
    return html.replace("</head>", HOME_PREF, 1).replace("</body>", HOME_LINK, 1)


# A deck page is otherwise a dead end: deckrun's own chrome is the tool belt
# along the bottom, so this sits top-left and stays out of the PDF.
HOME_LINK = """<a href="../index.html" id="deck-home">&#8592; all decks</a>
<style>
  #deck-home { position: fixed; top: 0.7rem; left: 0.9rem; z-index: 40;
    font: 500 0.78rem/1 ui-monospace, SFMono-Regular, Menlo, monospace;
    letter-spacing: 0.02em; color: currentColor; opacity: 0.38;
    text-decoration: none; padding: 0.35rem 0.5rem; border-radius: 4px;
    transition: opacity 0.15s ease, background 0.15s ease; }
  #deck-home:hover, #deck-home:focus-visible { opacity: 0.95; background: rgba(128,128,128,0.14); }
  @media print { #deck-home { display: none !important; } }
  #furigana-toggle { position: fixed; bottom: 2.7rem; right: 1.1rem; z-index: 40;
    font: 500 0.78rem/1 ui-monospace, SFMono-Regular, Menlo, monospace;
    color: currentColor; opacity: 0.38; cursor: pointer; user-select: none;
    background: none; border: 1px solid currentColor; border-radius: 4px;
    padding: 0.38rem 0.6rem;
    transition: opacity 0.15s ease, background 0.15s ease; }
  #furigana-toggle:hover, #furigana-toggle:focus-visible { opacity: 0.95; background: rgba(128,128,128,0.14); }
  @media print { #furigana-toggle { display: none !important; } }
</style>
<button id="furigana-toggle" type="button" aria-pressed="true">&#12405;&#12426;&#12364;&#12394; ON</button>
<script>
  (function () {
    // Deliberately click-only: readers who do not want furigana turn it off
    // once and it sticks, while every key stays free for presenting.
    var root = document.documentElement, btn = document.getElementById('furigana-toggle');
    function paint() {
      var off = root.getAttribute('data-furigana') === 'off';
      btn.textContent = '\\u3075\\u308a\\u304c\\u306a ' + (off ? 'OFF' : 'ON');
      btn.setAttribute('aria-pressed', String(!off));
    }
    btn.addEventListener('click', function () {
      var off = root.getAttribute('data-furigana') === 'off';
      if (off) root.removeAttribute('data-furigana');
      else root.setAttribute('data-furigana', 'off');
      try { localStorage.setItem('jlpt-furigana', off ? 'on' : 'off'); } catch (e) {}
      paint();
      btn.blur();
    });
    paint();
  })();
</script>
</body>"""

# Applied before the slides paint, so a reader who turned furigana off does not
# see it flash back on with every chapter they open.
HOME_PREF = """<script>
  try {
    if (localStorage.getItem('jlpt-furigana') === 'off') {
      document.documentElement.setAttribute('data-furigana', 'off');
    }
  } catch (e) {}
</script>
</head>"""


def slug(name: str) -> str:
    stem = re.sub(r"^(\d\d) - ", r"\1-", Path(name).stem)
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") + ".html"


def index_html(levels: dict) -> str:
    cards = []
    for level, chapters in levels.items():
        links = "\n".join(
            f'        <li><a href="{level}/{href}">{title}</a> '
            f'<span class="count">{slides} slides</span></li>'
            for _, title, href, slides in chapters)
        total = sum(c[3] for c in chapters)
        cards.append(f"""    <section>
      <h2>{level.upper()}</h2>
      <p class="meta">{len(chapters)} chapters · {total:,} slides</p>
      <ol>
{links}
      </ol>
    </section>""")
    path = "\n".join(f"        <li><b>{name}</b> — {gloss}</li>" for name, gloss in SECTIONS)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JLPT Grammar Decks</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ margin: 0; padding: 3rem 1.25rem 5rem; background: #f4efe7; color: #2f2a26;
         font: 17px/1.6 Georgia, "Times New Roman", serif; }}
  .wrap {{ max-width: 54rem; margin: 0 auto; }}
  h1 {{ font-size: 2.6rem; color: #9b1c2e; margin: 0 0 .4rem; letter-spacing: -.01em; }}
  .lede {{ font-size: 1.1rem; max-width: 40rem; }}
  .path {{ background: #ece3d7; border-left: 3px solid #9b1c2e; border-radius: 0 6px 6px 0;
           padding: 1rem 1.25rem; margin: 2rem 0 2.5rem; }}
  .path ul {{ margin: .6rem 0 0; padding-left: 1.2rem; }}
  .path li {{ margin: .15rem 0; }}
  section {{ margin: 2.5rem 0; }}
  h2 {{ font-size: 1.6rem; color: #9b1c2e; margin: 0 0 .1rem; }}
  .meta {{ margin: 0 0 .8rem; font-size: .95rem; opacity: .7; }}
  ol {{ padding-left: 1.4rem; margin: 0; }}
  li {{ margin: .3rem 0; }}
  a {{ color: #2f2a26; text-decoration-color: #c9b9a4; text-underline-offset: 3px; }}
  a:hover {{ color: #9b1c2e; }}
  .count {{ font-size: .85rem; opacity: .55; }}
  footer {{ margin-top: 4rem; font-size: .9rem; opacity: .75; }}
  footer a {{ color: #9b1c2e; }}
  @media (max-width: 40rem) {{ body {{ padding-top: 2rem; }} h1 {{ font-size: 2rem; }} }}
</style>
</head>
<body>
<div class="wrap">
  <h1>JLPT Grammar Decks</h1>
  <p class="lede">Every grammar point of the JLPT N5–N3 syllabus, as slides you can
  present. Each chapter is one self-contained page — arrow keys to move,
  <kbd>?</kbd> for the presenter controls.</p>

  <div class="path">
    Every grammar point walks the same short path, so a point runs about 19 slides
    and a chapter is one sitting. Nothing here is read front to back — jump to the
    point you need.
    <ul>
{path}
    </ul>
  </div>

{chr(10).join(cards)}

  <footer>
    Prose, examples and practice questions come from
    <a href="https://github.com/maitodesu/jlpt-grammar-enhanced">jlpt-grammar-enhanced</a>,
    reformatted into slides. Content is CC BY-SA 4.0; slides are rendered with
    <a href="https://github.com/arpitbbhayani/deckrun">deckrun</a> (MIT).
  </footer>
</div>
</body>
</html>
"""


def main():
    if len(sys.argv) not in (2, 3):
        print("usage: export_decks.py <out dir> [port]", file=sys.stderr)
        sys.exit(1)
    out_root = Path(sys.argv[1])
    port = int(sys.argv[2]) if len(sys.argv) == 3 else 7897

    levels = {}
    for level in LEVELS:
        chapters = sorted((ROOT / "decks" / level).glob("[0-9][0-9] - *.md"))
        if not chapters:
            continue
        (out_root / level).mkdir(parents=True, exist_ok=True)
        rows = []
        for path in chapters:
            markdown = path.read_text(encoding="utf-8")
            number, title = re.match(r"(\d\d) - (.+)", path.stem).groups()
            html = export(markdown, f"{level.upper()} · {title}", port)
            (out_root / level / slug(path.name)).write_text(html, encoding="utf-8")
            rows.append((int(number), title, slug(path.name), markdown.count("\n---\n") + 1))
            print(f"  {level}/{slug(path.name)} ({rows[-1][3]} slides, {len(html) // 1024} KB)")
        levels[level] = rows

    (out_root / "index.html").write_text(index_html(levels), encoding="utf-8")
    print(f"index.html -> {out_root}")


if __name__ == "__main__":
    main()
