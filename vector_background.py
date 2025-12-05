"""
Simple utility to create a high-contrast PNG stencil from an image.
Uses PIL for image processing - no vectorization needed.
"""

from PIL import Image, ImageEnhance
import ssl
import os
from urllib.request import urlopen, Request
from io import BytesIO

# Configuration
IMAGE_URL = "https://static.wikia.nocookie.net/choujin-x/images/9/9f/Choujin_X_art.png"
OUTPUT_DIR = "output/images"
OUTPUT_PNG = "background_lineart.png"


def process_image():
    """Download and process image to create a high-contrast stencil PNG."""
    # Bypass SSL for some scrapers
    ssl._create_default_https_context = ssl._create_unverified_context

    print(f"Downloading {IMAGE_URL}...")
    try:
        req = Request(IMAGE_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req) as u:
            data = BytesIO(u.read())
        img = Image.open(data)
    except Exception as e:
        print(f"Failed to download: {e}")
        return

    # Convert to grayscale
    gray = img.convert("L")

    # Enhance contrast to create a stencil effect
    # Increase contrast to make it more black and white
    enhancer = ImageEnhance.Contrast(gray)
    high_contrast = enhancer.enhance(2.5)  # Increase contrast

    # Apply threshold to create binary black/white image
    # Values below threshold become black (0), above become white (255)
    threshold = 128
    binary = high_contrast.point(lambda x: 0 if x < threshold else 255, mode="1")

    # Convert back to grayscale for saving (mode '1' is 1-bit, we want 8-bit grayscale)
    stencil = binary.convert("L")

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save the stencil PNG
    png_path = os.path.join(OUTPUT_DIR, OUTPUT_PNG)
    stencil.save(png_path)
    print(f"Saved High-Contrast Stencil: {png_path}")


if __name__ == "__main__":
    process_image()
