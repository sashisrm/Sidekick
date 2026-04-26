"""
Structure-aware chunker.

Strategy:
1. Receive PageSections from extractor (already structurally split)
2. Sub-chunk any section exceeding CHUNK_SIZE tokens at sentence boundaries
3. Apply OVERLAP between consecutive chunks
4. Merge sections that are too short (< MIN_TOKENS) with their neighbor
"""

import re
from dataclasses import dataclass, field

from pipelines.ingestion.extractor import PageSection

WORDS_PER_TOKEN = 0.75  # approximate


@dataclass
class Chunk:
    text: str
    section: str
    page_number: int | None
    has_table: bool
    word_count: int = 0

    def __post_init__(self):
        self.word_count = len(self.text.split())


def chunk_sections(
    sections: list[PageSection],
    chunk_size_tokens: int = 512,
    overlap_tokens: int = 50,
    min_tokens: int = 50,
) -> list[Chunk]:
    chunk_size_words = int(chunk_size_tokens * WORDS_PER_TOKEN)
    overlap_words = int(overlap_tokens * WORDS_PER_TOKEN)

    raw_chunks: list[Chunk] = []

    for section in sections:
        text = section.text.strip()
        if not text:
            continue

        words = text.split()
        if len(words) <= chunk_size_words:
            raw_chunks.append(Chunk(
                text=text,
                section=section.section,
                page_number=section.page_number,
                has_table=section.has_table,
            ))
        else:
            # Sub-chunk at sentence boundaries
            sub_chunks = _split_at_sentences(
                text,
                section=section.section,
                page_number=section.page_number,
                has_table=section.has_table,
                chunk_size_words=chunk_size_words,
                overlap_words=overlap_words,
            )
            raw_chunks.extend(sub_chunks)

    # Merge short chunks
    merged = _merge_short_chunks(raw_chunks, min_words=int(min_tokens * WORDS_PER_TOKEN))
    return merged


def _split_at_sentences(
    text: str,
    section: str,
    page_number: int | None,
    has_table: bool,
    chunk_size_words: int,
    overlap_words: int,
) -> list[Chunk]:
    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[Chunk] = []
    current_words: list[str] = []
    overlap_buffer: list[str] = []

    for sentence in sentences:
        sent_words = sentence.split()
        # If single sentence exceeds chunk size, split it hard
        if len(sent_words) > chunk_size_words:
            # Flush current
            if current_words:
                chunks.append(Chunk(
                    text=" ".join(current_words),
                    section=section,
                    page_number=page_number,
                    has_table=has_table,
                ))
                overlap_buffer = current_words[-overlap_words:] if overlap_words else []
                current_words = list(overlap_buffer)

            # Hard-split the long sentence
            for i in range(0, len(sent_words), chunk_size_words - overlap_words):
                part = sent_words[i: i + chunk_size_words]
                if part:
                    chunks.append(Chunk(
                        text=" ".join(part),
                        section=section,
                        page_number=page_number,
                        has_table=has_table,
                    ))
            overlap_buffer = sent_words[-overlap_words:] if overlap_words else []
            current_words = list(overlap_buffer)
            continue

        if len(current_words) + len(sent_words) > chunk_size_words:
            # Flush
            if current_words:
                chunks.append(Chunk(
                    text=" ".join(current_words),
                    section=section,
                    page_number=page_number,
                    has_table=has_table,
                ))
                overlap_buffer = current_words[-overlap_words:] if overlap_words else []
                current_words = list(overlap_buffer)

        current_words.extend(sent_words)

    if current_words:
        chunks.append(Chunk(
            text=" ".join(current_words),
            section=section,
            page_number=page_number,
            has_table=has_table,
        ))

    return chunks


def _merge_short_chunks(chunks: list[Chunk], min_words: int) -> list[Chunk]:
    if not chunks:
        return []

    merged: list[Chunk] = []
    i = 0

    while i < len(chunks):
        chunk = chunks[i]
        if chunk.word_count < min_words and i + 1 < len(chunks):
            next_chunk = chunks[i + 1]
            combined_text = chunk.text + " " + next_chunk.text
            merged.append(Chunk(
                text=combined_text,
                section=chunk.section or next_chunk.section,
                page_number=chunk.page_number or next_chunk.page_number,
                has_table=chunk.has_table or next_chunk.has_table,
            ))
            i += 2
        else:
            merged.append(chunk)
            i += 1

    return merged
