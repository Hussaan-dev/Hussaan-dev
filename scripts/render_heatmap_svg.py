"""
render_heatmap_svg.py
Render data/contributions.json as a 53-week x 7-day calendar of rounded
boxes, revealed with a diagonal slide-down (plays once, no looping).

Usage:
    python scripts/render_heatmap_svg.py
Writes:
    contrib-heatmap.svg
"""
import json
from datetime import datetime

IN_PATH = "data/contributions.json"
OUT_PATH = "contrib-heatmap.svg"

# Set both to None to show the full last-year calendar (blog default).
# Set to "YYYY-MM-DD" strings to crop to a shorter window instead.
START_DATE = "2026-06-01"
END_DATE = None   # None = up through the most recent day in the data

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#           none      lvl1       lvl2       lvl3       lvl4       lvl5 (neon top)

BOX = 11
GAP = 3
CELL = BOX + GAP
LEFT_PAD = 30      # room for weekday labels
TOP_PAD = 20        # room for month labels
BOTTOM_PAD = 34     # room for legend + stats footer
STAGGER = 0.006      # seconds between each box's reveal, driving the diagonal
REVEAL_DUR = 0.35

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # sparse labels like GitHub


def group_into_weeks(days):
    """Group day list into columns (weeks), Sunday-first, like GitHub."""
    weeks = []
    current_week = []
    for d in days:
        date = datetime.strptime(d["date"], "%Y-%m-%d")
        weekday = (date.weekday() + 1) % 7  # convert Mon=0..Sun=6 -> Sun=0..Sat=6
        if weekday == 0 and current_week:
            weeks.append(current_week)
            current_week = []
        # pad the first week so days align to the correct row
        if not current_week and weekday != 0:
            current_week = [None] * weekday
        current_week.append({**d, "weekday": weekday})
    if current_week:
        weeks.append(current_week)
    return weeks


def escape_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def filter_range(days, start_date, end_date):
    if start_date is None and end_date is None:
        return days
    filtered = [d for d in days
                if (start_date is None or d["date"] >= start_date)
                and (end_date is None or d["date"] <= end_date)]
    return filtered


def build_svg(data):
    days = filter_range(data["days"], START_DATE, END_DATE)

    # recompute the footer total for just the cropped range (not the full-year stat)
    def count_from_label(label):
        label = (label or "").lower()
        if label.startswith("no contributions") or not label:
            return 0
        parts = label.split()
        return int(parts[0]) if parts and parts[0].isdigit() else 0

    range_total = sum(count_from_label(d.get("label")) for d in days)
    stats = {**data["stats"], "total_last_year": range_total}

    weeks = group_into_weeks(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * CELL + 10
    height = TOP_PAD + 7 * CELL + BOTTOM_PAD

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Consolas, Menlo, monospace" font-size="10">'
    )
    parts.append(f'<style>.wk-label {{ fill: #8b949e; }} .box {{ opacity: 0; }}</style>')

    # weekday labels
    for wd, label in WEEKDAY_LABELS.items():
        y = TOP_PAD + wd * CELL + BOX * 0.8
        parts.append(f'<text x="0" y="{y:.0f}" class="wk-label">{label}</text>')

    # month labels: print a label the first time a week starts a new month
    seen_months = set()
    for wi, week in enumerate(weeks):
        first_real_day = next((d for d in week if d is not None), None)
        if not first_real_day:
            continue
        date = datetime.strptime(first_real_day["date"], "%Y-%m-%d")
        key = (date.year, date.month)
        if key not in seen_months:
            seen_months.add(key)
            x = LEFT_PAD + wi * CELL
            parts.append(f'<text x="{x:.0f}" y="{TOP_PAD - 6}" class="wk-label">{MONTH_NAMES[date.month - 1]}</text>')

    # boxes, diagonal reveal: delay based on (week + weekday) so it slides in
    # top-left to bottom-right diagonally rather than column by column
    idx = 0
    for wi, week in enumerate(weeks):
        for wd in range(7):
            day = week[wd] if wd < len(week) else None
            x = LEFT_PAD + wi * CELL
            y = TOP_PAD + wd * CELL
            if day is None:
                continue
            level = day.get("level", 0)
            color = PALETTE[min(level, len(PALETTE) - 1)]
            title = escape_xml(day.get("label") or day["date"])
            delay = (wi + wd) * STAGGER
            parts.append(
                f'<rect class="box" x="{x:.0f}" y="{y:.0f}" width="{BOX}" height="{BOX}" rx="2" '
                f'fill="{color}" transform="translate(0 -6)">'
                f'<title>{title}</title>'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{delay:.3f}s" dur="{REVEAL_DUR}s" fill="freeze" />'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="0 -6" to="0 0" begin="{delay:.3f}s" dur="{REVEAL_DUR}s" fill="freeze" '
                f'calcMode="spline" keySplines="0.25 0.1 0.25 1" additive="sum" />'
                f'</rect>'
            )
            idx += 1

    # legend: Less -> More
    legend_y = TOP_PAD + 7 * CELL + 16
    legend_x = LEFT_PAD
    parts.append(f'<text x="{legend_x}" y="{legend_y + 8}" class="wk-label">Less</text>')
    lx = legend_x + 32
    for color in PALETTE:
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="{BOX}" height="{BOX}" rx="2" fill="{color}" />')
        lx += CELL
    parts.append(f'<text x="{lx + 4}" y="{legend_y + 8}" class="wk-label">More</text>')

    # stats footer
    if START_DATE or END_DATE:
        footer = f"{stats['total_last_year']} contributions shown"
    else:
        footer = f"{stats['total_last_year']} contributions in the last year"
    parts.append(
        f'<text x="{width - 10:.0f}" y="{legend_y + 8}" text-anchor="end" class="wk-label">{escape_xml(footer)}</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    with open(IN_PATH) as f:
        data = json.load(f)
    svg = build_svg(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH}")
