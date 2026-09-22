#!/usr/bin/env python3
"""
Inject hover tooltips (<title>) into the generated snake SVG.
Each contribution square gets a <title> with:
  YYYY-MM-DD: N contributions
"""

import json
import os
import re
import sys
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

USER = os.environ.get("GITHUB_REPOSITORY_OWNER", "Sanidhyanegi07")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

OUTPUTS = (
    Path("dist/github-snake.svg"),
    Path("dist/github-snake-dark.svg"),
)


def get_labels_from_graphql():
    """Fetch calendar data using GitHub GraphQL API (most reliable)."""
    if not GITHUB_TOKEN:
        return None

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"login": USER}}).encode("utf-8")
    req = Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "User-Agent": "github-actions-snake",
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        calendar = (
            data.get("data", {})
            .get("user", {})
            .get("contributionsCollection", {})
            .get("contributionCalendar", {})
        )
        weeks = calendar.get("weeks", [])
        labels = []
        for week in weeks:
            for day in week.get("contributionDays", []):
                date = day["date"]
                count = day["contributionCount"]
                unit = "contribution" if count == 1 else "contributions"
                labels.append(f"{date}: {count} {unit}")
        if labels:
            print(f"Loaded {len(labels)} days from GitHub GraphQL API.")
            return labels
    except Exception as e:
        print(f"GraphQL request failed, falling back to HTML scraping: {e}", file=sys.stderr)

    return None


def get_labels_from_html():
    """Fallback: Scrape user's public contributions page and parse calendar."""
    url = f"https://github.com/users/{USER}/contributions"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8")

    # 1. Parse tooltips: <tool-tip for="id">text</tool-tip>
    tooltips = {}
    for match in re.finditer(r'<tool-tip\b[^>]*for=["\']([^"\']+)["\'][^>]*>(.*?)</tool-tip>', html, re.DOTALL):
        tooltips[match.group(1)] = match.group(2).strip()

    # 2. Parse day cells: <td ... data-date="YYYY-MM-DD" ... id="..." ...>
    day_cells = []
    td_pattern = re.compile(r'<td\b[^>]*data-date=["\'](\d{4}-\d{2}-\d{2})["\'][^>]*id=["\']([^"\']+)["\'][^>]*>')
    for date, cell_id in td_pattern.findall(html):
        tip = tooltips.get(cell_id, "")
        if tip:
            m = re.match(r"^(\d+|No)\s+contributions?", tip, re.IGNORECASE)
            if m:
                count_str = "0" if m.group(1).lower() == "no" else m.group(1)
                count = int(count_str)
                unit = "contribution" if count == 1 else "contributions"
                label = f"{date}: {count} {unit}"
            else:
                label = f"{date}: {tip}"
        else:
            label = f"{date}: 0 contributions"
        day_cells.append((date, label))

    if day_cells:
        # Sort chronologically so calendar matches snk's week-by-week layout
        day_cells.sort(key=lambda x: x[0])
        labels = [label for _, label in day_cells]
        print(f"Loaded {len(labels)} days from GitHub HTML calendar.")
        return labels

    # 3. Legacy check: <rect ... data-date="..." data-count="...">
    legacy_pattern = re.compile(r'<rect\b[^>]*data-date=["\']([^"\']+)["\'][^>]*data-count=["\'](\d+)["\'][^>]*>')
    legacy_matches = legacy_pattern.findall(html)
    if legacy_matches:
        labels = [
            f"{date}: {count} {'contribution' if count == '1' else 'contributions'}"
            for date, count in legacy_matches
        ]
        print(f"Loaded {len(labels)} days from legacy rect calendar.")
        return labels

    raise RuntimeError("Could not parse contribution data from GitHub calendar.")


def get_calendar_labels():
    labels = get_labels_from_graphql()
    if labels:
        return labels
    return get_labels_from_html()


def add_titles(path: Path, labels):
    content = path.read_text(encoding="utf-8")

    # Match self-closing calendar rects: <rect class="c..." ... rx="2" ry="2"/>
    # Day cells in Platane/snk have class starting with "c" and are self-closing
    day_rect_pattern = re.compile(r'<rect\b[^>]*\bclass=["\']c[^>]*\/>')
    rects = list(day_rect_pattern.finditer(content))

    if not rects:
        # Fallback to matching any rect if specific class isn't found
        rects = list(re.finditer(r"<rect\b[^>]*\/>", content))

    print(f"{path.name}: Found {len(rects)} day cells to tag (labels available: {len(labels)}).")

    new_parts = []
    last = 0
    count = min(len(rects), len(labels))

    for i in range(count):
        match = rects[i]
        start, end = match.span()
        new_parts.append(content[last:start])
        label = escape(labels[i])
        rect_str = match.group(0)
        # Convert self-closing tag to <rect ...><title>...</title></rect>
        tagged_rect = re.sub(r"/>$", f"><title>{label}</title></rect>", rect_str)
        new_parts.append(tagged_rect)
        last = end

    new_parts.append(content[last:])
    path.write_text("".join(new_parts), encoding="utf-8")
    print(f"{path.name}: Successfully injected {count} tooltips.")


def main():
    existing_outputs = [p for p in OUTPUTS if p.exists()]
    if not existing_outputs:
        print("No output SVG files found to process.")
        return

    labels = get_calendar_labels()
    for output in existing_outputs:
        add_titles(output, labels)


if __name__ == "__main__":
    main()
