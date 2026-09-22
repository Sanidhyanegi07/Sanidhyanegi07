"""
Generate a premium contribution calendar SVG with hover tooltips.

Fetches contribution data from GitHub's GraphQL API and renders a styled SVG
where each cell has a <title> element that shows the date + contribution count
as a native browser tooltip on hover.

Usage:
    python generate-calendar.py <github_username> <output_path>

Requires:
    GITHUB_TOKEN environment variable set with a valid token.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime


# ─── CONFIG ───────────────────────────────────────────────────────────
BG_COLOR = "#020306"
BORDER_COLOR = "#58a6ff"
TEXT_COLOR = "#8b949e"
LABEL_COLOR = "#58a6ff"
MONTH_LABEL_COLOR = "#c9d1d9"

# Contribution level colors (0 = no contributions → 4 = max)
LEVEL_COLORS = [
    "#161b22",   # Level 0 — empty
    "#0d2240",   # Level 1 — low
    "#1158a0",   # Level 2 — medium
    "#1f6feb",   # Level 3 — high
    "#58a6ff",   # Level 4 — max
]

CELL_SIZE = 13
CELL_GAP = 3
CELL_RADIUS = 2
TOTAL_STEP = CELL_SIZE + CELL_GAP

LEFT_LABEL_WIDTH = 36
TOP_LABEL_HEIGHT = 24
PADDING_X = 20
PADDING_Y = 20
BOTTOM_PADDING = 50

DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]
MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]


def fetch_contributions(username: str, token: str) -> dict:
    """Fetch contribution data from GitHub GraphQL API."""
    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                contributionLevel
                date
                weekday
              }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"username": username}})
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload.encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "contribution-calendar-generator",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Error fetching contributions: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)

    if "errors" in data:
        print(f"GraphQL errors: {data['errors']}", file=sys.stderr)
        sys.exit(1)

    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def level_to_index(level_str: str) -> int:
    """Convert GitHub's contributionLevel string to a 0-4 index."""
    mapping = {
        "NONE": 0,
        "FIRST_QUARTILE": 1,
        "SECOND_QUARTILE": 2,
        "THIRD_QUARTILE": 3,
        "FOURTH_QUARTILE": 4,
    }
    return mapping.get(level_str, 0)


def format_date(date_str: str) -> str:
    """Format 'YYYY-MM-DD' into 'Sep 15, 2026'."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%b %d, %Y").replace(" 0", " ")


def generate_svg(calendar_data: dict, username: str) -> str:
    """Generate the contribution calendar SVG string."""
    weeks = calendar_data["weeks"]
    total = calendar_data["totalContributions"]
    num_weeks = len(weeks)

    # ── Dimensions ──
    grid_w = num_weeks * TOTAL_STEP - CELL_GAP
    grid_h = 7 * TOTAL_STEP - CELL_GAP

    content_w = LEFT_LABEL_WIDTH + grid_w
    content_h = TOP_LABEL_HEIGHT + grid_h

    svg_w = content_w + 2 * PADDING_X
    svg_h = content_h + 2 * PADDING_Y + BOTTOM_PADDING

    grid_x = PADDING_X + LEFT_LABEL_WIDTH
    grid_y = PADDING_Y + TOP_LABEL_HEIGHT

    # ── Begin SVG ──
    lines = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" '
        f'width="100%" height="100%">'
    )

    # ── Defs ──
    lines.append("  <defs>")
    style_css = f"""    <style>
      @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&amp;display=swap');
      .cal-label {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; fill: {TEXT_COLOR}; }}
      .cal-month {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; fill: {MONTH_LABEL_COLOR}; font-weight: 500; }}
      .cal-title {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; fill: {LABEL_COLOR}; font-weight: 700; letter-spacing: 2px; }}
      .cal-total {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; fill: {TEXT_COLOR}; }}
      .cal-legend-label {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; fill: {TEXT_COLOR}; }}
    </style>"""
    lines.append(style_css)

    # Glow filter
    lines.append('    <filter id="cell-glow" x="-50%" y="-50%" width="200%" height="200%">')
    lines.append('      <feGaussianBlur stdDeviation="2" result="blur"/>')
    lines.append("      <feMerge>")
    lines.append('        <feMergeNode in="blur"/>')
    lines.append('        <feMergeNode in="SourceGraphic"/>')
    lines.append("      </feMerge>")
    lines.append("    </filter>")

    # Border glow
    lines.append('    <filter id="border-glow" x="-2%" y="-2%" width="104%" height="104%">')
    lines.append('      <feGaussianBlur stdDeviation="3" result="blur"/>')
    lines.append("      <feMerge>")
    lines.append('        <feMergeNode in="blur"/>')
    lines.append('        <feMergeNode in="SourceGraphic"/>')
    lines.append("      </feMerge>")
    lines.append("    </filter>")

    lines.append("  </defs>")

    # ── Background ──
    lines.append(
        f'  <rect width="{svg_w}" height="{svg_h}" rx="12" fill="{BG_COLOR}"/>'
    )

    # ── Animated Border ──
    lines.append(
        f'  <rect x="0.5" y="0.5" width="{svg_w - 1}" height="{svg_h - 1}" '
        f'rx="12" fill="none" stroke="{BORDER_COLOR}" stroke-width="1" '
        f'opacity="0.2" filter="url(#border-glow)">'
    )
    lines.append('    <animate attributeName="opacity" values="0.1;0.3;0.1" dur="4s" repeatCount="indefinite"/>')
    lines.append("  </rect>")

    # ── Title ──
    title_y = PADDING_Y + 10
    lines.append(
        f'  <text x="{PADDING_X}" y="{title_y}" class="cal-title">'
        f"&gt; CONTRIBUTION_GRID // {username.upper()}</text>"
    )

    # ── Day labels (Mon, Wed, Fri) ──
    for i, label in enumerate(DAY_LABELS):
        if label:
            y = grid_y + i * TOTAL_STEP + CELL_SIZE - 2
            lines.append(
                f'  <text x="{PADDING_X}" y="{y}" class="cal-label">{label}</text>'
            )

    # ── Month labels ──
    prev_month = -1
    for wi, week in enumerate(weeks):
        if not week["contributionDays"]:
            continue
        first_day = week["contributionDays"][0]
        dt = datetime.strptime(first_day["date"], "%Y-%m-%d")
        month = dt.month
        if month != prev_month:
            prev_month = month
            x = grid_x + wi * TOTAL_STEP
            y = grid_y - 6
            lines.append(
                f'  <text x="{x}" y="{y}" class="cal-month">'
                f"{MONTH_NAMES[month - 1]}</text>"
            )

    # ── Contribution cells ──
    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            level = level_to_index(day["contributionLevel"])
            count = day["contributionCount"]
            date_str = format_date(day["date"])
            weekday = day["weekday"]

            x = grid_x + wi * TOTAL_STEP
            y = grid_y + weekday * TOTAL_STEP

            color = LEVEL_COLORS[level]

            # Tooltip text
            if count == 0:
                tooltip = f"No contributions on {date_str}"
            elif count == 1:
                tooltip = f"1 contribution on {date_str}"
            else:
                tooltip = f"{count} contributions on {date_str}"

            # Cell with hover effect
            cell_attrs = (
                f'x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
                f'rx="{CELL_RADIUS}" fill="{color}"'
            )
            if level >= 3:
                cell_attrs += f' filter="url(#cell-glow)"'

            lines.append(f"  <rect {cell_attrs}>")
            lines.append(f"    <title>{tooltip}</title>")
            lines.append("  </rect>")

    # ── Bottom area: total + legend ──
    bottom_y = grid_y + grid_h + 24

    # Total contributions text
    lines.append(
        f'  <text x="{PADDING_X}" y="{bottom_y}" class="cal-total">'
        f"{total:,} contributions in the last year</text>"
    )

    # Legend
    legend_x = grid_x + grid_w - 140
    lines.append(
        f'  <text x="{legend_x - 30}" y="{bottom_y}" '
        f'class="cal-legend-label">Less</text>'
    )
    for i, c in enumerate(LEVEL_COLORS):
        lx = legend_x + i * (CELL_SIZE + 3)
        ly = bottom_y - CELL_SIZE + 3
        lines.append(
            f'  <rect x="{lx}" y="{ly}" width="{CELL_SIZE}" '
            f'height="{CELL_SIZE}" rx="{CELL_RADIUS}" fill="{c}"/>'
        )
    lines.append(
        f'  <text x="{legend_x + 5 * (CELL_SIZE + 3) + 2}" y="{bottom_y}" '
        f'class="cal-legend-label">More</text>'
    )

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate-calendar.py <username> <output_path>", file=sys.stderr)
        sys.exit(1)

    username = sys.argv[1]
    output_path = sys.argv[2]
    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        print("Error: GITHUB_TOKEN environment variable is required.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching contributions for {username}...")
    calendar_data = fetch_contributions(username, token)
    print(f"Total contributions: {calendar_data['totalContributions']}")

    print("Generating SVG...")
    svg_content = generate_svg(calendar_data, username)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
