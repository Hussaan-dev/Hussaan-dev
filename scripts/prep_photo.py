"""
prep_photo.py
Prep a source photo for ASCII conversion:
  1. Remove background (rembg) so only the subject remains
  2. Boost local contrast (CLAHE) so a flat face gets real highlight/shadow
  3. Composite onto pure white so background maps to blank glyph later

Usage:
    python scripts/prep_photo.py source-photo.jpg
Writes:
    source-prepped.png
"""
import sys
import io
import numpy as np
import cv2
from PIL import Image
from rembg import remove

def prep(src_path: str, out_path: str = "source-prepped.png"):
    with open(src_path, "rb") as f:
        input_bytes = f.read()

    # 1. Remove background -> RGBA with subject isolated
    cutout_bytes = remove(input_bytes)
    cutout = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")

    # 2. Boost local contrast on the subject (CLAHE on the L channel)
    rgb = np.array(cutout.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    contrasted_rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    contrasted = Image.fromarray(contrasted_rgb).convert("RGBA")
    contrasted.putalpha(cutout.getchannel("A"))  # keep original cutout mask

    # 3. Composite onto pure white background
    white_bg = Image.new("RGBA", contrasted.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, contrasted).convert("L")  # grayscale

    composited.save(out_path)
    print(f"wrote {out_path} ({composited.size[0]}x{composited.size[1]})")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-photo.jpg"
    prep(src)
