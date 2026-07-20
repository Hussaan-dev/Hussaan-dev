"""
make_ascii_svg.py
Convert source-prepped.png into a self-typing, monochrome ASCII-art SVG.

Usage:
    python scripts/make_ascii_svg.py
Writes:
    avi-ascii.svg   (rename via OUT_PATH below if you like)
"""
from PIL import Image

# ---------- config ----------
IN_PATH = "source-prepped.png"
OUT_PATH = "avi-ascii.svg"
COLS = 100
ROWS = 53
FONT_SIZE = 9
CHAR_W = FONT_SIZE * 0.6      # monospace advance width
LINE_H = FONT_SIZE * 1.0
FILL_COLOR = "#c9d1d9"        # single light-gray fill (monochrome, no rainbow)
BG_COLOR = "transparent"
ROW_STAGGER = 0.045           # seconds between each row starting its wipe
ROW_WIPE_DUR = 0.5            # seconds for one row's left-to-right wipe

RAMP = " .`:-=+*cs#%@"        # bright (sparse) -> dark (dense)
# ^ leading space clears the background to nothing
# -----------------------------


def image_to_ascii_rows(path, cols, rows):
    img = Image.open(path).convert("L")
    # character cells are taller than wide, so correct aspect ratio on resize
    img = img.resize((cols, rows))
    pixels = list(img.getdata())

    ramp_len = len(RAMP)
    lines = []
    for r in range(rows):
        row_chars = []
        for c in range(cols):
            brightness = pixels[r * cols + c]  # 0=black .. 255=white
            idx = int((255 - brightness) / 255 * (ramp_len - 1))
            row_chars.append(RAMP[idx])
        lines.append("".join(row_chars))
    return lines


def escape_xml(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(lines):
    width = COLS * CHAR_W
    height = ROWS * LINE_H + 20

    svg_parts = []
    svg_parts.append(
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Consolas, Menlo, monospace" font-size="{FONT_SIZE}">'
    )
    svg_parts.append(
        f'<style>'
        f'.row {{ fill: {FILL_COLOR}; white-space: pre; }}'
        f'.clip-rect {{ animation-timing-function: steps(1, end); }}'
        f'</style>'
    )

    for r, line in enumerate(lines):
        text = escape_xml(line)
        clip_id = f"clip{r}"
        y = (r + 1) * LINE_H
        delay = r * ROW_STAGGER

        # clipPath rectangle animates its width from 0 -> full row width,
        # revealing the text left-to-right like it's being typed
        svg_parts.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{y - LINE_H}" height="{LINE_H}" width="0">'
            f'<animate attributeName="width" from="0" to="{width:.0f}" '
            f'begin="{delay:.3f}s" dur="{ROW_WIPE_DUR}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1" />'
            f'</rect>'
            f'</clipPath>'
        )
        svg_parts.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="0" y="{y}" class="row">{text}</text>'
            f'</g>'
        )
        # small "cursor" block riding the wipe edge, then vanishing
        svg_parts.append(
            f'<rect x="0" y="{y - LINE_H + 1}" width="{CHAR_W:.1f}" height="{LINE_H - 2:.1f}" '
            f'fill="{FILL_COLOR}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;0" '
            f'begin="{delay:.3f}s" dur="{ROW_WIPE_DUR}s" fill="freeze" />'
            f'<animate attributeName="x" from="0" to="{width - CHAR_W:.1f}" '
            f'begin="{delay:.3f}s" dur="{ROW_WIPE_DUR}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1" />'
            f'</rect>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


if __name__ == "__main__":
    lines = image_to_ascii_rows(IN_PATH, COLS, ROWS)
    svg = build_svg(lines)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({COLS}x{ROWS} chars)")
