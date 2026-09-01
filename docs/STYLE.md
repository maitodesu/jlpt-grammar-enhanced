# Conversion spec - JLPT Grammar, Enhanced

Every grammar-point page in this book is written against this document. Read it
end to end before writing anything, and run the self-check at the bottom before
you report finished.

## Prime directive

**Everything on the page is written by you, from your own knowledge of Japanese.**

`jlptgrammarlist.neocities.org` supplies exactly one thing: the *syllabus* - which
grammar patterns exist at which JLPT level, and a short gloss that disambiguates
homographs (`が 1` = subject marker vs `が 2` = "but"). That scope information is
in `docs/book-syllabus.json`.

Do **not** copy the source site's example sentences, its translations, or its
wording. Do not paraphrase them either. Write your own examples. The source is a
bare list; the whole value of this book is the depth it does not have.

The second directive is **correctness**. A learner will memorise what you write.
An invented particle rule or a wrong reading is worse than a thin page. If you are
not confident about a nuance, say less rather than guessing - but do not skip a
required section.

## Files

One page per grammar point. Paths come from `docs/book-syllabus.json` (`path`
field) -- use them exactly, do not invent filenames. `src/n5/007-がいる.md` etc.

Each level also has `src/nN/index.md`, a landing page: bare `#` heading, then the
link list. No orientation blurb.

## Page template

Every page has these **eight** parts, in this order. Seven carry an exact
`##` heading; **Meaning has no heading** -- it is a `**Meaning** ·` lead line
directly under the title.

### Title

```markdown
# ～ておく
```

The heading is the pattern itself. Use `～` (U+FF5E) for the attachment point when
the pattern is a suffix. For particles and standalone words, no `～`.

**Do not put furigana in the H1.** The heading is reused verbatim as the sidebar
label, and the furigana preprocessor does not run over navigation text. Give the
reading in the Meaning line instead. (`gen_summary.py` strips furigana from nav
titles as a backstop, but the page's own heading should read cleanly.)

If the point has a sense number in the syllabus, disambiguate in the title:

```markdown
# が - subject marker
```

### Meaning

One `**Meaning**` line, then one or two sentences of plain English. This is the
part a learner re-reads at 2am. Make it land.

```markdown
**Meaning** · do something in advance, in preparation for what comes next

`～ておく` frames an action as *setup*. The speaker is not just doing the thing - 
they are doing it now so that later is easier.
```

### Formation

A table. One row per thing the pattern attaches to. This is the section learners
actually look up, so it must be complete: if the pattern attaches differently to
verbs, い-adjectives, な-adjectives and nouns, all four get rows.

The three column headers are fixed. If "Attaches to" reads oddly for a bare
particle, add a lead sentence above the table rather than renaming the column.

```markdown
## Formation

| Attaches to | Form | Example |
|---|---|---|
| Verb | て-form + おく | {f|読|よ}む → {f|読|よ}んでおく |
| Verb (negative) | ない-form + でおく | {f|読|よ}まないでおく |
```

Show the transformation with an arrow, not prose.

### Examples

**Six to ten** sentences, ordered easy → hard. Each one is a `<pre>` block with
the grammar point bolded, followed by the translation. Match this shape exactly:

```markdown
<pre>
{f|明日|あした}のテストのために、{f|今夜|こんや}<b>{f|勉強|べんきょう}しておく</b>。
I'll study tonight for tomorrow's test.
</pre>
```

Rules for examples:

- The **first two** must be short and use only vocabulary at or below this JLPT
  level. A learner meeting the pattern for the first time reads these.
- The **last two** should show the pattern in a realistic, longer sentence - 
  something a person would actually say.
- Each `<pre>` block is **exactly two lines**: Japanese, then English. No third
  commentary line. A blank line inside the block terminates the HTML block.
- Every example must be **yours**. The verifier fails the build if the same
  sentence appears on two different pages.
- Vary the subject, the register, and the tense across the set. Do not write eight
  sentences that are all `私は…ます`.
- Bold **only** the grammar point being taught, with `<b>`.
- Furigana on **every kanji on the page** - examples, tables, callouts,
  practice questions, and English prose alike. A bare kanji anywhere is a defect.
  Written `{f|漢字|かんじ}`. Per-character where the reading splits
  per character (`{f|食|た}べる`), per-word where it does not (`{f|明日|あした}`).
  Getting this wrong renders a wrong reading as if it were authoritative - check it.
- The English line is a natural translation, not a gloss. Don't write "As for me,
  tomorrow's test for the sake of, tonight study-in-advance."

### Nuance & register

Prose. What does this pattern *feel* like? Cover whatever applies:

- politeness level, and how it changes in ます/です form
- casual contractions (`～ておく` → `～とく`) - these are extremely common in speech
  and learners are blindsided by them
- spoken vs written, male/female or age-marked usage, formality of the surrounding
  register
- whether it sounds stiff, rude, childish, or old-fashioned in the wrong context

If a pattern is genuinely register-neutral, say so in a sentence and move on.

### Contrast

The single highest-value section. Compare against the patterns learners actually
confuse this one with. Write **exactly three** `###` subsections. Use a
`<div class="rule">` callout for the rule of thumb, then examples showing
minimal pairs.

```markdown
## Contrast

### ～ておく vs ～てある

<div class="rule">

**Rule of thumb** - `～ておく` is about the *doing*; `～てある` is about the
*resulting state*.

</div>

<pre>
{f|窓|まど}を<b>{f|開|あ}けておいた</b>。
I opened the window (deliberately, ahead of time).
</pre>
```

The blank lines inside `<div>` are mandatory - without them markdown will not
parse inside the div and you get raw HTML on the page.

### Common mistakes

A short list. Each item: the wrong sentence, marked, then why. Use ❌ / ✅.

```markdown
## Common mistakes

- ❌ {f|食|た}べるておく → ✅ {f|食|た}<b>べておく</b>
  `おく` attaches to the て-form, not the dictionary form.
```

Draw these from mistakes learners genuinely make - interference from English,
confusion with a similar pattern, wrong conjugation base. Two to five items.

### Practice

Exactly **five** questions. Mix the types - do not write five fill-in-the-blanks:

1. fill in the blank
2. choose between this pattern and a confusable one
3. translate EN → JA
4. spot and fix the error
5. explain the nuance difference between two given sentences

Each answer goes in a collapsible block, immediately under its question:

```markdown
## Practice

**1.** {f|出|で}かける{f|前|まえ}に、{f|窓|まど}を{f|閉|し}め____。

<details><summary>Answer</summary>

{f|閉|し}め**ておく**（or 閉めておきます）

`～ておく` because the window is being closed *in preparation* for going out.

</details>
```

The blank line after `<summary>` and before `</details>` is mandatory, same reason
as the div callouts.

Answers must **explain**, not just state. One or two sentences of why.

## Rendering traps -- read this twice

Both of these fail **silently**. `mdbook build` succeeds, no warning is printed,
and the page is wrong. They were found the hard way; do not rediscover them.

### 1. Never open `**bold**` immediately before a `{f|` token

```markdown
BAD   を**{f|買|か}いたい**      renders as literal asterisks on the page
GOOD  を<b>{f|買|か}いたい</b>
```

CommonMark's left-flanking rule: the `**` is preceded by a letter and followed by
`{`, which counts as punctuation, so it cannot open emphasis. **Use `<b>...</b>`
for every bolded Japanese span.** Reserve `**` for English.

This bites hardest in practice answers, which is exactly where you will write
`**{f|`.

### 2. Never put furigana inside backticks

```markdown
BAD   `{f|見|み}える`        reader sees the literal <ruby> tags
GOOD  <code>{f|見|み}える</code>
```

The furigana preprocessor rewrites the raw markdown *before* it is parsed, so the
ruby HTML lands inside the code span and gets escaped. **Use `<code>...</code>`
whenever the content contains a `{f|` group.** Backticks are safe only for
kana-only or romaji strings.

### 3. Never break a line in the middle of a Japanese run

A markdown soft line break inside Japanese renders as a visible space. Wrap
English prose freely; keep each Japanese sentence on one line however long it is.

### 4. Use `～` U+FF5E, never `〜` U+301C

They are visually identical and will silently fragment titles and anchors.


## Formatting reference

| Thing | Markup |
|---|---|
| Furigana | `{f|漢字|かんじ}` → ruby |
| Example block | `<pre>` … `</pre>`, Japanese line then English line |
| Grammar point in example | `<b>…</b>` |
| Any bolded Japanese | `<b>…</b>` -- never `**` |
| Inline pattern name with kanji | `<code>…</code>` -- never backticks |
| Rule callout | `<div class="rule">` + blank lines |
| Side note | `<div class="note">` + blank lines |
| Wrong / right | ❌ / ✅ |

Do not use colour to carry meaning - use bold.

Never write a literal `【…】` reading in the page body; that is what furigana is for.

## Cross-page links

**Do not link to other pages in this book.** Pages are written in parallel; a link
to a sibling that has not been written yet is a dead link, and `gen_summary.py`
only lists files that exist. Name the other pattern in prose instead.

## Adverb pages

Entries whose `kind` is `"adverb"` in `docs/book-syllabus.json` are adverbs or
conjunctions rather than grammar points -- いちばん, まだ, もう, たとえば, つまり and
similar. They use a **shortened template**: title, Meaning, Usage (prose, in place
of Formation), **four** examples, Nuance & register, Common mistakes, and **three**
practice questions. No Formation table and no Contrast section unless the word
genuinely has a near-twin worth separating (たとえば vs つまり does; ずっと does not).

Do not pad a Formation table for a word that does not conjugate or attach.


## House style

Settled decisions. Several agents hit each of these independently; follow them so
the book does not contradict itself page to page.

**Readings where usage is split.** Use the dominant modern spoken form, which is
also NHK's:

| Write | Not | Note |
|---|---|---|
| じゅっぷん (十分) | じっぷん | じっぷん is the traditionally prescribed reading; say so in a note if the page is about counters |
| さんじゅっぷん (三十分) | さんじっぷん | |
| さんがい (三階) | さんかい | |

If a page's whole subject is the reading itself, give both and say which is
prescribed. Otherwise pick the table's form and move on.

**Verb class labels.** Use **う-verb / る-verb** as the primary terms, with a
one-line note giving 五段/godan/Group 1 and 一段/ichidan/Group 2 the first time a
page needs them. Do not switch systems mid-page.

**Sociolinguistic claims** - "sounds feminine", "leans male", "sounds dated",
"more common in writing" - are tendencies, not rules. Write them as tendencies.
"`だろう` leans male in casual speech" is fine; "women do not use `だろう`" is not.
The same goes for politeness rankings among near-synonyms: give the ordering, but
do not present a soft gradient as a hard rule.

### Readings that pass every check and are still wrong

A furigana group can be well-formed, kana-only, attached to a real kanji, and
simply incorrect. No mechanical check catches this. Every one of the following
was a real defect found in this book after an agent reported its pages verified:

| Wrong | Right | Why |
|---|---|---|
| 来れば = これば | **くれば** | 来る is カ変: 仮定形 is くれ. こ- is the 未然形 (来ない, 来よう, 来られる) and the ら抜き potential 来れる |
| 十個 = じゅうこ | **じゅっこ** | counter gemination |
| 予定通り = よていとおり | **よていどおり** | rendaku after a noun |
| 何でも = なにでも | **なんでも** | 何 is なん before で/だ/の, なに before が/か |
| 起こる = {f&#124;起&#124;おこ}る | {f&#124;起&#124;お}こる | the okurigana こ is outside the kanji |
| 整備不足 = ふそく | **ぶそく** | rendaku |
| 五つ = ごつ | **いつつ** | native numeral |

Check these classes specifically before reporting:

- **Irregular stems.** 来る and する change vowel by form. Verify each occurrence
  against its actual form, not against the last one you wrote.
- **Counters.** Gemination and rendaku (一本 いっぽん, 三本 さんぼん, 六本 ろっぽん,
  十回 じゅっかい, 三階 さんがい, 一人 ひとり, 二人 ふたり, 八つ やっつ).
- **Homographs.** 話 はな/はなし, 出 で/だ, 入 い/はい, 開 あ/ひら, 遅 おく/おそ,
  上 あ/うえ/のぼ, 中 なか/ちゅう/じゅう, 後 あと/ご/のち/うし, 通 とお/かよ.
- **Okurigana boundaries.** The furigana base is the kanji only; kana that belongs
  to the word goes outside the group.

`scripts/check_pages.py` carries a `KNOWN_BAD` table of specific wrong readings
already found. Add to it when you find a new one -- that is how this class of
defect gets caught for everyone else.

**When you are not sure, say less.** A page that omits a subtle nuance is a thin
page. A page that asserts a wrong one teaches an error to someone who will repeat
it. Prefer the first, and name the uncertainty in your report.

## Recognise-only pages

Some N1 and a few N2 patterns are archaic, literary, or so register-marked that a
learner who produces them will sound wrong -- 〜んがため, 〜べからず, 〜まじき,
〜ごとき, 〜たまえ. Your assignment table marks these **RECOGNISE-ONLY**.

Those pages are written to be *read past*, not deployed. Requirements:

- Open the Nuance & register section with an explicit warning: where the pattern
  actually appears (legal text, signage, fiction, speeches, set phrases), and that
  the reader should recognise it and use the ordinary modern equivalent instead.
  Name that equivalent.
- Put the modern equivalent in the Contrast section. For 〜べからず that is
  〜てはいけない; for 〜んがため it is 〜ために. The comparison *is* the page.
- Examples should be the kind of sentence the pattern really occurs in -- a sign, a
  proverb, a line of narration -- not invented conversational sentences that no
  one would say.
- Practice questions should test recognition and register judgement ("where would
  you see this?", "rewrite it in modern Japanese"), not production.

Do not soften this into "somewhat formal". If a form would be strange in speech,
say so plainly.

### Two reasons a page carries the flag

The flag marks *do not produce this*, but the reason differs, and the page must say
which applies. Getting this wrong is a factual error, not a stylistic one.

**Archaic** -- the form is dead in modern speech and survives in signage, law,
proverbs and literary narration: 〜べからず, 〜まじき, 〜んがため, 〜ごとく, たまえ.
Here "you will never say this" is simply true.

**Register-locked** -- the form is alive and current, but confined to a narrow
habitat, and a learner who uses it outside that habitat sounds wrong rather than
old-fashioned: 〜ずくめ (collocation-locked), ときたら (performed exasperation),
わ〜わで (stylised grumbling), たはいいが (wry self-deprecating anecdote), ものか
(emotionally loaded), べくして (commentary and sports reporting).

For these, the hazard is **coining new uses**, not the form's age. Say what the
live habitat is, name the collocations that actually occur, and warn against
extending the pattern -- do not call it archaic, because that is false and a
reader will hear it in ordinary conversation the same week.

If your table marks a page recognise-only and you judge the honest description to
be the second kind, write it that way and say so in your report.

## Stay inside your assignment

Write **only** the files your assignment table lists. This is not bureaucracy --
15 or more agents write in parallel, and an agent that ran a bulk regex across
files it did not own during the N4 pass corrupted bold delimiters on 14 lines and
invalidated other agents' in-memory copies of those files. It repaired the damage,
but it was caught by luck, not by design.

If you spot a defect in someone else's page, **report it, do not fix it.**

Where the assignment table and this document or your prompt's prose disagree, the
**table wins**. Agents have correctly caught prompt errors this way more than once
-- a miscounted page total, a pattern named in prose but absent from the table, and
a reading "correction" that was backwards. Trust the table and say what looked wrong.


## Self-check before you report finished

1. Do all eight parts exist -- Meaning as a lead line, the other seven as exact
   `##` headings? (Adverb pages: the shortened set.)
2. Are there 6 - 10 examples, and exactly 5 practice questions?
3. Is every kanji anywhere on the page furigana-annotated, and is every
   reading correct? (Re-read them. This is the most common defect.)
4. Did you write every sentence yourself, rather than lifting it from the source
   site or from another page in this book?
5. Would a learner who read only this page be able to use the pattern correctly in
   conversation - and would they know when *not* to use it?
6. Did you use `<b>` rather than `**` for every bolded Japanese span, and
   `<code>` rather than backticks anywhere furigana appears?
7. Does `python scripts/check_pages.py <your files>` pass, and `mdbook build`
   succeed with no warnings?
8. Does `python scripts/check_rendered.py` pass? It inspects the **built HTML**
   and is the only thing that catches bold which failed to parse and furigana
   trapped in a code span. Source-level grepping cannot distinguish those from
   correct usage. If it reports defects on pages that are not yours, say so in
   your report rather than editing them.
