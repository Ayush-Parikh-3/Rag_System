"""
chunker.py
Splits documents into overlapping token-aware chunks.
"""

CHUNK_SIZE   = 600   # words per chunk
CHUNK_OVERLAP = 80   # overlapping words


def chunk_documents(docs: list[dict]) -> list[dict]:
    """
    Input:  list of {text, path, url, branch, owner, repo}
    Output: list of {text, metadata: {path, url, branch, owner, repo, chunk_index}}
    """
    chunks = []
    for doc in docs:
        words = doc["text"].split()
        step  = CHUNK_SIZE - CHUNK_OVERLAP
        for i in range(0, max(1, len(words)), step):
            slice_words = words[i : i + CHUNK_SIZE]
            text = " ".join(slice_words).strip()
            if len(text) < 40:          # skip near-empty chunks
                continue
            chunks.append({
                "text": text,
                "metadata": {
                    "path":        doc["path"],
                    "url":         doc["url"],
                    "branch":      doc["branch"],
                    "owner":       doc["owner"],
                    "repo":        doc["repo"],
                    "chunk_index": len(chunks),
                },
            })
    return chunks
