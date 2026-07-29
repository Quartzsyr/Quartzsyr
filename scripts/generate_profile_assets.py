#!/usr/bin/env python3
"""Generate local GitHub profile SVG cards.

The script uses GitHub's REST API and writes theme-aware SVG files into assets/.
It intentionally avoids third-party image endpoints so README images remain stable.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OWNER = os.environ.get("PROFILE_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "Quartzsyr"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
EXCLUDED_REPOS = {
    item.strip()
    for item in os.environ.get("EXCLUDED_REPOS", "Quartzsyr").split(",")
    if item.strip()
}

API = "https://api.github.com"


def request_json(url: str) -> tuple[Any, dict[str, str]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Quartz-profile-assets",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
        return data, dict(response.headers.items())


def paginate(url: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    page = 1
    while True:
        separator = "&" if "?" in url else "?"
        data, _ = request_json(f"{url}{separator}per_page=100&page={page}")
        if not isinstance(data, list):
            raise RuntimeError(f"Expected list from {url}")
        output.extend(data)
        if len(data) < 100:
            break
        page += 1
    return output


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def fmt_number(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def theme_values(theme: str) -> dict[str, str]:
    dark = theme == "dark"
    return {
        "bg": "#08111f" if dark else "#f8fbff",
        "border": "#2b4568" if dark else "#c9d7ec",
        "text": "#f4f7fb" if dark else "#12213b",
        "sub": "#9fb3d0" if dark else "#60728f",
        "track": "#1d304a" if dark else "#dce6f4",
    }


def stats_svg(theme: str, profile: dict[str, Any], repos: list[dict[str, Any]]) -> str:
    c = theme_values(theme)
    owned = [r for r in repos if not r.get("fork")]
    public_repos = len(owned)
    stars = sum(int(r.get("stargazers_count", 0)) for r in owned)
    forks = sum(int(r.get("forks_count", 0)) for r in owned)
    followers = int(profile.get("followers", 0))
    items = [
        ("PUBLIC REPOS", public_repos),
        ("TOTAL STARS", stars),
        ("FOLLOWERS", followers),
        ("TOTAL FORKS", forks),
    ]
    updated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d UTC")
    body = []
    for index, (label, value) in enumerate(items):
        x = 28 + index * 138
        body.append(
            f'<text x="{x}" y="105" fill="{c["text"]}" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="28" font-weight="700">{esc(fmt_number(value))}</text>'
        )
        body.append(
            f'<text x="{x}" y="131" fill="{c["sub"]}" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="10" font-weight="600" letter-spacing="1">{label}</text>'
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="590" height="185" viewBox="0 0 590 185">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#58a6ff"/><stop offset="1" stop-color="#8b5cf6"/></linearGradient></defs>
<rect x="1" y="1" width="588" height="183" rx="20" fill="{c['bg']}" stroke="{c['border']}" stroke-width="2"/>
<text x="28" y="38" fill="{c['text']}" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="17" font-weight="700" letter-spacing="2">GITHUB SIGNALS</text>
<rect x="28" y="51" width="120" height="3" rx="2" fill="url(#g)"/>
{''.join(body)}
<text x="28" y="162" fill="{c['sub']}" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="11">Updated {updated} · generated inside this repository</text>
</svg>'''


def collect_languages(repos: list[dict[str, Any]]) -> Counter[str]:
    totals: Counter[str] = Counter()
    candidates = [
        repo
        for repo in repos
        if not repo.get("fork")
        and not repo.get("archived")
        and repo.get("name") not in EXCLUDED_REPOS
    ]
    for repo in candidates:
        full_name = repo.get("full_name")
        if not full_name:
            continue
        try:
            data, _ = request_json(f"{API}/repos/{full_name}/languages")
            if isinstance(data, dict):
                for language, bytes_count in data.items():
                    totals[str(language)] += int(bytes_count)
        except Exception as exc:  # keep the remaining repositories usable
            print(f"warning: language request failed for {full_name}: {exc}", file=sys.stderr)
            primary = repo.get("language")
            if primary:
                totals[str(primary)] += 1
    return totals


def languages_svg(theme: str, totals: Counter[str]) -> str:
    c = theme_values(theme)
    palette = ["#58a6ff", "#8b5cf6", "#30bced", "#ff9f43", "#9fb3d0"]
    total = sum(totals.values()) or 1
    top = totals.most_common(5)
    if not top:
        top = [("Python", 1)]
        total = 1
    rows = []
    y = 78
    for index, (language, amount) in enumerate(top):
        percent = amount / total * 100
        width = max(4, 390 * percent / 100)
        color = palette[index % len(palette)]
        rows.append(f'<text x="28" y="{y+5}" fill="{c["sub"]}" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="12">{esc(language)}</text>')
        rows.append(f'<rect x="150" y="{y-8}" width="390" height="12" rx="6" fill="{c["track"]}"/>')
        rows.append(f'<rect x="150" y="{y-8}" width="{width:.1f}" height="12" rx="6" fill="{color}"/>')
        rows.append(f'<text x="554" y="{y+4}" text-anchor="end" fill="{c["text"]}" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="11">{percent:.1f}%</text>')
        y += 22
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="590" height="185" viewBox="0 0 590 185">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#58a6ff"/><stop offset="1" stop-color="#8b5cf6"/></linearGradient></defs>
<rect x="1" y="1" width="588" height="183" rx="20" fill="{c['bg']}" stroke="{c['border']}" stroke-width="2"/>
<text x="28" y="38" fill="{c['text']}" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="17" font-weight="700" letter-spacing="2">LANGUAGE SPECTRUM</text>
<rect x="28" y="51" width="120" height="3" rx="2" fill="url(#g)"/>
{''.join(rows)}
</svg>'''


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    try:
        profile, _ = request_json(f"{API}/users/{urllib.parse.quote(OWNER)}")
        repos = paginate(f"{API}/users/{urllib.parse.quote(OWNER)}/repos?type=owner&sort=updated")
        languages = collect_languages(repos)
    except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"warning: GitHub API unavailable; preserving existing profile assets: {exc}", file=sys.stderr)
        return 0

    for theme in ("dark", "light"):
        (ASSETS / f"stats-{theme}.svg").write_text(stats_svg(theme, profile, repos), encoding="utf-8")
        (ASSETS / f"languages-{theme}.svg").write_text(languages_svg(theme, languages), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
