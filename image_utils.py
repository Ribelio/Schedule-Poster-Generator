"""
Image loading and processing utilities.
"""

import os
import hashlib
from io import BytesIO
from urllib.request import urlopen, Request
from urllib.parse import urlparse
from PIL import Image

# Cache directory for downloaded images
CACHE_DIR = "output/images/covers"


def _get_cache_filename(url, volume=None):
    """
    Generate a cache filename for an image.
    
    Args:
        url: URL of the image
        volume: Optional volume number to use as filename
        
    Returns:
        Cache file path
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    if volume is not None:
        # Use volume number as filename, preserve original extension
        parsed_url = urlparse(url)
        ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
        return os.path.join(CACHE_DIR, f"volume_{volume}{ext}")
    else:
        # Use URL hash as filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        parsed_url = urlparse(url)
        ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
        return os.path.join(CACHE_DIR, f"{url_hash}{ext}")


def load_image(url, volume=None):
    """
    Load image from URL or local cache and return as PIL Image.
    Downloads and caches the image if not already cached.
    
    Args:
        url: URL of the image to load
        volume: Optional volume number for better cache filename
        
    Returns:
        PIL Image object or None if loading fails
    """
    if not url:
        return None
    
    # Get cache filename
    cache_path = _get_cache_filename(url, volume)
    
    # Try to load from cache first
    if os.path.exists(cache_path):
        try:
            return Image.open(cache_path)
        except Exception as e:
            print(f"Failed to load cached image {cache_path}: {e}")
            # If cached file is corrupted, delete it and re-download
            try:
                os.remove(cache_path)
            except:
                pass
    
    # Download image if not in cache
    try:
        print(f"Downloading image for volume {volume or 'unknown'}...")
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req) as u:
            data = BytesIO(u.read())
        img = Image.open(data)
        
        # Save to cache
        img.save(cache_path)
        print(f"Cached image to {cache_path}")
        
        return img
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

