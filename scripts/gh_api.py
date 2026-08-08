#!/usr/bin/env python3
"""Minimal GitHub REST client for sandboxed sessions where the gh CLI cannot
verify TLS (Go binaries need the macOS trust store; the sandbox blocks it —
OSStatus -26276). python's ssl uses the file-based CA bundle, which works.

Token source: gh's plain config file (~/.config/gh/hosts.yml), the same
sandbox-readable store the git credential helper uses. Never prints the token.

Usage:
  python3 scripts/gh_api.py GET  /repos/OWNER/REPO/pulls?head=OWNER:BRANCH
  python3 scripts/gh_api.py POST /repos/OWNER/REPO/pulls  < body.json

Output: HTTP status on stderr, response JSON on stdout.
"""

import gzip
import http.client
import json
import pathlib
import sys
import urllib.error
import urllib.request


def token() -> str:
    hosts = pathlib.Path.home() / ".config" / "gh" / "hosts.yml"
    for line in hosts.read_text().splitlines():
        line = line.strip()
        if line.startswith("oauth_token:"):
            return line.split(":", 1)[1].strip()
    sys.exit("no oauth_token in ~/.config/gh/hosts.yml — run scripts/claude-git-access.sh")


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    method, path = sys.argv[1].upper(), sys.argv[2]
    body = sys.stdin.read().encode() if method in ("POST", "PATCH", "PUT") else None
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "poker-coach-sandbox-client",
            # The sandbox proxy truncates larger plain bodies (~22KB observed);
            # gzip keeps most GitHub responses well under that on the wire.
            "Accept-Encoding": "gzip",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"HTTP {resp.status}", file=sys.stderr)
            sys.stdout.write(_decode(_read_all(resp), resp).decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}", file=sys.stderr)
        sys.stdout.write(_decode(_read_all(e), e).decode())
        sys.exit(1)


def _decode(body: bytes, resp) -> bytes:
    if resp.headers.get("Content-Encoding", "") == "gzip":
        return gzip.decompress(body)
    return body


def _read_all(resp) -> bytes:
    # The sandbox's network proxy can mis-report Content-Length on larger
    # bodies, making a plain read() raise IncompleteRead even though the full
    # payload arrives. Stream in chunks and keep whatever was delivered.
    chunks = []
    while True:
        try:
            chunk = resp.read(8192)
        except http.client.IncompleteRead as e:
            chunks.append(e.partial)
            break
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


if __name__ == "__main__":
    main()
