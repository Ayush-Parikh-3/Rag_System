"""
github_fetcher.py
Recursively fetches supported text files from a GitHub repository.
"""

import requests
from typing import Optional

SUPPORTED_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".json", ".html", ".css", ".yaml", ".yml", ".sh",
    ".go", ".rs", ".java", ".cpp", ".c", ".h", ".rb", ".php",
}

MAX_FILE_SIZE = 200_000   # 200 KB


def fetch_repo_files(
    owner: str,
    repo: str,
    branch: str = "main",
    token: Optional[str] = None,
) -> list[dict]:
    """
    Returns a list of dicts:
        {text, path, url, branch, owner, repo}
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    # Try specified branch; fall back to 'master'
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    resp = requests.get(tree_url, headers=headers, timeout=20)
    if resp.status_code == 404 and branch == "main":
        branch = "master"
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        resp = requests.get(tree_url, headers=headers, timeout=20)
    resp.raise_for_status()

    tree = resp.json().get("tree", [])
    blobs = [
        f for f in tree
        if f["type"] == "blob"
        and f.get("size", 0) < MAX_FILE_SIZE
        and any(f["path"].endswith(ext) for ext in SUPPORTED_EXTENSIONS)
    ]

    docs = []
    for blob in blobs[:100]:           # cap at 100 files per repo
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{blob['path']}"
        try:
            r = requests.get(raw_url, headers=headers, timeout=15)
            if r.status_code == 200 and r.text.strip():
                docs.append({
                    "text": r.text,
                    "path": blob["path"],
                    "url": f"https://github.com/{owner}/{repo}/blob/{branch}/{blob['path']}",
                    "branch": branch,
                    "owner": owner,
                    "repo": repo,
                })
        except Exception:
            pass

    return docs
