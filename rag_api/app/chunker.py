from typing import List


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    if chunk_size <= 0:
        return [text]

    words = text.split()
    chunks: List[str] = []

    current_words: List[str] = []
    current_len = 0
    for word in words:
        # +1 for the space that will be inserted when joining
        additional = len(word) + (1 if current_words else 0)
        if current_len + additional > chunk_size and current_words:
            chunks.append(" ".join(current_words))
            # start next chunk with overlap
            if overlap > 0:
                overlap_text = chunks[-1][-overlap:]
                current_words = [overlap_text]
                current_len = len(overlap_text)
            else:
                current_words = []
                current_len = 0
        current_words.append(word)
        current_len += additional

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks
