"""
make_info_card.py
Hand-authored neofetch-style SVG panel that fades/slides in line by line.

Usage:
    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py   # frozen frame for Quick Look
Writes:
    info-card.svg
"""
import os

# ---------- EDIT ME: your content ----------
USERNAME = "hussaan-dev"
FIELDS = [
    ("Now", "BS Computer Science @ GCU Lahore"),
    ("Learning", "Docker -> FastAPI next"),
    ("Stack", "Python · Django · SQL"),
    ("Projects", "Clinic booking system, Expense splitter, Pokedex CLI"),
]
ACCENT = "#39d353"   # key color
TEXT_COLOR = "#c9d1d9"
TITLEBAR_COLOR = "#8b949e"
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
# --------------------------------------------

WIDTH = 490
ROW_H = 34
PAD_X = 24
TITLEBAR_H = 34
FONT = "Consolas, Menlo, monospace"
STAGGER = 0.15
FADE_DUR = 0.4


def escape_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(static=False):
    height = TITLEBAR_H + len(FIELDS) * ROW_H + 24

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {WIDTH} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="{FONT}">'
    )
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8" '
        f'fill="{BG_COLOR}" stroke="{BORDER_COLOR}" />'
    )

    # title bar with fake window dots
    parts.append(f'<rect x="0" y="0" width="{WIDTH}" height="{TITLEBAR_H}" rx="8" fill="{BG_COLOR}" />')
    for i, dot_color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{20 + i * 18}" cy="{TITLEBAR_H / 2}" r="5" fill="{dot_color}" />')
    parts.append(
        f'<text x="{WIDTH / 2}" y="{TITLEBAR_H / 2 + 4}" text-anchor="middle" '
        f'fill="{TITLEBAR_COLOR}" font-size="12">{escape_xml(USERNAME)}@github: neofetch</text>'
    )

    # rows
    for i, (key, value) in enumerate(FIELDS):
        y = TITLEBAR_H + 24 + i * ROW_H
        delay = i * STAGGER
        opacity_attr = "" if static else 'opacity="0"'
        anim = "" if static else (
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{delay:.2f}s" dur="{FADE_DUR}s" fill="freeze" />'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="-12 0" to="0 0" begin="{delay:.2f}s" dur="{FADE_DUR}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1" />'
        )
        parts.append(
            f'<g {opacity_attr} transform="translate({"0 0" if static else "-12 0"})">'
            f'{anim}'
            f'<text x="{PAD_X}" y="{y}" font-size="14" font-weight="bold" fill="{ACCENT}">{escape_xml(key)}</text>'
            f'<text x="{PAD_X + 110}" y="{y}" font-size="14" fill="{TEXT_COLOR}">{escape_xml(value)}</text>'
            f'</g>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    static = os.environ.get("STATIC") == "1"
    svg = build_svg(static=static)
    with open("info-card.svg", "w") as f:
        f.write(svg)
    print(f"wrote info-card.svg (static={static})")