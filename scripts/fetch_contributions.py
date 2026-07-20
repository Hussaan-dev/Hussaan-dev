"""
fetch_contributions.py
Scrape the public contribution calendar HTML fragment GitHub serves at
https://github.com/users/<username>/contributions -- no token needed.

Usage:
    python scripts/fetch_contributions.py
Writes:
    data/contributions.json
"""
import json
import sys
from datetime import datetime
import requests
from bs4 import BeautifulSoup

USERNAME = "Hussaan-dev"
URL = f"https://github.com/users/{USERNAME}/contributions"


def fetch(username):
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": "profile-readme-bot"}, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # GitHub renders each day as a <td class="ContributionCalendar-day"> with
    # data-date/data-level, but the human-readable count ("3 contributions on
    # July 4th.") lives in a *separate* <tool-tip for="<td-id>"> element, not
    # in an aria-label/title on the cell itself. Build an id -> label map first.
    tooltip_by_id = {}
    for tip in soup.select("tool-tip[for]"):
        tooltip_by_id[tip.get("for")] = tip.get_text(strip=True)

    days = []
    cells = soup.select("td.ContributionCalendar-day, rect.ContributionCalendar-day")
    for cell in cells:
        date = cell.get("data-date")
        level = cell.get("data-level")
        if date is None:
            continue
        cell_id = cell.get("id")
        count_text = tooltip_by_id.get(cell_id, "") or cell.get("aria-label") or cell.get("title") or ""
        days.append({
            "date": date,
            "level": int(level) if level is not None else 0,
            "label": count_text.strip(),
        })

    days.sort(key=lambda d: d["date"])
    return days


def extract_count(label):
    # aria-label examples: "No contributions on ...", "3 contributions on ..."
    label = label.lower()
    if label.startswith("no contributions"):
        return 0
    parts = label.split()
    if parts and parts[0].isdigit():
        return int(parts[0])
    return 0


def derive_stats(days):
    counts = [extract_count(d["label"]) for d in days]
    total = sum(counts)

    # current streak (from the end, counting back while count > 0)
    current_streak = 0
    for c in reversed(counts):
        if c > 0:
            current_streak += 1
        else:
            break

    # longest streak
    longest_streak = 0
    running = 0
    for c in counts:
        if c > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_idx = max(range(len(counts)), key=lambda i: counts[i]) if counts else None
    best_day = days[best_idx]["date"] if best_idx is not None else None
    best_count = counts[best_idx] if best_idx is not None else 0

    monthly = {}
    for d, c in zip(days, counts):
        month = d["date"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0) + c

    return {
        "total_last_year": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "best_day_count": best_count,
        "monthly_totals": monthly,
    }


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    days = fetch(username)
    if not days:
        print(f"warning: no contribution cells found for {username} -- GitHub markup may differ", file=sys.stderr)
    stats = derive_stats(days)
    out = {
        "username": username,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }
    with open("data/contributions.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote data/contributions.json ({len(days)} days, {stats['total_last_year']} contributions)")
