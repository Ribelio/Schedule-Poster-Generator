"""
Rendering logic for creating the schedule poster.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.path import Path
from matplotlib.patheffects import withStroke
import numpy as np
import os

from config import (
    schedule, cover_urls, ZOOM_FACTOR, VERTICAL_OFFSET,
    COLS, TITLE_ROW_HEIGHT, VERTICAL_PADDING, BOTTOM_MARGIN,
    HORIZONTAL_PADDING, COLUMN_SPACING, FRAME_WIDTH, FRAME_HEIGHT,
    SKEW_ANGLE, FRAME_SPACING, TITLE_TEXT, TITLE_FONTSIZE,
    TITLE_FONTWEIGHT, TITLE_COLOR, TITLE_FONTFAMILY, DATE_FONTSIZE,
    VOLUME_FONTSIZE, TEXT_COLOR, BACKGROUND_COLOR, FRAME_BORDER_COLOR,
    OUTPUT_DIR, OUTPUT_FILENAME, DPI,
    BACKGROUND_LINEART_ENABLED, BACKGROUND_LINEART_PATH, BACKGROUND_LINEART_ALPHA,
    BACKGROUND_LINEART_COLOR
)
from image_utils import load_image, center_crop_zoom
from geometry import calculate_parallelogram_vertices, calculate_layout_dimensions
from PIL import Image as PILImage


def format_volume_text(vols):
    """Format volume numbers into readable text."""
    if len(vols) == 1:
        return f"Volume {vols[0]}"
    elif len(vols) == 2:
        return f"Volumes {vols[0]} & {vols[1]}"
    else:
        return f"Volumes {', '.join(map(str, vols[:-1]))} & {vols[-1]}"


def calculate_scale_factor(num_vols, frame_width, frame_spacing):
    """
    Calculate scale factor to fit n volumes in the same width as 2 volumes.
    
    Args:
        num_vols: Number of volumes
        frame_width: Base frame width
        frame_spacing: Base frame spacing
        
    Returns:
        Scale factor (capped at 1.0)
    """
    reference_width = 2 * frame_width + frame_spacing
    
    if num_vols > 0:
        total_unscaled_width = num_vols * frame_width + (num_vols - 1) * frame_spacing
        scale_factor = reference_width / total_unscaled_width if total_unscaled_width > 0 else 1.0
        # Cap scale factor at 1.0 to prevent scaling up (n=1 should be same size as n=2)
        scale_factor = min(scale_factor, 1.0)
    else:
        scale_factor = 1.0
    
    return scale_factor


def render_volume_frame(ax, x_center, y_center, scaled_frame_width, scaled_frame_height,
                       skew_angle, zorder_base=1):
    """
    Render a single volume frame with shadow and border.
    
    Returns:
        vertices: numpy array of parallelogram vertices
        clip_path: Path object for clipping
    """
    # Calculate parallelogram vertices
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
                    alpha=0.4, zorder=zorder_base)
    ax.add_patch(shadow)
    
    # Draw main frame border (thick white stroke)
    frame = Polygon(vertices, closed=True,
                   edgecolor=FRAME_BORDER_COLOR, linewidth=4,
                   facecolor='none', zorder=zorder_base + 3)
    ax.add_patch(frame)
    
    return vertices, clip_path


def render_volume_image(ax, vol, vertices, clip_path, x_center, y_center):
    """Render the volume cover image within the frame."""
    # Load and process image
    img_pil = load_image(cover_urls.get(vol, ""))
    
    if img_pil is not None:
        # Apply center-crop-zoom to focus on character art
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
               color=TEXT_COLOR, fontfamily='sans-serif')


def render_background_lineart(ax, fig_width, fig_height):
    """
    Render background line art image behind all other elements.
    Image is scaled to fit width while preserving aspect ratio.
    """
    if not BACKGROUND_LINEART_ENABLED:
        return
    
    # Check if file exists
    if not os.path.exists(BACKGROUND_LINEART_PATH):
        print(f"Warning: Background line art not found at {BACKGROUND_LINEART_PATH}")
        return
    
    try:
        # Load the image
        img = PILImage.open(BACKGROUND_LINEART_PATH)
        
        # Convert to grayscale if needed, then to RGB
        if img.mode != 'RGB':
            if img.mode == 'RGBA':
                # Convert RGBA to RGB with white background
                rgb_img = PILImage.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = rgb_img
            else:
                img = img.convert('RGB')
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # For line art (typically black on white), invert if needed
        # The stencil PNG is typically white lines on black, so we may need to invert
        # or use it as-is depending on the source
        
        # Get image dimensions and aspect ratio
        img_height, img_width = img_array.shape[:2]
        img_aspect = img_width / img_height
        
        # Calculate dimensions to fit width while preserving aspect ratio
        target_width = fig_width
        target_height = target_width / img_aspect
        
        # Center vertically
        y_center = fig_height / 2
        x_center = fig_width / 2
        
        # Calculate extent (left, right, bottom, top)
        extent = [
            x_center - target_width / 2,
            x_center + target_width / 2,
            y_center - target_height / 2,
            y_center + target_height / 2
        ]
        
        # Render image with low transparency, behind everything (zorder=0)
        # Use cmap='gray' if it's a grayscale image, otherwise use the RGB array directly
        ax.imshow(img_array, extent=extent, zorder=0, aspect='auto', 
                 alpha=BACKGROUND_LINEART_ALPHA, interpolation='bilinear')
        
    except Exception as e:
        print(f"Warning: Failed to load background line art: {e}")


def render_schedule_item(ax, date, vols, cell_x, cell_y, frame_width, frame_height,
                         frame_spacing, skew_angle):
    """Render a single schedule item with date, volumes, and frames."""
    # Date text
    ax.text(cell_x, cell_y + frame_height / 2 + 0.4, date,
            ha='center', va='bottom', fontsize=DATE_FONTSIZE, fontweight='bold',
            color=TEXT_COLOR, fontfamily=TITLE_FONTFAMILY,
            path_effects=[withStroke(linewidth=2, foreground=BACKGROUND_COLOR)])
    
    # Volume numbers text
    vol_text = format_volume_text(vols)
    ax.text(cell_x, cell_y + frame_height / 2 + 0.15, vol_text,
            ha='center', va='bottom', fontsize=VOLUME_FONTSIZE,
            color=TEXT_COLOR, fontfamily='sans-serif',
            path_effects=[withStroke(linewidth=2, foreground=BACKGROUND_COLOR)])
    
    # Calculate scale factor for volumes
    num_vols = len(vols)
    scale_factor = calculate_scale_factor(num_vols, frame_width, frame_spacing)
    
    # Scaled dimensions (scale both width and height to maintain aspect ratio)
    scaled_frame_width = frame_width * scale_factor
    scaled_frame_height = frame_height * scale_factor
    scaled_frame_spacing = frame_spacing * scale_factor
    
    # Draw frames for each volume
    for j, vol in enumerate(vols):
        # Position frames side by side, centered
        total_width = num_vols * scaled_frame_width + (num_vols - 1) * scaled_frame_spacing
        start_x = cell_x - total_width / 2
        x_center = start_x + j * (scaled_frame_width + scaled_frame_spacing) + scaled_frame_width / 2
        y_center = cell_y
        
        # Render frame
        vertices, clip_path = render_volume_frame(
            ax, x_center, y_center, scaled_frame_width, scaled_frame_height, skew_angle
        )
        
        # Render image
        render_volume_image(ax, vol, vertices, clip_path, x_center, y_center)


def create_poster():
    """Main function to create and save the schedule poster."""
    # Calculate layout dimensions
    fig_width, fig_height, cell_width, cell_height, min_cell_width, content_rows = \
        calculate_layout_dimensions(
            schedule, COLS, FRAME_WIDTH, FRAME_SPACING,
            HORIZONTAL_PADDING, COLUMN_SPACING, TITLE_ROW_HEIGHT,
            VERTICAL_PADDING, BOTTOM_MARGIN
        )
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_xlim(0, fig_width)
    ax.set_ylim(0, fig_height)
    ax.axis('off')
    
    # Render background line art first (behind everything, zorder=0)
    render_background_lineart(ax, fig_width, fig_height)
    
    # Title
    title_y = fig_height - TITLE_ROW_HEIGHT / 2
    ax.text(fig_width / 2, title_y, TITLE_TEXT,
            ha='center', va='center', fontsize=TITLE_FONTSIZE, fontweight=TITLE_FONTWEIGHT,
            color=TITLE_COLOR, fontfamily=TITLE_FONTFAMILY,
            path_effects=[withStroke(linewidth=3, foreground=BACKGROUND_COLOR)])
    
    # Calculate starting position
    start_y = fig_height - TITLE_ROW_HEIGHT
    
    # Render schedule items
    for idx, (date, vols) in enumerate(schedule):
        row = idx // COLS
        col = idx % COLS
        
        # Calculate cell position
        cell_x = col * (cell_width + COLUMN_SPACING) + cell_width / 2
        y_offset = row * (cell_height + VERTICAL_PADDING)
        cell_y = start_y - y_offset - cell_height / 2
        
        # Render the schedule item
        render_schedule_item(ax, date, vols, cell_x, cell_y,
                           FRAME_WIDTH, FRAME_HEIGHT, FRAME_SPACING, SKEW_ANGLE)
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    
    # Save figure
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight',
                facecolor=fig.get_facecolor(), edgecolor='none')
    print(f"Saved as {output_path}")
    
    # Open the image (Windows specific)
    try:
        os.startfile(output_path)
    except:
        pass
    
    plt.close()
    
    return output_path

