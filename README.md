# The Unofficial Guide

<!-- Replace this line with your name and which corpus you picked. -->

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

```

```

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
| 1. Retrieved chunk contains the answer | 4 of 5 |       |       |       |         |
| 2. Every answer names a source         | 5 of 5 |       |       |       |         |
| 3. Gate stops out-of-corpus questions  | 4 of 5 |       |       |       |         |
| 4.                                     |        |       |       |       |         |
| 5.                                     |        |       |       |       |         |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| #   | Criterion | Verdict | How I decided |
| --- | --------- | ------- | ------------- |
| 1   |           |         |               |
| 2   |           |         |               |
| 3   |           |         |               |
| 4   |           |         |               |
| 5   |           |         |               |

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

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion                              | Target | Run 1 | Run 2 | Run 3 | Verdict |
| -------------------------------------- | ------ | ----- | ----- | ----- | ------- |
| 1. Retrieved chunk contains the answer | 4 of 5 |       |       |       |         |
| 2. Every answer names a source         | 5 of 5 |       |       |       |         |
| 3. Gate stops out-of-corpus questions  | 4 of 5 |       |       |       |         |
| 4.                                     |        |       |       |       |         |
| 5.                                     |        |       |       |       |         |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
