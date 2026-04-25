from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    Split text into overlapping chunks. `overlap` must be less than `chunk_size`.
    """
    t = (text or "").strip()
    if not t:
        return []
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    step = chunk_size - overlap
    chunks: list[str] = []
    start = 0
    while start < len(t):
        piece = t[start : start + chunk_size].strip()
        if piece:
            chunks.append(piece)
        start += step
    return chunks
