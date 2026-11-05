import streamlit as st
import os
import re
from dotenv import load_dotenv

from github_fetcher import fetch_repo_files
from chunker import chunk_documents
from embedder import embed_texts, embed_query
from vector_store import VectorStore
from rag_chain import generate_answer

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

st.set_page_config(page_title="gitRAG", page_icon="🔍", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, .stApp {
    background: #ffffff !important;
    color: #111111 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #fafafa !important;
    border-right: 1px solid #eee !important;
}
[data-testid="stSidebar"] * {
    color: #111 !important;
}

/* Inputs */
.stTextInput input {
    background: #ffffff !important;
    border: 1px solid #e5e5e5 !important;
    color: #111 !important;
    border-radius: 6px !important;
    padding: 12px !important;
}
.stTextInput input:focus {
    border-color: #ccc !important;
}

/* Buttons */
.stButton button {
    background: #FFFFFF !important;
    color: #111 !important;
    border-radius: 6px !important;
    padding: 12px !important;
    font-weight: 500 !important;
}
.stButton button:hover {
    border-color: #000000 !important;
    color: #FFFFFF !important;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 14px 0 !important;
}

/* Assistant message */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    color: #444 !important;
}

/* User message */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    text-align: right;
}

/* Chat input */
[data-testid="stChatInput"] textarea {
    background: #fff !important;
    border: 1px solid #e5e5e5 !important;
    color: #111 !important;
    border-radius: 8px !important;
    padding: 14px !important;
}

/* Headings */
h1, h2, h3 {
    color: #111 !important;
    font-weight: 500 !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: transparent !important;
    border: none !important;
}

/* Source chips */
.source-chip {
    background: #f5f5f5;
    border: 1px solid #e5e5e5;
    color: #555 !important;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}
.source-chip:hover {
    color: #000 !important;
    background: #eee;
}

/* Brand */
.brand-name {
    font-size: 18px;
    font-weight: 600;
    color: #111;
}
.brand-sub {
    font-size: 11px;
    color: #888;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #ddd; }


</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
for k, v in [("vector_stores",{}),("repo_meta",{}),("current_repo",None),("messages",{})]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="brand">
        <div class="brand-name">git RAG</div>
        <div class="brand-sub">Repository knowledge search</div>
    </div>
    """, unsafe_allow_html=True)

    groq_dot   = "dot-on"   if GROQ_API_KEY else "dot-off"
    github_dot = "dot-on"   if GITHUB_TOKEN else "dot-warn"
    groq_label   = "Groq connected"        if GROQ_API_KEY else "Groq key missing"
    github_label = "GitHub token connected" if GITHUB_TOKEN else "GitHub token not set"

    st.markdown(f"""
    <div class="status-row"><span class="{groq_dot}"></span>{groq_label}</div>
    <div class="status-row"><span class="{github_dot}"></span>{github_label}</div>
    """, unsafe_allow_html=True)

    if not GROQ_API_KEY:
        st.error("Add GROQ_API_KEY to your .env file and restart.")
        st.stop()

    st.divider()
    st.subheader("Repository")
    repo_url = st.text_input("GitHub URL", placeholder="https://github.com/owner/repo", label_visibility="collapsed")
    branch   = st.text_input("Branch", value="main", label_visibility="collapsed")
    load_btn = st.button("Load & index repository", use_container_width=True)

    if st.session_state.repo_meta:
        st.divider()
        st.subheader("Loaded")
        for key, meta in st.session_state.repo_meta.items():
            active = "→ " if st.session_state.current_repo == key else ""
            if st.button(f"{active}{meta['owner']}/{meta['repo']}", key=f"sel_{key}", use_container_width=True):
                st.session_state.current_repo = key
                st.rerun()

# ── Load repo ──────────────────────────────────────────────────────────────────
if load_btn and repo_url:
    match = re.match(r"https?://github\.com/([^/]+)/([^/\s]+)", repo_url)
    if not match:
        st.error("Invalid URL — use https://github.com/owner/repo")
    else:
        owner     = match.group(1)
        repo_name = match.group(2).rstrip("/")
        repo_key  = f"{owner}_{repo_name}"

        if repo_key in st.session_state.vector_stores:
            st.session_state.current_repo = repo_key
            st.rerun()
        else:
            with st.status(f"Indexing {owner}/{repo_name}…", expanded=True) as status:
                st.write("Fetching files from GitHub…")
                docs = fetch_repo_files(owner, repo_name, branch, GITHUB_TOKEN or None)
                st.write(f"{len(docs)} files fetched")

                st.write("Splitting into chunks…")
                chunks = chunk_documents(docs)
                st.write(f"{len(chunks)} chunks created")

                st.write("Generating embeddings locally…")
                embeddings = embed_texts([c["text"] for c in chunks])
                st.write(f"{len(embeddings)} vectors ready")

                st.write("Storing in ChromaDB…")f
                vs = VectorStore(collection_name=repo_key)
                vs.add(chunks, embeddings)

                st.session_state.vector_stores[repo_key] = vs
                st.session_state.repo_meta[repo_key] = {
                    "owner": owner, "repo": repo_name, "branch": branch,
                    "files": len(docs), "chunks": len(chunks), "url": repo_url,
                }
                st.session_state.messages[repo_key] = []
                st.session_state.current_repo = repo_key
                status.update(label="Indexed successfully.", state="complete")

# ── Main ───────────────────────────────────────────────────────────────────────
if st.session_state.current_repo is None:
    st.markdown("## Start by loading a repository")
    st.markdown("""
Paste a GitHub URL into the sidebar and click **Load & index repository**.

The system will fetch all source files, split them into chunks, generate local embeddings, and store everything in a vector database — no data leaves your machine except the LLM query.

**Supported:** `.py` `.js` `.ts` `.go` `.rs` `.java` `.cpp` `.md` `.json` `.yaml` `.html` `.css` `.sh`
    """)
else:
    key  = st.session_state.current_repo
    meta = st.session_state.repo_meta[key]
    vs   = st.session_state.vector_stores[key]

    # Header
    col1, col2, col3 = st.columns([5, 1, 1])
    with col1:
        st.markdown(f'<div class="repo-header">{meta["owner"]}/{meta["repo"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="repo-meta">branch: {meta["branch"]} &nbsp;·&nbsp; {meta["files"]} files &nbsp;·&nbsp; {meta["chunks"]} chunks</div>', unsafe_allow_html=True)
    with col2:
        st.metric("Files", meta["files"])
    with col3:
        st.metric("Chunks", meta["chunks"])

    st.divider()

    # Chat history
    for m in st.session_state.messages.get(key, []):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("sources"):
                src_html = '<div class="sources-label">Sources</div>'
                src_html += "".join(
                    f'<a href="{s["url"]}" target="_blank" class="source-chip">⌗ {s["path"].split("/")[-1]}</a>'
                    for s in m["sources"]
                )
                st.markdown(src_html, unsafe_allow_html=True)

    # Input
    query = st.chat_input("Ask anything about this codebase…")
    if query:
        st.session_state.messages[key].append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Searching…"):
                q_emb   = embed_query(query)
                results = vs.search(q_emb, top_k=6)
                answer  = generate_answer(
                    query=query, chunks=results,
                    owner=meta["owner"], repo=meta["repo"],
                    groq_api_key=GROQ_API_KEY,
                )

            st.markdown(answer)

            seen, src_html = set(), '<div class="sources-label">Sources</div>'
            for r in results:
                p = r["metadata"]["path"]
                if p not in seen:
                    seen.add(p)
                    src_html += f'<a href="{r["metadata"]["url"]}" target="_blank" class="source-chip">⌗ {p.split("/")[-1]}</a> '
            if seen:
                st.markdown(src_html, unsafe_allow_html=True)

            st.session_state.messages[key].append({
                "role": "assistant", "content": answer,
                "sources": [{"path": r["metadata"]["path"], "url": r["metadata"]["url"]} for r in results],
            })