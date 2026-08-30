"""Structural verifier for grammar-point pages.

The pages are written by LLM agents against docs/STYLE.md, so correctness is not
guaranteed by construction -- it has to be enforced after the fact. This script
checks everything that can be checked mechanically. It cannot check whether a
nuance claim is *true*; that needs a human or a reviewing agent.

Usage:
    python scripts/check_pages.py            # every page that exists
    python scripts/check_pages.py n5         # one level
    python scripts/check_pages.py src/n5/003-が-1.md ...   # specific files

Exits non-zero if any page fails.
"""
import collections
import json
import re
import sys
from pathlib import Path

# Two templates. Adverb/conjunction entries (kind == "adverb" in the syllabus)
# are words, not patterns: they have nothing to put in a Formation table and
# often no confusable twin, so STYLE.md gives them a shortened page. Checking
# them against the grammar template fails correct work.
SPEC = {
    "grammar": {
        "required": ["## Formation", "## Examples", "## Nuance & register",
                     "## Contrast", "## Common mistakes", "## Practice"],
        "examples": (6, 10),
        "questions": 5,
    },
    "adverb": {
        "required": ["## Usage", "## Examples", "## Nuance & register",
                     "## Common mistakes", "## Practice"],
        "examples": (3, 6),
        "questions": 3,
    },
}

PRE = re.compile(r"<pre>(.*?)</pre>", re.S)
DETAILS = re.compile(r"<details>(.*?)</details>", re.S)
QUESTION = re.compile(r"^\*\*(\d+)\.\*\*", re.M)
FURI = re.compile(r"\{f\|([^|{}]*)\|([^|{}]*)\}")
FURI_LOOSE = re.compile(r"\{f\|")
DIV_OPEN = re.compile(r'^<div class="(?:rule|note)">[ \t]*\n(?![ \t]*\n)', re.M)
DIV_CLOSE = re.compile(r'(?<!\n\n)^</div>[ \t]*$', re.M)
KANJI = re.compile(r"[一-鿿]")
KANA_ONLY = re.compile(r"^[぀-ゟ゠-ヿー]+$")
CODE = re.compile(r"<code>.*?</code>|`+[^`]*`+", re.S)

# Readings that are well-formed, kana-only, and simply wrong. The mechanical
# checks cannot catch these, so known offenders are listed explicitly.
# 来る is カ変: 仮定形 is くれ (来れば = くれば). こ- is the 未然形 -- 来ない, 来よう,
# 来られる -- and the ら抜き potential 来れる, both of which are correct.
KNOWN_BAD = {
    "{f|来|こ}れば": "来れば is くれば (仮定形 くれ); こ- is the 未然形",
}


def strip_furigana(s):
    return FURI.sub(r"\1", s)


def section(text, heading):
    """Body of one `## Heading` section, up to the next `## `."""
    m = re.search(rf"^{re.escape(heading)}\s*$", text, re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def check(path, seen_examples, kind="grammar"):
    text = path.read_text(encoding="utf-8")
    spec = SPEC[kind]
    MIN_EXAMPLES, MAX_EXAMPLES = spec["examples"]
    N_QUESTIONS = spec["questions"]
    errs = []

    if not text.lstrip().startswith("# "):
        errs.append("no level-1 title on first line")

    for heading in spec["required"]:
        if not re.search(rf"^{re.escape(heading)}\s*$", text, re.M):
            errs.append(f"missing section: {heading}")

    if "**Meaning**" not in text:
        errs.append("missing **Meaning** line")

    # --- examples ---
    ex_body = section(text, "## Examples")
    examples = PRE.findall(ex_body)
    if not (MIN_EXAMPLES <= len(examples) <= MAX_EXAMPLES):
        errs.append(f"{len(examples)} examples in ## Examples (want {MIN_EXAMPLES}-{MAX_EXAMPLES})")

    for raw in examples:
        lines = [l for l in raw.strip().splitlines() if l.strip()]
        if len(lines) < 2:
            errs.append(f"example block has no translation line: {raw.strip()[:40]!r}")
            continue
        jp = strip_furigana(lines[0])
        if "<b>" not in lines[0]:
            errs.append(f"example not bolding the grammar point: {jp[:40]!r}")
        # Reused sentences mean an agent copied from a neighbouring page.
        key = re.sub(r"</?b>|\s", "", jp)
        if key in seen_examples and seen_examples[key] != path:
            errs.append(f"example duplicated from {seen_examples[key].name}: {jp[:40]!r}")
        seen_examples.setdefault(key, path)

    # --- practice ---
    pr_body = section(text, "## Practice")
    qs = QUESTION.findall(pr_body)
    answers = DETAILS.findall(pr_body)
    if len(qs) != N_QUESTIONS:
        errs.append(f"{len(qs)} practice questions (want {N_QUESTIONS})")
    if len(answers) != N_QUESTIONS:
        errs.append(f"{len(answers)} answer blocks (want {N_QUESTIONS})")
    if qs and [int(q) for q in qs] != list(range(1, len(qs) + 1)):
        errs.append(f"practice questions misnumbered: {qs}")
    for a in answers:
        if len(strip_furigana(re.sub(r"<[^>]+>", "", a)).split()) < 8:
            errs.append("answer block does not explain (too short)")

    # --- furigana ---
    # A malformed group survives the preprocessor as literal text on the page.
    if len(FURI_LOOSE.findall(text)) != len(FURI.findall(text)):
        errs.append("malformed {f|...} group")
    for base, reading in FURI.findall(text):
        if not base or not reading:
            errs.append(f"empty furigana group: {{f|{base}|{reading}}}")
        elif not KANJI.search(base):
            errs.append(f"furigana on non-kanji base: {{f|{base}|{reading}}}")
        elif not KANA_ONLY.match(reading):
            errs.append(f"furigana reading is not kana: {{f|{base}|{reading}}}")

    if "〜" in text:
        n = text.count("〜")
        errs.append(f"{n}x U+301C tilde -- STYLE mandates U+FF5E (they look identical)")

    # Bare kanji. Code spans are exempt: furigana inside backticks or <code>
    # renders as literal <ruby> tags (see STYLE "Rendering traps"), so a kanji
    # quoted as a form there cannot be annotated. The H1 is exempt too -- it is
    # reused as the sidebar label, which the preprocessor never rewrites.
    body = FURI.sub("", text)
    body = CODE.sub("", body)
    body = re.sub(r"^#\s+.*$", "", body, count=1, flags=re.M)
    bare = sorted(set(KANJI.findall(body)))
    if bare:
        errs.append(f"bare kanji outside furigana: {''.join(bare[:12])}"
                    + (f" (+{len(bare)-12} more)" if len(bare) > 12 else ""))

    for tag in ("details", "pre", "div", "summary", "b", "code"):
        opens = len(re.findall(rf"<{tag}(?:\s[^>]*)?>", text))
        closes = len(re.findall(rf"</{tag}>", text))
        if opens != closes:
            errs.append(f"unbalanced <{tag}>: {opens} open, {closes} close")

    for bad, why in KNOWN_BAD.items():
        if bad in text:
            errs.append(f"known-wrong reading {bad}: {why}")

    if "【" in text:
        errs.append("literal 【...】 reading in body -- use furigana")

    # --- callouts ---
    # CommonMark needs a blank line inside an HTML block for markdown to parse.
    if DIV_OPEN.search(text):
        errs.append("<div class=...> without a blank line after it")
    if DIV_CLOSE.search(text):
        errs.append("</div> without a blank line before it")

    return errs


def main():
    syllabus = json.loads(Path("docs/book-syllabus.json").read_text(encoding="utf-8"))
    args = sys.argv[1:]

    if args and args[0] in syllabus:
        want = [Path(i["path"]) for i in syllabus[args[0]]]
    elif args:
        want = [Path(a) for a in args]
    else:
        want = [Path(i["path"]) for lvl in syllabus.values() for i in lvl]

    pages = [p for p in want if p.exists() and p.name != "index.md"]
    if not pages:
        print("no pages to check")
        return 0

    kinds = {Path(i["path"]).name: i.get("kind", "grammar")
             for lvl in syllabus.values() for i in lvl}

    seen_examples = {}
    failures = collections.OrderedDict()
    for page in sorted(pages):
        errs = check(page, seen_examples, kinds.get(page.name, "grammar"))
        if errs:
            failures[page] = errs

    for page, errs in failures.items():
        print(f"\nFAIL {page}")
        for e in errs:
            print(f"  - {e}")

    ok = len(pages) - len(failures)
    print(f"\n{ok}/{len(pages)} pages pass  ({len(seen_examples)} distinct examples)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
