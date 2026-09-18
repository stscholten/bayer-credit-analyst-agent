#!/usr/bin/env python3
"""Upload all project files to GitHub via REST API."""

import urllib.request
import urllib.error
import json
import base64
import os
import sys

TOKEN = "Ghp_pccKk3Aw0U4LW6vxhDpk4OaoURCE3O0emnma"
REPO = "stscholten/bayer-credit-analyst-agent"
BRANCH = "main"
API_BASE = "https://api.github.com"

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json",
    "User-Agent": "SAP-Build-Agent"
}

# Files to upload (relative to /home/user/project), mapped to GitHub path
PROJECT_ROOT = "/home/user/project"

# Exclude internal skill files and system files
EXCLUDE_PREFIXES = [
    ".agent/",
    ".build",
    "github_upload.py"
]

def should_exclude(rel_path):
    for prefix in EXCLUDE_PREFIXES:
        if rel_path.startswith(prefix):
            return True
    return False

def api_request(method, path, data=None):
    url = f"{API_BASE}/{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return json.loads(body) if body else {}, e.code

def get_file_sha(github_path):
    result, status = api_request("GET", f"repos/{REPO}/contents/{github_path}?ref={BRANCH}")
    if status == 200:
        return result.get("sha")
    return None

def upload_file(local_path, github_path):
    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    
    sha = get_file_sha(github_path)
    
    data = {
        "message": f"Add {github_path}",
        "content": content,
        "branch": BRANCH
    }
    if sha:
        data["sha"] = sha
        data["message"] = f"Update {github_path}"
    
    result, status = api_request("PUT", f"repos/{REPO}/contents/{github_path}", data)
    return status in (200, 201)

def ensure_branch_exists():
    """Make sure main branch exists, create if needed."""
    result, status = api_request("GET", f"repos/{REPO}/git/ref/heads/{BRANCH}")
    if status == 200:
        return True
    # Try to create from default branch
    result, status = api_request("GET", f"repos/{REPO}")
    if status == 200:
        default = result.get("default_branch", "main")
        ref_result, ref_status = api_request("GET", f"repos/{REPO}/git/ref/heads/{default}")
        if ref_status == 200:
            sha = ref_result["object"]["sha"]
            create_data = {"ref": f"refs/heads/{BRANCH}", "sha": sha}
            api_request("POST", f"repos/{REPO}/git/refs", create_data)
    return True

def collect_files():
    files = []
    for root, dirs, filenames in os.walk(PROJECT_ROOT):
        # Skip hidden dirs except we handle them by path
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for filename in filenames:
            local_path = os.path.join(root, filename)
            rel_path = os.path.relpath(local_path, PROJECT_ROOT)
            if not should_exclude(rel_path):
                files.append((local_path, rel_path))
    return sorted(files)

def main():
    print("🔗 Verbinde mit GitHub...")
    ensure_branch_exists()
    
    files = collect_files()
    print(f"📁 {len(files)} Dateien gefunden")
    
    success = 0
    failed = 0
    
    for i, (local_path, github_path) in enumerate(files, 1):
        try:
            ok = upload_file(local_path, github_path)
            if ok:
                print(f"  ✅ [{i:3d}/{len(files)}] {github_path}")
                success += 1
            else:
                print(f"  ❌ [{i:3d}/{len(files)}] {github_path} — fehlgeschlagen")
                failed += 1
        except Exception as e:
            print(f"  ❌ [{i:3d}/{len(files)}] {github_path} — Fehler: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Erfolgreich: {success}/{len(files)}")
    if failed:
        print(f"❌ Fehlgeschlagen: {failed}")
    print(f"\n🌐 Repository: https://github.com/{REPO}")
    print(f"🌐 Joule UI:  https://stscholten.github.io/bayer-credit-analyst-agent/")

if __name__ == "__main__":
    main()
