"""
rag_chain.py
Constructs the RAG prompt and calls Groq API for answer generation.
Supports: llama3-70b-8192, mixtral-8x7b-32768, llama3-8b-8192
"""

import os
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"


def build_prompt(query: str, chunks: list[dict], owner: str, repo: str) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        path = chunk["metadata"]["path"]
        context_parts.append(f"[{i}] File: `{path}`\n{chunk['text'][:600]}")
    context = "\n\n---\n\n".join(context_parts)

    return f"""You are an expert code assistant analyzing the GitHub repository `{owner}/{repo}`.

Use ONLY the context below to answer the question. Be specific and concise.
If the context does not contain enough information, say so clearly.
Always mention relevant file names when referencing code.

=== CONTEXT ===
{context}

=== QUESTION ===
{query}

=== ANSWER ==="""


def generate_answer(
    query: str,
    chunks: list[dict],
    owner: str,
    repo: str,
    groq_api_key: str = "",
    model: str = DEFAULT_MODEL,
) -> str:
    api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return (
            "⚠️ No Groq API key provided. "
            "Get a free key at https://console.groq.com and enter it in the sidebar."
        )

    if not chunks:
        return "No relevant context found in the repository for this question."

    prompt = build_prompt(query, chunks, owner, repo)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.2,
    }

    try:
        resp = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 401:
            return "❌ Invalid Groq API key. Check your key at https://console.groq.com"
        if resp.status_code == 429:
            return "⏳ Groq rate limit hit. Wait a moment and try again."
        return f"❌ Groq API error: {e}"
    except Exception as e:
        return f"❌ Error calling Groq API: {e}"
