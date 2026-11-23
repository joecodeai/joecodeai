"""Render an activity card (contributions, repositories, languages) from the GitHub API.

Runs in GitHub Actions with the workflow token and writes an SVG that matches the rest of the
profile artwork. Standard library only.

    GITHUB_TOKEN=... python scripts/stats.py --user joecodeai --out dist/stats.svg
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import UTC, datetime
from html import escape
from pathlib import Path

from build_assets import (
    BLUE,
    CYAN,
    DIM,
    MAGENTA,
    MONO,
    MUTED,
    SANS,
    TEXT,
    VIOLET,
    card_bg,
    card_defs,
    neon_gradient,
    svg,
)

# Notebooks inflate byte counts with outputs and markup, so they would drown everything else.
IGNORED_LANGUAGES = {
    "Jupyter Notebook",
    "HTML",
    "CSS",
    "Dockerfile",
    "Makefile",
    "Shell",
    "HCL",
    "Smarty",
    "Go Template",
}
# Linguist labels protobuf-style .pb files as PureBasic.
IGNORED_LANGUAGES |= {"PureBasic"}
LANG_COLORS = [CYAN, BLUE, VIOLET, MAGENTA, "#f59e0b", "#22c55e"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions }
    }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
  }
}
"""


def fetch(login: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]


def summarise(user: dict) -> dict:
    cc = user["contributionsCollection"]
    repos = user["repositories"]
    sizes: dict[str, int] = {}
    for repo in repos["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name not in IGNORED_LANGUAGES:
                sizes[name] = sizes.get(name, 0) + edge["size"]
    total = sum(sizes.values()) or 1
    top = sorted(sizes.items(), key=lambda kv: -kv[1])[:6]
    return {
        "contributions": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "pull_requests": cc["totalPullRequestContributions"],
        "repos": repos["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos["nodes"]),
        "languages": [(name, size / total) for name, size in top],
    }


def top_language_tile(languages: list[tuple[str, float]]) -> tuple[str, str, str]:
    if not languages:
        return ("-", "primary language", "")
    name, share = languages[0]
    return (name, "primary language", f"{share * 100:.0f}% of code")


def render(s: dict, login: str) -> str:
    w, h = 1000, 250
    tiles = [
        (f"{s['contributions']:,}", "contributions", "last 12 months"),
        (f"{s['commits']:,}", "commits", "last 12 months"),
        (f"{s['repos']:,}", "public repos", "original work"),
        top_language_tile(s["languages"]),
    ]
    out = []
    for i, (value, label, sub) in enumerate(tiles):
        x = 32 + (i % 2) * 200
        y = 34 + (i // 2) * 98
        out.append(
            f'<g class="pop" style="animation-delay:{0.1 + i * 0.12:.2f}s">'
            f'<rect x="{x}" y="{y}" width="188" height="86" rx="12" fill="#ffffff" fill-opacity=".035" '
            f'stroke="#ffffff" stroke-opacity=".09"/>'
            f'<text x="{x + 16}" y="{y + 38}" class="sans" font-size="28" font-weight="800" fill="url(#neon)">'
            f"{escape(value)}</text>"
            f'<text x="{x + 16}" y="{y + 60}" class="mono" font-size="12" fill="{MUTED}">{label}</text>'
            f'<text x="{x + 16}" y="{y + 75}" class="mono" font-size="10.5" fill="{DIM}">{sub}</text></g>'
        )

    # Language split: one stacked bar plus a legend.
    lx, ly, lw = 460, 58, 508
    out.append(
        f'<text x="{lx}" y="44" class="mono" font-size="12" fill="{MUTED}" letter-spacing="1">'
        f"LANGUAGES · by code size, public repos</text>"
    )
    x = float(lx)
    for i, (name, share) in enumerate(s["languages"]):
        seg = max(lw * share, 3)
        color = LANG_COLORS[i % len(LANG_COLORS)]
        out.append(
            f'<rect x="{x:.1f}" y="{ly}" width="0" height="12" fill="{color}">'
            f'<animate attributeName="width" from="0" to="{seg:.1f}" dur=".9s" begin="{0.2 + i * 0.12:.2f}s" '
            f'fill="freeze"/></rect>'
        )
        x += seg
        col, row = i % 2, i // 2
        tx, ty = lx + col * 260, ly + 46 + row * 34
        out.append(
            f'<circle cx="{tx + 6}" cy="{ty - 4}" r="5" fill="{color}"/>'
            f'<text x="{tx + 20}" y="{ty}" class="sans" font-size="15" fill="{TEXT}">{escape(name)}</text>'
            f'<text x="{tx + 230}" y="{ty}" text-anchor="end" class="mono" font-size="13" fill="{MUTED}">'
            f"{share * 100:.1f}%</text>"
        )
    out.append(
        f'<rect x="{lx}" y="{ly}" width="{lw}" height="12" rx="6" fill="none" stroke="#ffffff" stroke-opacity=".1"/>'
    )
    stamp = datetime.now(UTC).strftime("%d %b %Y")
    out.append(
        f'<text x="{w - 32}" y="{h - 20}" text-anchor="end" class="mono" font-size="10.5" fill="{DIM}">'
        f"github.com/{escape(login)} · updated {stamp}</text>"
    )

    style = (
        f".mono{{font-family:{MONO}}}.sans{{font-family:{SANS}}}"
        "@keyframes pop{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
        ".pop{opacity:0;animation:pop .5s ease-out forwards}"
    )
    body = "<defs>" + card_defs(w, h) + neon_gradient("neon", 200, 6) + "</defs>" + card_bg(w, h) + "".join(out)
    langs = ", ".join(f"{n} {p * 100:.0f}%" for n, p in s["languages"])
    desc = (
        f"{s['contributions']} contributions and {s['commits']} commits in the last 12 months, "
        f"{s['repos']} public repositories, {s['stars']} stars. Languages: {langs}."
    )
    return svg(w, h, "GitHub activity", desc, body, style)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--user", default="joecodeai")
    p.add_argument("--out", default="dist/stats.svg")
    args = p.parse_args()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("set GITHUB_TOKEN")
    summary = summarise(fetch(args.user, token))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(summary, args.user), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "languages"}), summary["languages"])


if __name__ == "__main__":
    main()
