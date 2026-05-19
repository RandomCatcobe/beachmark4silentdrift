"""
GitHub changelog / release-note fetcher.

Strategy (in order of preference, fall back on failure):
    1. GitHub Releases API (clean, paginated, has tag + body)
    2. CHANGELOG.md from default branch (good for old releases)
    3. wiki pages named like "*Release-Notes*" (Spring Boot uses these)

We never page beyond `max_releases` to keep token / network cost predictable.
All responses are cached on disk under data/raw_changelogs/<owner>__<repo>/.

Auth: optionally reads GITHUB_TOKEN from env to lift rate limit from 60/hr
to 5000/hr. Without a token, this works for small mining runs but will
throttle on a larger pass.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

API_ROOT = "https://api.github.com"
USER_AGENT = "silent-drift-miner/0.1 (research)"


@dataclass
class ReleaseDoc:
    """One release / changelog entry, normalized across source types."""
    library: str        # e.g. "spring-boot"
    owner: str          # e.g. "spring-projects"
    repo: str           # e.g. "spring-boot"
    tag: str            # e.g. "v3.0.0"
    name: str           # human-readable name; often same as tag
    body: str           # raw markdown body (release notes)
    html_url: str       # canonical user-facing URL
    published_at: Optional[str]  # ISO timestamp
    source_type: str    # "release_api" | "changelog_file" | "wiki"


class GitHubFetcher:
    def __init__(
        self,
        cache_dir: Path,
        token: Optional[str] = None,
        request_pause: float = 0.4,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.request_pause = request_pause
        self._last_request_ts = 0.0

    # ---------- public API ----------

    def fetch_releases(
        self,
        owner: str,
        repo: str,
        max_releases: int = 50,
        use_cache: bool = True,
    ) -> list[ReleaseDoc]:
        """Pull up to `max_releases` releases from the Releases API."""
        cache_path = self._cache_path(owner, repo, "releases.json")
        if use_cache and cache_path.exists():
            data = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            data = self._fetch_releases_api(owner, repo, max_releases)
            cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        out: list[ReleaseDoc] = []
        for item in data[:max_releases]:
            out.append(
                ReleaseDoc(
                    library=repo,
                    owner=owner,
                    repo=repo,
                    tag=item.get("tag_name") or "",
                    name=item.get("name") or item.get("tag_name") or "",
                    body=item.get("body") or "",
                    html_url=item.get("html_url") or "",
                    published_at=item.get("published_at"),
                    source_type="release_api",
                )
            )
        return out

    def fetch_changelog_file(
        self,
        owner: str,
        repo: str,
        candidate_paths: Optional[list[str]] = None,
        use_cache: bool = True,
    ) -> Optional[ReleaseDoc]:
        """Try a few common CHANGELOG paths on the default branch.

        Returns one ReleaseDoc whose body is the entire changelog file.
        Downstream extractors are responsible for splitting it into sections.
        """
        if candidate_paths is None:
            candidate_paths = [
                "CHANGELOG.md",
                "CHANGELOG",
                "CHANGES.md",
                "CHANGES.rst",
                "HISTORY.md",
                "docs/CHANGELOG.md",
            ]
        for path in candidate_paths:
            cache_path = self._cache_path(owner, repo, f"file__{path.replace('/', '__')}")
            if use_cache and cache_path.exists():
                body = cache_path.read_text(encoding="utf-8")
                if body == "__NOT_FOUND__":
                    continue
                return ReleaseDoc(
                    library=repo, owner=owner, repo=repo,
                    tag="(file)", name=path, body=body,
                    html_url=f"https://github.com/{owner}/{repo}/blob/HEAD/{path}",
                    published_at=None, source_type="changelog_file",
                )
            body = self._fetch_raw_file(owner, repo, path)
            if body is None:
                cache_path.write_text("__NOT_FOUND__", encoding="utf-8")
                continue
            cache_path.write_text(body, encoding="utf-8")
            return ReleaseDoc(
                library=repo, owner=owner, repo=repo,
                tag="(file)", name=path, body=body,
                html_url=f"https://github.com/{owner}/{repo}/blob/HEAD/{path}",
                published_at=None, source_type="changelog_file",
            )
        return None

    # ---------- internals ----------

    def _cache_path(self, owner: str, repo: str, name: str) -> Path:
        d = self.cache_dir / f"{owner}__{repo}"
        d.mkdir(parents=True, exist_ok=True)
        return d / name

    def _fetch_releases_api(self, owner: str, repo: str, max_releases: int) -> list[dict]:
        per_page = 30
        pages_needed = (max_releases + per_page - 1) // per_page
        merged: list[dict] = []
        for page in range(1, pages_needed + 1):
            url = (
                f"{API_ROOT}/repos/{owner}/{repo}/releases"
                f"?per_page={per_page}&page={page}"
            )
            data = self._http_get_json(url)
            if not data:
                break
            merged.extend(data)
            if len(data) < per_page:
                break
        return merged

    def _fetch_raw_file(self, owner: str, repo: str, path: str) -> Optional[str]:
        # raw.githubusercontent.com is unauthenticated, no rate limit issues
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{urllib.parse.quote(path)}"
        try:
            return self._http_get_text(url, accept="text/plain")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def _http_get_json(self, url: str) -> list[dict] | dict:
        text = self._http_get_text(url, accept="application/vnd.github+json")
        return json.loads(text)

    def _http_get_text(self, url: str, accept: str) -> str:
        # naive request pacing
        elapsed = time.time() - self._last_request_ts
        if elapsed < self.request_pause:
            time.sleep(self.request_pause - elapsed)
        self._last_request_ts = time.time()

        req = urllib.request.Request(url)
        req.add_header("Accept", accept)
        req.add_header("User-Agent", USER_AGENT)
        if self.token and "api.github.com" in url:
            req.add_header("Authorization", f"Bearer {self.token}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")


# ---------- section splitter for monolithic CHANGELOG files ----------

def split_changelog_into_sections(body: str) -> Iterator[tuple[str, str]]:
    """Yield (version_label, section_body) pairs.

    Heuristic: a level-1 or level-2 markdown header that contains a version-like
    token (e.g. "## 3.0.0", "## [3.0.0]", "## v3.0.0 - 2023-01-15") starts a
    new section. Anything before the first such header is skipped.
    """
    import re
    header_re = re.compile(
        r"^(#{1,2})\s+(.*?(?:v?\d+\.\d+(?:\.\d+)?[\w\.\-]*).*)$",
        re.MULTILINE,
    )
    matches = list(header_re.finditer(body))
    for i, m in enumerate(matches):
        version_label = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        section = body[start:end].strip()
        if section:
            yield version_label, section
