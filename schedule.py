import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, PathPatch
from matplotlib.path import Path
from matplotlib.patheffects import withStroke
from io import BytesIO
from urllib.request import urlopen, Request
from PIL import Image
import numpy as np
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

# Center-crop-zoom factor: Higher values = more zoom into center (crops more)
# Note: This is now less critical since we use fit-to-width scaling
ZOOM_FACTOR = 0.95  # Reduced since we're fitting to width now

# Vertical offset for image positioning: Positive values move image higher
# (0.0 = centered, 0.1 = slightly higher, 0.2 = noticeably higher)
VERTICAL_OFFSET = -0.1  # Adjust this to move the focus higher in the frame

# List of dates and volume pairs
schedule = [
    # ("November 15, 2025", [1]),
    ("November 22, 2025", [2, 3]),
    ("November 29, 2025", [4, 5]),
    ("December 6, 2025", [6, 7]),
    ("December 13, 2025", [8, 9]),
    ("December 20, 2025", [10, 11]),
    ("December 27, 2025", [12, 13, 14])
]

# URLs for volume covers
cover_urls = {
    1: "https://m.media-amazon.com/images/I/41H1JFuv+0L.jpg",
    2: "https://m.media-amazon.com/images/I/71Gj55-N1kL.jpg",
    3: "https://m.media-amazon.com/images/I/71wLxeDsuUL.jpg",
    4: "https://m.media-amazon.com/images/I/61xNxUCXEqL.jpg",
    5: "https://m.media-amazon.com/images/I/71h0-rh4FhL.jpg",
    6: "https://m.media-amazon.com/images/I/71s5Zu1-BzL.jpg",
    7: "https://m.media-amazon.com/images/I/71PX3Euwa0L.jpg",
    8: "https://m.media-amazon.com/images/I/61n17DEPKEL.jpg",
    9: "https://m.media-amazon.com/images/I/71HN34iWcEL.jpg",
    10: "https://m.media-amazon.com/images/I/710m+JUnVWL.jpg",
    11: "https://m.media-amazon.com/images/I/81nZp9xd1-L.jpg",
    # UPDATES NEEDED BELOW:
    # Volume 12 is the Green cover featuring Tokio
    12: "https://static.wikia.nocookie.net/choujin-x/images/a/a9/Volume_12.jpg", 
    # Volume 13 is the Red cover featuring Batista
    13: "https://static.wikia.nocookie.net/choujin-x/images/b/b6/Volume_13.png",   
    14: "https://static.wikia.nocookie.net/choujin-x/images/a/a3/Volume_14.jpg"
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_image(url):
    """Load image from URL and return as numpy array."""
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
        Cropped PIL Image
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

def calculate_parallelogram_vertices(x_center, y_center, width, height, skew_angle):
    """
    Calculate the 4 corner points of a parallelogram.
    
    Args:
        x_center, y_center: Center point of parallelogram
        width: Width of the parallelogram
        height: Height of the parallelogram
        skew_angle: Skew angle in degrees (positive = right-leaning)
    
    Returns:
        numpy array of shape (4, 2) with vertices in order:
        [bottom_left, bottom_right, top_right, top_left]
    """
    half_w = width / 2
    half_h = height / 2
    skew_offset = half_h * np.tan(np.radians(skew_angle))
    
    vertices = np.array([
        [x_center - half_w - skew_offset, y_center - half_h],  # Bottom Left
        [x_center + half_w - skew_offset, y_center - half_h],  # Bottom Right
        [x_center + half_w + skew_offset, y_center + half_h],  # Top Right
        [x_center - half_w + skew_offset, y_center + half_h]   # Top Left
    ])
    
    return vertices

# ============================================================================
# MAIN RENDERING
# ============================================================================

# Layout parameters
num_items = len(schedule)
cols = 2
content_rows = (num_items + cols - 1) // cols  # Rows for schedule items (excluding title)
title_row_height = 3.0  # Dedicated height for title row
vertical_padding = 1  # Significant padding between content rows

# Dynamic figure height: title row + content rows
fig_width = 16
fig_height = title_row_height + (content_rows * 5)  # Title row + content rows
bottom_margin = 1.0  # Bottom margin

# Create figure with dynamic height
fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))
fig.patch.set_facecolor('#1a1a1a')
ax.set_facecolor('#1a1a1a')
ax.set_xlim(0, fig_width)
ax.set_ylim(0, fig_height)
ax.axis('off')

# Title in its own dedicated row (row 0)
title_y = fig_height - title_row_height / 2
ax.text(fig_width / 2, title_y, "Choujin X Book Club Schedule",
        ha='center', va='center', fontsize=42, fontweight='bold',
        color='white', fontfamily='Courier New',
        path_effects=[withStroke(linewidth=3, foreground='#1a1a1a')])

# Grid spacing with significant vertical padding
cell_width = fig_width / cols
# Calculate cell height for content rows (excluding title row)
total_content_height = fig_height - title_row_height - bottom_margin
cell_height = (total_content_height - (content_rows - 1) * vertical_padding) / content_rows
start_y = fig_height - title_row_height  # Start content below title row

# Parallelogram frame parameters
frame_width = 2.8
frame_height = 3.5
skew_angle = 15  # degrees
frame_spacing = 0.5  # Space between frames in a row

for idx, (date, vols) in enumerate(schedule):
    row = idx // cols
    col = idx % cols
    
    # Calculate cell center with vertical padding between rows
    cell_x = (col + 0.5) * cell_width
    # Account for vertical padding: each row after the first adds padding
    y_offset = row * (cell_height + vertical_padding)
    cell_y = start_y - y_offset - cell_height / 2
    
    # Date text
    ax.text(cell_x, cell_y + frame_height / 2 + 0.4, date,
            ha='center', va='bottom', fontsize=18, fontweight='bold',
            color='white', fontfamily='Courier New',
            path_effects=[withStroke(linewidth=2, foreground='#1a1a1a')])
    
    # Volume numbers text
    if len(vols) == 1:
        vol_text = f"Volume {vols[0]}"
    elif len(vols) == 2:
        vol_text = f"Volumes {vols[0]} & {vols[1]}"
    else:
        vol_text = f"Volumes {', '.join(map(str, vols[:-1]))} & {vols[-1]}"
    ax.text(cell_x, cell_y + frame_height / 2 + 0.15, vol_text,
            ha='center', va='bottom', fontsize=14,
            color='white', fontfamily='sans-serif',
            path_effects=[withStroke(linewidth=2, foreground='#1a1a1a')])
    
    # Calculate scale factor to fit n volumes in the same width as 2 volumes
    # Total width for 2 volumes: 2 * frame_width + frame_spacing
    reference_width = 2 * frame_width + frame_spacing
    num_vols = len(vols)
    
    # For n volumes: n * scaled_width + (n-1) * scaled_spacing = reference_width
    # Scale factor: s = reference_width / (n * frame_width + (n-1) * frame_spacing)
    # But cap at 1.0 so n=1 doesn't scale up (stays same size as n=2)
    if num_vols > 0:
        total_unscaled_width = num_vols * frame_width + (num_vols - 1) * frame_spacing
        scale_factor = reference_width / total_unscaled_width if total_unscaled_width > 0 else 1.0
        # Cap scale factor at 1.0 to prevent scaling up (n=1 should be same size as n=2)
        scale_factor = min(scale_factor, 1.0)
    else:
        scale_factor = 1.0
    
    # Scaled dimensions (scale both width and height to maintain aspect ratio)
    scaled_frame_width = frame_width * scale_factor
    scaled_frame_height = frame_height * scale_factor
    scaled_frame_spacing = frame_spacing * scale_factor
    
    # Draw frames for each volume
    for j, vol in enumerate(vols):
        # Position frames side by side, centered
        # Calculate total width of all volumes
        total_width = num_vols * scaled_frame_width + (num_vols - 1) * scaled_frame_spacing
        # Start from left edge of centered group
        start_x = cell_x - total_width / 2
        # Position this volume within the group
        x_center = start_x + j * (scaled_frame_width + scaled_frame_spacing) + scaled_frame_width / 2
        y_center = cell_y
        
        # Calculate parallelogram vertices with scaled dimensions
        vertices = calculate_parallelogram_vertices(
            x_center, y_center, scaled_frame_width, scaled_frame_height, skew_angle
        )
        
        # Create clipping path
        clip_path = Path(vertices)
        
        # Draw drop shadow (offset parallelogram behind main frame)
        shadow_offset = 0.15
        shadow_vertices = vertices + np.array([shadow_offset, -shadow_offset])
        shadow = Polygon(shadow_vertices, closed=True,
                        facecolor='black', edgecolor='none',
                        alpha=0.4, zorder=1)
        ax.add_patch(shadow)
        
        # Draw main frame border (thick white stroke)
        frame = Polygon(vertices, closed=True,
                       edgecolor='white', linewidth=4,
                       facecolor='none', zorder=4)
        ax.add_patch(frame)
        
        # Load and process image
        img_pil = load_image(cover_urls.get(vol, ""))
        
        if img_pil is not None:
            # Apply center-crop-zoom to focus on character art (reduced zoom now)
            img_cropped = center_crop_zoom(img_pil, ZOOM_FACTOR)
            img_array = np.array(img_cropped)
            
            # Get image dimensions and aspect ratio
            img_height, img_width = img_array.shape[:2]
            img_aspect = img_width / img_height
            
            # Calculate the bounding box of the parallelogram
            min_x = vertices[:, 0].min()
            max_x = vertices[:, 0].max()
            min_y = vertices[:, 1].min()
            max_y = vertices[:, 1].max()
            
            para_width = max_x - min_x
            para_height = max_y - min_y
            
            # FIT-TO-WIDTH: Match image width to parallelogram width
            # Add small padding to ensure skewed corners are covered
            padding_factor = 1.05  # 5% padding to cover skew corners
            target_width = para_width * padding_factor
            
            # Calculate height based on aspect ratio
            target_height = target_width / img_aspect
            
            # Position the image horizontally centered, vertically offset
            # VERTICAL_OFFSET > 0 moves image higher (shows more of top, less of bottom)
            vertical_shift = target_height * VERTICAL_OFFSET
            extent = [
                x_center - target_width / 2,
                x_center + target_width / 2,
                y_center - target_height / 2 + vertical_shift,
                y_center + target_height / 2 + vertical_shift
            ]
            
            # Draw image as a rectangle (no distortion)
            im = ax.imshow(img_array, extent=extent, zorder=2, aspect='auto')
            
            # Clip to parallelogram shape (this creates the "window" effect)
            im.set_clip_path(clip_path, transform=ax.transData)
            
        else:
            # Fallback text if image fails
            ax.text(x_center, y_center, f"Vol {vol}\n(Image N/A)",
                   ha='center', va='center', fontsize=12,
                   color='white', fontfamily='sans-serif')

# Save figure
output_file = "choujin_x_schedule_fixed.png"
plt.savefig(output_file, dpi=200, bbox_inches='tight',
            facecolor=fig.get_facecolor(), edgecolor='none')
print(f"Saved as {output_file}")

# Open the image (Windows specific)
try:
    os.startfile(output_file)
except:
    pass

plt.close()
