# About this book

A deep-dive grammar reference covering the JLPT grammar syllabus from N5 through
N3. Every pattern gets its own page: what it means, exactly how it attaches,
worked examples with furigana, how it differs from the patterns it gets confused
with, the mistakes learners actually make, and five practice questions with
explained answers.

## Where the content comes from

**All explanations, example sentences, translations and practice questions in this
book are written for this book.** Nothing is reproduced from another source.

The *starting point* for scope - which grammar patterns exist at which JLPT
level - was the list published at
[jlptgrammarlist.neocities.org](https://jlptgrammarlist.neocities.org/), and it
deserves credit for that. It is unaffiliated with this book and has not reviewed
or endorsed it.

We departed from it substantially, and you should know how:

- **63 pages cover patterns it omits entirely**, including `を`, the direct object
  particle, which appears nowhere in its 711 entries. Also absent were こそあど,
  the question words, adjective conjugation, ましょう/ませんか and んです.
- **15 patterns were moved down from N2 to N3**, and three from N4 to N5, where
  the mainstream references (Bunpro, JLPT Sensei, Shin Kanzen Master) place them.
- **Four glosses were corrected** where the source described a different pattern.
- **The order is entirely ours.** That list is sorted by kana - its own changelog
  says "sorted alphanumerically" - which is fine for lookup and useless for study.
  Pages here are grouped by teaching topic and sequenced so nothing depends on a
  pattern taught later. Each level index keeps a kana-ordered list for lookup.

The JLPT itself is administered by the Japan Foundation and JEES, neither of which
publishes an official grammar list. Every "JLPT grammar list" - including the one
this book follows - is a community reconstruction from past papers and textbooks.
Treat the level labels as a study ordering, not a syllabus guarantee.

N3 deserves a specific warning: it was created in 2010 and, unlike the other
levels, has no pre-2010 official list behind it. Every N3 grammar list in
existence is a reconstruction, and they disagree with each other.

## Before you rely on this to study

- The example sentences are written to teach a pattern, and are natural but not
  corpus-attested. If a sentence sounds odd to a native speaker, trust them.
- Nuance claims - register, politeness, "this sounds stiff" - are the hardest part
  to get right and the most likely place for an error to hide.
- Practice-question answers are explained, but a pattern often admits more than
  one correct answer. If your answer differs and you can justify it, you may well
  be right.
- **No native or advanced speaker has reviewed these pages.** They are checked
  automatically for structure, furigana well-formedness and internal consistency,
  and those checks are thorough - but no automated check can tell you whether a
  claim about register or naturalness is *true*. Roughly 150 such claims across
  the book were flagged by their own authors as uncertain.
- If you find an error, please open an issue. Corrections are the whole point.

## Design

Built with [mdBook](https://rust-lang.github.io/mdBook/). The visual style and the
Japanese search tokenizer are adapted from
[yokubi-enhanced](https://github.com/maitodesu/yokubi-enhanced), used under
CC BY 4.0. Furigana is written as <code>&#123;f|漢字|かんじ&#125;</code> in the source and expanded to
`<ruby>` at build time by `scripts/preprocess-furigana.py`.

Book content is licensed CC BY-SA 4.0; see the `LICENSE` file in the repository
for the full terms, including the separately-licensed theme and search assets.
