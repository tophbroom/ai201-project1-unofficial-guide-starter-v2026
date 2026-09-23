"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


# Only "##" section headings are split points. A lone "#" is the document
# title, handled separately, not a section of its own.
_HEADING_RE = re.compile(r"^##\s+(.*)$", re.MULTILINE)

# A section beyond this length is more than one thought stitched together, so
# it gets split further instead of shipped as one chunk. Picked well above the
# ~450-char sections this corpus actually has, so it only fires on an outlier.
MAX_SECTION_SIZE = 1000


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """
    Split one document's text on markdown '##' headings.

    Returns a list of (heading, body) pairs. Anything before the first '##'
    heading (the document's title / intro line) is kept as its own section
    with an empty heading, so it isn't dropped.
    """
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        body = re.sub(r"^#\s+.*\n?", "", text).strip()
        return [("", body)] if body else []

    sections: list[tuple[str, str]] = []

    intro = text[: matches[0].start()].strip()
    # Drop the leading "# Title" line — the title is carried separately and
    # would otherwise appear twice in the intro chunk.
    intro = re.sub(r"^#\s+.*\n?", "", intro).strip()
    if intro:
        sections.append(("", intro))

    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        if body:
            sections.append((heading, body))

    return sections


def _split_long_section(body: str, max_size: int) -> list[str]:
    """
    Break an oversized section into paragraph-sized pieces, packing
    consecutive paragraphs together up to max_size rather than cutting mid-
    paragraph.
    """
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    pieces: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) > max_size and current:
            pieces.append(current)
            current = para
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split documents into chunks along their markdown '##' section headings.

    city_guides documents are already organised into short, self-contained
    sections ("Getting there", "Eat and drink", "When to go", ...), each one
    a single topic covered in a few sentences. Cutting at fixed character
    counts (the fallback) slices straight through those sections instead of
    respecting them, so this chunker treats each heading's section as one
    chunk instead.

    Each chunk is prefixed with the document title and its section heading
    ("Brightwater — Getting there:") so it reads as a complete thought on its
    own, without needing the surrounding chunks for context.

    A section that runs unusually long (past MAX_SECTION_SIZE) is broken
    further along paragraph breaks rather than kept as one oversized chunk.
    """
    chunks: list[Chunk] = []
    for doc in documents:
        title_match = re.match(r"^#\s+(.*)$", doc.text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else doc.source

        sections = _split_into_sections(doc.text)
        index = 0
        for heading, body in sections:
            pieces = (
                [body] if len(body) <= MAX_SECTION_SIZE
                else _split_long_section(body, MAX_SECTION_SIZE)
            )
            for piece in pieces:
                # The intro before the first "##" has no heading of its own;
                # label it with just the title instead of "Title — :".
                label = f"{title} — {heading}" if heading else title
                prefix = f"{label}:\n\n"
                chunks.append(
                    Chunk(
                        text=(prefix + piece).strip(),
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::split_documents",
                    )
                )
                index += 1

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
