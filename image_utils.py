"""
Image loading and processing utilities.
"""

from io import BytesIO
from urllib.request import urlopen, Request
from PIL import Image


def load_image(url):
    """
    Load image from URL and return as PIL Image.
    
    Args:
        url: URL of the image to load
        
    Returns:
        PIL Image object or None if loading fails
    """
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req) as u:
            data = BytesIO(u.read())
        return Image.open(data)
    except Exception as e:
        print(f"Failed to load {url}: {e}")
        return None


def center_crop_zoom(img_pil, zoom_factor=1.5):
    """
    Center-crop and zoom into an image to focus on the center (character art).
    This removes the 'fluff' (title text) at top/bottom.
    
    Args:
        img_pil: PIL Image object
        zoom_factor: How much to zoom (1.0 = no zoom, 1.5 = 1.5x zoom)
    
    Returns:
        Cropped PIL Image or None if input is None
    """
    if img_pil is None:
        return None
    
    width, height = img_pil.size
    
    # Calculate new dimensions (smaller = more zoom)
    new_width = int(width / zoom_factor)
    new_height = int(height / zoom_factor)
    
    # Calculate center crop coordinates
    left = (width - new_width) // 2
    top = (height - new_height) // 2
    right = left + new_width
    bottom = top + new_height
    
    # Crop and return
    return img_pil.crop((left, top, right, bottom))

