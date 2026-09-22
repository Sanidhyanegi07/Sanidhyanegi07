#!/usr/bin/env python3
"""
Decorate Platane/snk snake SVG with dates, month labels, day labels,
and an obsidian/cyan HUD systems telemetry container.

Usage:
    python decorate-snake.py <path_to_dark_svg> [<path_to_light_svg>]
"""

import sys
import os
import re
from datetime import datetime, timezone, timedelta

def decorate_snake_svg(svg_path: str, is_dark: bool = True):
    if not os.path.exists(svg_path):
        print(f"File not found: {svg_path}", file=sys.stderr)
        return

    with open(svg_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract style block
    style_match = re.search(r"<style>([\s\S]*?)</style>", content)
    styles = style_match.group(1) if style_match else ""

    # Enforce neon cyan snake and deep space blue/obsidian dots
    if is_dark:
        styles = re.sub(r"--cs:[^;]+;", "--cs:#58a6ff;", styles)
        styles = re.sub(r"--c0:[^;]+;", "--c0:#161b22;", styles)
        styles = re.sub(r"--c1:[^;]+;", "--c1:#0d2240;", styles)
        styles = re.sub(r"--c2:[^;]+;", "--c2:#1158a0;", styles)
        styles = re.sub(r"--c3:[^;]+;", "--c3:#1f6feb;", styles)
        styles = re.sub(r"--c4:[^;]+;", "--c4:#58a6ff;", styles)
        styles = re.sub(r"--ce:[^;]+;", "--ce:#161b22;", styles)
        styles = re.sub(r"--cb:[^;]+;", "--cb:rgba(27,31,35,0.2);", styles)

    # Extract all rects from first <rect to the end before </svg>
    first_rect_idx = content.find("<rect")
    if first_rect_idx == -1:
        print(f"No rect elements found in {svg_path}")
        return

    last_svg_idx = content.rfind("</svg>")
    rects_content = content[first_rect_idx:last_svg_idx]

    # Calculate 53 weeks timeline
    now = datetime.now(timezone.utc)
    # GitHub weekday: 0 = Sun, 1 = Mon, ..., 6 = Sat
    # Python weekday(): 0 = Mon, ..., 6 = Sun
    gh_day = (now.weekday() + 1) % 7
    last_sunday = now - timedelta(days=gh_day)
    start_sunday = last_sunday - timedelta(weeks=52)

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_labels = []
    prev_month = -1
    last_x = -100

    grid_offset_x = 52
    grid_offset_y = 64

    for w in range(53):
        d = start_sunday + timedelta(weeks=w)
        m = d.month - 1
        x = grid_offset_x + w * 16
        if m != prev_month:
            if x - last_x >= 30:
                month_labels.append({"x": x + 2, "month": month_names[m]})
                last_x = x
                prev_month = m

    start_date_str = f"{month_names[start_sunday.month - 1].upper()} {start_sunday.year}"
    end_date_str = f"{month_names[now.month - 1].upper()} {now.year}"

    total_w = 956
    total_h = 228
    bg_color = "#020306" if is_dark else "#f6f8fa"
    border_color = "#58a6ff" if is_dark else "#0969da"
    header_color = "#58a6ff" if is_dark else "#0969da"
    meta_color = "#8b949e" if is_dark else "#57606a"
    day_color = "#6e7681" if is_dark else "#8c959f"

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {total_h}" width="100%" height="100%">')
    lines.append("  <defs>")
    lines.append("    <style>")
    lines.append("      @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&amp;display=swap');")
    lines.append(f"      .hud-title {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; fill: {header_color}; font-weight: 700; letter-spacing: 2px; }}")
    lines.append(f"      .hud-dates {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; fill: {meta_color}; letter-spacing: 1.5px; }}")
    lines.append(f"      .hud-month {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; fill: {meta_color}; font-weight: 500; }}")
    lines.append(f"      .hud-day {{ font-family: 'JetBrains Mono', monospace; font-size: 9px; fill: {day_color}; font-weight: 500; text-anchor: end; }}")
    lines.append(f"      .hud-legend {{ font-family: 'JetBrains Mono', monospace; font-size: 9px; fill: {day_color}; }}")
    lines.append(f"      {styles}")
    lines.append("    </style>")
    lines.append('    <filter id="neon-glow" x="-50%" y="-50%" width="200%" height="200%">')
    lines.append('      <feGaussianBlur stdDeviation="2.5" result="blur"/>')
    lines.append('      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>')
    lines.append("    </filter>")
    lines.append("  </defs>")
    lines.append("")
    lines.append("  <!-- Obsidian Container -->")
    lines.append(f'  <rect width="{total_w}" height="{total_h}" rx="12" fill="{bg_color}"/>')
    lines.append(f'  <rect x="0.5" y="0.5" width="{total_w - 1}" height="{total_h - 1}" rx="12" fill="none" stroke="{border_color}" stroke-width="1" opacity="0.2"/>')
    lines.append("")
    lines.append("  <!-- HUD Header -->")
    lines.append('  <g transform="translate(24, 24)">')
    lines.append('    <circle cx="4" cy="-3" r="3.5" fill="#58a6ff" filter="url(#neon-glow)">')
    lines.append('      <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite"/>')
    lines.append('    </circle>')
    lines.append('    <text x="16" y="0" class="hud-title">&gt; SYS.TELEMETRY // CONTRIBUTION_STREAM</text>')
    lines.append(f'    <text x="{total_w - 48}" y="0" class="hud-dates" text-anchor="end">[ {start_date_str} — {end_date_str} ]</text>')
    lines.append("  </g>")
    lines.append("")
    lines.append(f'  <line x1="24" y1="36" x2="{total_w - 24}" y2="36" stroke="{border_color}" stroke-width="1" opacity="0.15"/>')
    lines.append("")
    lines.append("  <!-- Month Labels -->")
    lines.append('  <g id="month-labels">')
    for m in month_labels:
        lines.append(f'    <text x="{m["x"]}" y="52" class="hud-month">{m["month"]}</text>')
    lines.append("  </g>")
    lines.append("")
    lines.append("  <!-- Day Labels -->")
    day_y_mon = grid_offset_y + 1 * 16 + 10
    day_y_wed = grid_offset_y + 3 * 16 + 10
    day_y_fri = grid_offset_y + 5 * 16 + 10
    lines.append('  <g id="day-labels">')
    lines.append(f'    <text x="{grid_offset_x - 10}" y="{day_y_mon}" class="hud-day">Mon</text>')
    lines.append(f'    <text x="{grid_offset_x - 10}" y="{day_y_wed}" class="hud-day">Wed</text>')
    lines.append(f'    <text x="{grid_offset_x - 10}" y="{day_y_fri}" class="hud-day">Fri</text>')
    lines.append("  </g>")
    lines.append("")
    lines.append("  <!-- Snake & Contribution Grid -->")
    lines.append(f'  <g transform="translate({grid_offset_x}, {grid_offset_y})">')
    lines.append(f"    {rects_content}")
    lines.append("  </g>")
    lines.append("")
    lines.append("  <!-- HUD Footer -->")
    bottom_y = total_h - 16
    lines.append(f'  <g transform="translate(24, {bottom_y})">')
    lines.append('    <text x="0" y="0" class="hud-legend">&gt; SENSOR_STREAM: CONTINUOUS_EVALUATION // 24H_SYNC</text>')
    lines.append(f'    <g transform="translate({total_w - 210}, -9)">')
    lines.append('      <text x="-8" y="9" class="hud-legend" text-anchor="end">Less</text>')
    lines.append('      <rect x="0" y="0" width="10" height="10" rx="2" fill="#161b22"/>')
    lines.append('      <rect x="14" y="0" width="10" height="10" rx="2" fill="#0d2240"/>')
    lines.append('      <rect x="28" y="0" width="10" height="10" rx="2" fill="#1158a0"/>')
    lines.append('      <rect x="42" y="0" width="10" height="10" rx="2" fill="#1f6feb"/>')
    lines.append('      <rect x="56" y="0" width="10" height="10" rx="2" fill="#58a6ff"/>')
    lines.append('      <text x="74" y="9" class="hud-legend">More</text>')
    lines.append("    </g>")
    lines.append("  </g>")
    lines.append("</svg>")

    new_content = "\n".join(lines)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Successfully decorated {svg_path} (length={len(new_content)})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python decorate-snake.py <svg_file1> [<svg_file2> ...]")
        sys.exit(1)

    for path in sys.argv[1:]:
        is_dark = "dark" in os.path.basename(path).lower() or True
        decorate_snake_svg(path, is_dark=is_dark)
