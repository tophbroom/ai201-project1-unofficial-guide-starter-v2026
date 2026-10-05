# The Unofficial Guide

Devin Lin — `city_guides` corpus

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

This is a retrieval-augmented question answering system built on the `city_guides` corpus — fourteen short travel guides to fictional towns, each covering practical visitor information like getting there, where to stay, what to see, and when to go. Ask it something a guide would actually cover — "Where's the free car park in Pellew Sands?", "When's the Givens Mill tearoom closed?" — and it retrieves the relevant section from the right guide, then has a language model answer strictly from that retrieved text rather than its own general knowledge. If a question falls outside what the guides cover, a relevance gate catches it before it ever reaches the model and the system says so instead of guessing.

## Chunking Strategy

**Chunk size:** one markdown `##` section per chunk (no fixed character target); sections that exceed 1000 characters are split further on paragraph breaks.
**Overlap:** none.

The starter's fixed 800-character window doesn't fit these documents. Each
guide is a handful of short, self-contained `##` sections — "Getting there",
"Eat and drink", "What to see", "When to go" — and none of them come close to
800 characters (the corpus's sections run roughly 150–450 characters). A
fixed window either grabs one section plus the start of the next (the
`app.py index` summary before this change showed 51 chunks from only 14
documents, i.e. every document getting cut mid-section) or, on the shorter
guides, leaves a section stranded as a tiny trailing fragment.

Since the documents already come pre-divided into single-topic sections by
their authors, I chunk on those boundaries instead of on a character count:
one `##` section = one chunk. Each chunk is prefixed with its document title
and section heading (e.g. `Brightwater — Getting there:`) so it reads as a
complete thought without needing the chunks before or after it — the heading
alone often answers "what is this about," and the retrieved text answers the
rest. There's no overlap because sections don't share content with their
neighbours; overlap would just duplicate parts of the previous or next topic.

The one guard rail: a section over 1000 characters (well above anything in
this corpus today, in case a future guide adds a long section) gets split
further along paragraph breaks rather than shipped as one oversized chunk.

Re-running `python app.py index` on `city_guides` with this strategy gives
94 chunks from 14 documents, averaging 319 characters, shortest 173 and
longest 759 — no 2-character fragments and nothing spanning multiple topics.

## Sample Chunks

<!-- Five chunks, pasted as text. Label each one and name the file it came from
     AND the function that produced it — the grader checks your code against
     what you claim here.

     `python app.py chunks -n 5` prints all three for you. Copy them straight
     across.

     Milestone 3. -->

**Chunk 1** — source: `guide_accessibility.md#0` — produced by: `chunker.py::split_documents`

```
Getting around the region with limited mobility:

An honest assessment rather than a promotional one. Some of these places are
difficult and it is better to know in advance.
```

**Chunk 2** — source: `guide_corry_vale.md#5` — produced by: `chunker.py::split_documents`

```
Corry Vale — Where to stay:

Perhaps thirty beds in the entire valley, spread across two pubs and a handful of farmhouse rooms. In summer these are booked months ahead. Camping is permitted on two marked fields and nowhere else.
```

**Chunk 3** — source: `guide_givens_mill.md#2` — produced by: `chunker.py::split_documents`

```
Givens Mill — Getting around:

Everything is on one street along the river. The mill is at one end and the church at the other, eight minutes apart. The riverside path continues in both directions for as far as you want to walk.
```

**Chunk 4** — source: `guide_kestrelford.md#4` — produced by: `chunker.py::split_documents`

```
Kestrelford — What to see:

The market square on a Saturday morning is the main event and has run continuously since the 1400s. The parish church has a 13th-century tower you can climb for £2. The old trackbed walk runs six miles to the next village along an easy gradient and is the best half-day here.
```

**Chunk 5** — source: `guide_pellew_sands.md#6` — produced by: `chunker.py::split_documents`

```
Pellew Sands — When to go:

June and September for the beach without the crowds. July and August are busy and the town is at its most itself, for better and worse. Winter is bleak, largely closed, and has a following among people who like that sort of thing.
```

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:**
Where can I park for free in Pellew Sands, and how far is it from the seafront?

**Answer:**
You can park for free in the lot behind the station, which is a four-minute walk from the seafront (from guide_pellew_sands.md).

Sources retrieved: guide_accessibility.md, guide_pellew_sands.md

**My relevance cutoff:**

I kept `TOP_K` at 5 and `THRESHOLD` at 0.6, the starter defaults. Running all five in-corpus questions and all five `OUT_OF_SCOPE` questions through `python app.py retrieve "..."` showed a wide, clean gap between the two groups: in-corpus best distances top out at 0.369, and the closest any out-of-scope question got was 0.802. There's over 0.4 of empty space between the two groups, so 0.6 sits safely in the middle of the gap rather than near either edge — I didn't need to move it. For each in-corpus question, the top chunk was also clearly on-topic (right village, right section) rather than a coincidental keyword match, so I left `TOP_K` alone too — 5 results already surfaces the right chunk first or second without burying it.

| Question                                                                                                                  | In corpus? | Best distance |
| ------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------- |
| Which street in Brightwater offers comparable food for about a third less than the riverside strip?                       | Yes        | 0.207         |
| Where is the free car park in Pellew Sands, and how far is the walk from it to the seafront?                              | Yes        | 0.278         |
| What are the opening hours of the Givens Mill tearoom, and which day is it closed?                                        | Yes        | 0.369         |
| Which months are best for birdwatching at Elder Ness, and how far ahead does accommodation book up for migration seasons? | Yes        | 0.215         |
| Which district is recommended for eating in Marchwood, and how late do kitchens serve on Fridays and Saturdays?           | Yes        | 0.212         |
| What is the capital of Mongolia?                                                                                          | No         | 0.802         |
| How do I change the oil in a diesel engine?                                                                               | No         | 0.885         |
| Who won the 1994 World Cup?                                                                                               | No         | 0.967         |
| What is the recommended dosage of ibuprofen for a headache?                                                               | No         | 0.841         |
| How do I write a for loop in Rust?                                                                                        | No         | 0.847         |

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1.**
I asked Claude to rewrite `split_documents` in `chunker.py` to chunk on markdown `##` section headings instead of the starter's fixed 800-character window. Its first version split correctly on headings but returned each chunk as just the raw section body, no heading or document title attached, so a chunk like the Pellew Sands parking paragraph would read as isolated text with no indication of which town or topic it belonged to. I asked it to prefix each chunk with `"{title} — {heading}:"` before the body, so a chunk reads as a complete thought on its own (e.g. `Pellew Sands — Getting there:`) without needing the chunks around it for context.

**2.**
I had Claude run `python app.py retrieve` on all five in-corpus test questions and all five `OUT_OF_SCOPE` questions to find where the relevance cutoff should sit, rather than picking a number by feel. It came back with the best distance for each of the ten questions and pointed out a wide gap in corpus questions topped out at 0.369, out of scope questions never got closer than 0.802. I expected to have to lower `THRESHOLD` from the starter's 0.6 default, but the gap showed 0.6 already sits safely in the middle, so I left it alone instead of changing something that wasn't actually broken.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion                              | Target | Run 1 | Run 2 | Run 3 | Verdict |
| -------------------------------------- | ------ | ----- | ----- | ----- | ------- |
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5   | 5/5   | 5/5   | MET     |
| 2. Every answer names a source         | 5 of 5 | 5/5   | 5/5   | 5/5   | MET     |
| 3. Gate stops out-of-corpus questions  | 4 of 5 | 5/5   | 5/5   | 5/5   | MET     |
| 4. Sampled chunks are self-contained   | 4 of 5 | 4/5   | 4/5   | 4/5   | MET     |
| 5. Cited source supports the answer    | 4 of 5 | 5/5   | 5/5   | 5/5   | MET     |

Source: `results/run_2026-10-05_0326_before.md`. Criteria 1, 2 and 5 were scored by hand
because `scorer.py` doesn't exist. Criteria 3 and 4 are deterministic (the gate is a
fixed cutoff, and the chunk sample is the same chunks every time), so one number fills all three columns.

### Real output

**Criterion 1 — retrieved chunks contain the answer.** Retrieval is `store.py::search`; the
log is written by `run_eval.py::main`. Question 3, run 1:

```
Best distance: 0.3692 (passed the gate)
Sources retrieved: guide_givens_mill.md
The Givens Mill tearoom is open from 10 to 4 daily, and it is closed on Tuesdays (guide_givens_mill.md).
```

**Criterion 2 — every answer names a source.** Answers come from `generate.py`. Question 4, run 2:

```
The best months for birdwatching at Elder Ness are April to May and September to October. Accommodation for the migration seasons books up a year ahead.

*(Source: guide_elder_ness.md)*
```

**Criterion 3 — gate stops out-of-corpus questions.** `run_eval.py::check_out_of_scope`, cutoff 0.6, refused 5 of 5:

```
| What is the capital of Mongolia? | 0.802 | refused |
| How do I change the oil in a diesel engine? | 0.885 | refused |
| Who won the 1994 World Cup? | 0.967 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.841 | refused |
| How do I write a for loop in Rust? | 0.847 | refused |
```

**Criterion 4 — chunks are self-contained.** Chunks come from `chunker.py::split_documents`
(94 chunks). I sampled 5 with `random.seed(201)`. Four stand on their own; one does not.
Self-contained (`guide_kestrelford.md#3`, 261 chars):

```
Kestrelford — Eat and drink:

Four pubs, two cafés, and a bakery that sells out by 11am. The pubs serve food between 12 and 2 and again between 6 and 8:30, and outside those windows there is nowhere to eat at all. The bakery is the reason most people come back.
```

Not self-contained (`guide_accessibility.md#0`, 173 chars) — a heading and one intro sentence, no content:

```
Getting around the region with limited mobility:

An honest assessment rather than a promotional one. Some of these places are
difficult and it is better to know in advance.
```

**Criterion 5 — cited source supports the answer.** Question 5, run 1, cites `guide_marchwood.md`. The
supporting line in that file (line 15) reads: "The best eating is in the Northgate district… kitchens
serve until 10:30pm, and until midnight on Fridays and Saturdays."

```
The best eating is in the Northgate district, and kitchens serve until midnight on Fridays and Saturdays (guide_marchwood.md).
```

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| #   | Criterion | Verdict | How I decided |
| --- | --------- | ------- | ------------- |
| 1   | Retrieved chunks contain the answer | MET | All five answers matched their `expects` value (Corry Lane, station, Tuesday, year, Northgate), and each cited file contains the passage. 5/5 on all three runs. Retrieval is deterministic, so the runs agree. Caveat: `expects` is a single word and Q2 (`station`), Q3 (`Tuesday`) and Q4 (`year`) each ask a two-part question, so I read the whole answer rather than trusting the keyword. Both halves were present every time (four-minute walk, 10 to 4, April–May and September–October). |
| 2   | Every answer names a source | MET | All 15 answers (5 questions × 3 runs) name a `guide_*.md` file, though the format varies (bold, backticks, parentheses, "Source:"). |
| 3   | Gate stops out-of-corpus questions | MET | Refused 5 of 5. Best distances ran 0.802–0.967, all above the 0.6 cutoff. In-corpus questions ran 0.207–0.369, so there is a clean gap. |
| 4   | At least 4 of 5 sampled chunks are self-contained | MET (close) | 4 of 5 in my sample. My rule: a chunk is self-contained if it holds at least one concrete fact someone could answer a question from, without the neighbouring chunks. `guide_accessibility.md#0` fails — a heading plus an intro sentence, no fact. It is exactly at target, so I checked all 94 chunks, not just the sample: it is the only chunk with no usable fact. Eleven others are short (under 200 characters) but each still holds a fact, so the full corpus looks closer to 93 of 94 than 4 of 5 and the sample was unlucky, not generous. |
| 5   | Cited source supports the answer | MET | I checked each cited file for the claim. All five are supported. |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

**I missed nothing.** All five criteria were MET on all three runs, so there is nothing to diagnose.

**My targets were too easy, criterion 4 most of all.** The target was 4 of 5 sampled chunks and my sample hit exactly 4, but checking all 94 chunks showed only one fails (`guide_accessibility.md#0`, a heading and an intro sentence with no fact, produced by `chunker.py::split_documents`). The real pass rate is about 99%, so an 80% target proved nothing. **I would tighten criterion 4 to at least 93 of all 94 chunks, checked across the whole corpus instead of a sample of five.**

## The Improvement

**What I changed:** In `chunker.py::split_documents`, an intro (text before the first `##`) shorter than `MIN_INTRO_SIZE = 150` characters is now merged into the first `##` section instead of being its own chunk. Only `guide_accessibility.md` was affected: its 123-character intro folded into its "Straightforward" section, taking the corpus from 94 to 93 chunks. The other nine town intros are 187+ characters and state real facts, so they are unchanged. Nothing else was touched (threshold 0.6, top-k 5, prompt, and the per-town prefix are all as before).

**Why I picked it:** My Diagnoses section found exactly one defective chunk, `guide_accessibility.md#0` (a heading and an intro sentence with no fact), so I'm merging fact-free intros into the next section to fix that chunk and move criterion 4.

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion                              | Target | Run 1 | Run 2 | Run 3 | Verdict |
| -------------------------------------- | ------ | ----- | ----- | ----- | ------- |
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5   | 5/5   | 5/5   | MET     |
| 2. Every answer names a source         | 5 of 5 | 5/5   | 5/5   | 5/5   | MET     |
| 3. Gate stops out-of-corpus questions  | 4 of 5 | 5/5   | 5/5   | 5/5   | MET     |
| 4. Sampled chunks are self-contained   | 4 of 5 | 5/5   | 5/5   | 5/5   | MET     |
| 5. Cited source supports the answer    | 4 of 5 | 5/5   | 5/5   | 5/5   | MET     |

Source: `results/run_2026-10-05_0432_after.md`. Scored by hand as before. Criteria 3 and 4 are deterministic, so one number fills all three columns. Criterion 4 uses the same `random.seed(201)` sample; it now includes the merged chunk `guide_accessibility.md#0`, which holds facts and passes. The first attempt crashed on a Gemini `503`; this is from the retry.

Only criterion 4 changed (4/5 → 5/5). Criteria 1, 2, 3 and 5 were 5/5 before and after, and the best retrieval distances for all five test questions are identical to four decimals (0.2073, 0.2778, 0.3692, 0.2147, 0.2123).

**Did it help?**

Yes, but narrowly. Criterion 4 went from 4/5 to 5/5, and across all chunks the one fact-free chunk is gone (93/94 → 93/93 pass). Retrieval distances didn't move, so the merge didn't disturb retrieval; the other four criteria were already at ceiling. Caveats: the sample-based result is partly luck of the seed (the full-corpus count is the real measure), and none of my test questions touches the accessibility guide, so the merged chunk's own retrieval is untested. I did not fix the Marchwood-vs-Brightwater hospital contradiction; that is a corpus issue, not a pipeline fault.

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

**No criterion is still missed.** All five were MET before and after the fix. Four things are still open:

1. **Marchwood vs. Brightwater hospital contradiction.** The two guides disagree about the nearest hospital. It's a corpus problem, not a pipeline fault. I'd correct the wrong guide, or have the prompt flag conflicting chunks. I stopped because none of my criteria measures it.
2. **Criteria 1, 2 and 5 were scored by hand.** `scorer.py` doesn't exist, so the scores are my reading and can't be re-run. I'd script criteria 1 and 2 (keyword and `guide_*.md` filename checks) and keep hand-checking 5. I stopped because it wasn't part of the milestones.
3. **The merged accessibility chunk's retrieval is untested.** None of my test questions touches `guide_accessibility.md`. I'd add a limited-mobility question and check the chunk comes back in the top 5. I stopped because changing the test set between the before and after runs would muddy the comparison.
4. **The 150-character threshold is tuned to this corpus.** It sits between the fact-free intro (123) and the shortest real one (187). A future short intro that does hold a fact would be merged needlessly. A general fix needs more machinery than one bad chunk justifies.

## What I'd Do Differently

**Criterion 4 is the one I'd rewrite.** My sample hit exactly 4 of 5, but checking all 94 chunks showed only one failure (about 99%), so an 80% target on a sample of five told me almost nothing. Next time I'd check every chunk, set the target at 93 of 94 or tighter, and write down my definition of self-contained before scoring.

**Criterion 1 is the second.** A single-word `expects` is too thin for two-part questions. I'd use one keyword per part so a half-answer fails.

**Criteria 2 and 5:** I'd keep them, but name an exact citation format for 2 so a script can check it, and add a question for 5 whose answer needs two chunks. I'd keep criterion 3 as is: the gap between in-corpus (0.207–0.369) and out-of-scope (0.802–0.967) distances made 5 of 5 a fair target.

## How I Used AI — Unit 2

**3.**
I asked Claude how to fix criterion 4 after my full-corpus check found one defective chunk. It offered a narrow change to `chunker.py::split_documents` or hybrid search, and recommended the chunker fix because the diagnosis pointed at chunking and retrieval distances were already fine. I agreed. I also had it check every guide's intro length before choosing `MIN_INTRO_SIZE = 150`: the accessibility intro is 123 characters and the shortest intro with real facts is 187. That took the corpus from 94 chunks to 93 with nothing else changed.

**4.**
I used Claude to scan all 94 chunks for ones with no usable fact instead of trusting my sample of five. It found only `guide_accessibility.md#0`, and showed that eleven other chunks under 200 characters still hold a fact. That is what exposed my criterion 4 target as too easy. I read the flagged chunks myself and kept my own definition of self-contained.
