# gitRAG — GitHub Repository RAG System

Ask natural language questions about any GitHub repository using local embeddings + Groq LLM.

## Architecture

```
GitHub URL → Fetch Files → Chunk → Embed (local) → ChromaDB
                                                        ↓
User Query → Embed Query → Similarity Search → Groq LLM → Answer + Sources
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> First run downloads the `all-MiniLM-L6-v2` model (~90MB) automatically.

### 2. Get a free Groq API key

Go to https://console.groq.com → sign up → create an API key.

### 3. Run

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Usage

1. Paste a GitHub repo URL in the sidebar (e.g. `https://github.com/streamlit/streamlit`)
2. Optionally add a GitHub token (Settings → Developer Settings → Personal Access Tokens)
3. Enter your Groq API key
4. Click **Load & Index Repository**
5. Ask anything about the codebase in the chat

## Supported File Types

`.md` `.txt` `.py` `.js` `.ts` `.jsx` `.tsx` `.json` `.html` `.css`
`.yaml` `.yml` `.sh` `.go` `.rs` `.java` `.cpp` `.c` `.h` `.rb` `.php`

## Configuration

| Setting | Default | Description |
|---|---|---|
| Chunk size | 600 words | Words per chunk |
| Chunk overlap | 80 words | Overlap between chunks |
| Max files | 100 | Files fetched per repo |
| Max file size | 200 KB | Skip larger files |
| Top-K retrieval | 6 | Chunks passed to LLM |
| LLM model | llama3-70b-8192 | Groq model used |

## Files

```
app.py            → Streamlit UI + session state
github_fetcher.py → GitHub API file fetching
chunker.py        → Text chunking with overlap
embedder.py       → Local sentence-transformers embeddings
vector_store.py   → ChromaDB persistence layer
rag_chain.py      → Groq LLM prompt + answer generation
requirements.txt  → Python dependencies
```

## Environment Variables (optional)

Instead of entering keys in the UI, you can set:

```bash
export GROQ_API_KEY=your_key_here
export GITHUB_TOKEN=your_token_here
```
