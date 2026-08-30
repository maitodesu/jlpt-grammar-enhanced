# JLPT Grammar - Enhanced

A chapter-wise [mdBook](https://rust-lang.github.io/mdBook/) grammar reference
covering the JLPT N5 - N3 grammar syllabus, one page per grammar point.

Each page carries: meaning, a full formation table, 6 - 10 graded examples with
furigana and translations, nuance and register notes, contrast against the
patterns it gets confused with, common mistakes, and five practice questions with
collapsible explained answers.

## Content

All prose, examples and questions are original to this book. The *syllabus* - which
patterns belong to which level - follows
[jlptgrammarlist.neocities.org](https://jlptgrammarlist.neocities.org/); see
[`src/about.md`](src/about.md) for full attribution.

## Build

```sh
cargo install mdbook          # or: brew install mdbook
mdbook serve --open           # needs python3 on PATH for the furigana preprocessor
```

## Layout

```
docs/syllabus.json      scope index: pattern -> level -> file path
docs/STYLE.md           the spec every page is written against
scripts/extract_syllabus.py   builds syllabus.json from a source snapshot
scripts/gen_summary.py        regenerates SUMMARY.md + level landing pages
scripts/check_pages.py        structural verifier (run before publishing)
src/nN/NNN-<pattern>.md       one grammar point
style/ js/              theme + Japanese search tokenizer
```

`src/SUMMARY.md` and `src/nN/index.md` are **generated**. Edit the syllabus or add
pages, then re-run `scripts/gen_summary.py`.

## Licence

Book content: CC BY-SA 4.0. Reused theme/search assets: CC BY 4.0. See
[`LICENSE`](LICENSE).
