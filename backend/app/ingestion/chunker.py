from app.config import CHUNK_SIZE_CHARS, CHUNK_OVERLAP_CHARS


def chunk_text(text: str, size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    """Simple sliding-window chunker on paragraphs first, falling back to raw
    character windows for text with no paragraph breaks (e.g. dense tables)."""
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 1 <= size:
            current = f"{current}\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            if len(para) > size:
                # paragraph itself too long (e.g. a giant table dump) — window it
                for i in range(0, len(para), size - overlap):
                    chunks.append(para[i:i + size])
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    # add overlap between consecutive chunks so context isn't lost at boundaries
    overlapped = []
    for i, c in enumerate(chunks):
        if i == 0:
            overlapped.append(c)
        else:
            tail = chunks[i - 1][-overlap:] if overlap else ""
            overlapped.append((tail + "\n" + c).strip())

    return overlapped
