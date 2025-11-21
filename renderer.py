"""
Rendering logic for creating the schedule poster.
"""

import io
import matplotlib.pyplot as plt
from matplotlib.patheffects import withStroke
import numpy as np
import os

from config import config
from image_utils import load_image, center_crop_zoom
from frame import create_frame_from_preset
from stagger import create_stagger_from_preset
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


def calculate_max_item_width(schedule, frame_width, frame_spacing):
    """
    Calculate the maximum width needed for any schedule item.
    Accounts for scaling: items with 1-2 volumes use full width (scale factor = 1.0),
    while items with 3+ volumes are scaled down to the reference width.
    
    Args:
        schedule: List of (date, volumes) tuples
        frame_width: Width of a single frame
        frame_spacing: Spacing between frames
        
    Returns:
        Maximum width needed for the widest item
    """
    reference_width = 2 * frame_width + frame_spacing
    max_item_width = 0
    
    for date, vols in schedule:
        num_vols = len(vols)
        if num_vols > 0:
            if num_vols <= 2:
                # Items with 1-2 volumes don't get scaled (scale factor capped at 1.0)
                # Use their actual width
                item_width = num_vols * frame_width + (num_vols - 1) * frame_spacing
            else:
                # Items with 3+ volumes get scaled down to reference width
                item_width = reference_width
            
            max_item_width = max(max_item_width, item_width)
    
    return max_item_width


def calculate_layout_dimensions(schedule, config):
    """
    Calculate layout dimensions based on schedule and configuration.
    
    Args:
        schedule: List of (date, volumes) tuples
        config: PosterConfig instance
        
    Returns:
        Tuple of (fig_width, fig_height, cell_width, cell_height, min_cell_width, content_rows)
    """
    frame_width = config.shape_preset['width']
    frame_spacing = config.shape_preset['spacing']
    
    num_items = len(schedule)
    content_rows = (num_items + config.cols - 1) // config.cols
    
    # Calculate maximum item width
    max_item_width = calculate_max_item_width(schedule, frame_width, frame_spacing)
    min_cell_width = max_item_width + 2 * config.horizontal_padding
    
    # Calculate figure width
    fig_width = config.cols * min_cell_width + (config.cols - 1) * config.column_spacing
    
    # Calculate figure height
    fig_height = config.title_row_height + (content_rows * 5)  # Title row + content rows
    
    # Calculate cell dimensions
    cell_width = min_cell_width
    total_content_height = fig_height - config.title_row_height - config.bottom_margin
    cell_height = (total_content_height - (content_rows - 1) * config.vertical_padding) / content_rows
    
    return fig_width, fig_height, cell_width, cell_height, min_cell_width, content_rows


def render_volume_image(ax, vol, vertices, clip_path, x_center, y_center, config, frame_instance):
    """Render the volume cover image within the frame."""
    from config import cover_urls
    
    # Load and process image (with volume number for caching)
    img_pil = load_image(cover_urls.get(vol, ""), volume=vol)
    
    if img_pil is not None:
        # Apply center-crop-zoom to focus on character art
        img_cropped = center_crop_zoom(img_pil, config.zoom_factor)
        img_array = np.array(img_cropped)
        
        # Get image dimensions and aspect ratio
        img_height, img_width = img_array.shape[:2]
        img_aspect = img_width / img_height
        
        # Calculate the bounding box using Frame method
        frame_width, frame_height = frame_instance.get_bounding_box(vertices)
        
        # FIT-TO-WIDTH: Match image width to frame width
        # Add small padding to ensure skewed corners are covered
        padding_factor = 1.05  # 5% padding to cover skew corners
        target_width = frame_width * padding_factor
        
        # Calculate height based on aspect ratio
        target_height = target_width / img_aspect
        
        # Position the image horizontally centered, vertically offset
        vertical_shift = target_height * config.vertical_offset
        extent = [
            x_center - target_width / 2,
            x_center + target_width / 2,
            y_center - target_height / 2 + vertical_shift,
            y_center + target_height / 2 + vertical_shift
        ]
        
        # Draw image as a rectangle (no distortion)
        im = ax.imshow(img_array, extent=extent, zorder=2, aspect='auto')
        
        # Clip to frame shape (this creates the "window" effect)
        im.set_clip_path(clip_path, transform=ax.transData)
    else:
        # Fallback text if image fails
        ax.text(x_center, y_center, f"Vol {vol}\n(Image N/A)",
               ha='center', va='center', fontsize=12,
               color=config.text_color, fontfamily='sans-serif')


def render_background_lineart(ax, fig_width, fig_height, config):
    """
    Render background line art image behind all other elements.
    Image is scaled to fit width while preserving aspect ratio.
    """
    if not config.background_lineart_enabled:
        return
    
    # Check if file exists
    if not os.path.exists(config.background_lineart_path):
        print(f"Warning: Background line art not found at {config.background_lineart_path}")
        return
    
    try:
        # Load the image
        img = PILImage.open(config.background_lineart_path)
        
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
                 alpha=config.background_lineart_alpha, interpolation='bilinear')
        
    except Exception as e:
        print(f"Warning: Failed to load background line art: {e}")


def render_schedule_item(ax, date, vols, cell_x, cell_y, frame_instance, stagger_strategy, config):
    """
    Render a single schedule item with date, volumes, and frames.
    
    Args:
        ax: Matplotlib axes
        date: Date string
        vols: List of volume numbers
        cell_x, cell_y: Cell center position
        frame_instance: Frame instance (from create_frame_from_preset)
        stagger_strategy: StaggerStrategy instance for vertical positioning
        config: PosterConfig instance
    """
    # Extract shape parameters from frame instance
    frame_width = frame_instance.width
    frame_height = frame_instance.height
    frame_spacing = frame_instance.spacing
    
    # Date text
    ax.text(cell_x, cell_y + frame_height / 2 + 0.4, date,
            ha='center', va='bottom', fontsize=config.date_fontsize, fontweight='bold',
            color=config.text_color, fontfamily=config.title_fontfamily,
            path_effects=[withStroke(linewidth=2, foreground=config.background_color)])
    
    # Volume numbers text
    vol_text = format_volume_text(vols)
    ax.text(cell_x, cell_y + frame_height / 2 + 0.15, vol_text,
            ha='center', va='bottom', fontsize=config.volume_fontsize,
            color=config.text_color, fontfamily='sans-serif',
            path_effects=[withStroke(linewidth=2, foreground=config.background_color)])
    
    # Calculate scale factor for volumes
    num_vols = len(vols)
    scale_factor = calculate_scale_factor(num_vols, frame_width, frame_spacing)
    
    # Scaled dimensions (scale both width and height to maintain aspect ratio)
    scaled_frame_width = frame_width * scale_factor
    scaled_frame_height = frame_height * scale_factor
    
    # Calculate spacing: evenly distribute available space among gaps
    # Reference width for 2 frames: 2 * frame_width + frame_spacing
    reference_width = 2 * frame_width + frame_spacing
    total_scaled_frames_width = num_vols * scaled_frame_width
    num_gaps = num_vols - 1
    
    if num_gaps > 0:
        # Calculate spacing to evenly distribute remaining space
        available_space_for_gaps = reference_width - total_scaled_frames_width
        scaled_frame_spacing = available_space_for_gaps / num_gaps
    else:
        scaled_frame_spacing = 0
    
    # Draw frames for each volume
    for j, vol in enumerate(vols):
        # Position frames side by side, centered
        total_width = num_vols * scaled_frame_width + (num_vols - 1) * scaled_frame_spacing
        start_x = cell_x - total_width / 2
        x_center = start_x + j * (scaled_frame_width + scaled_frame_spacing) + scaled_frame_width / 2
        
        # Apply stagger strategy to calculate vertical offset
        y_offset = stagger_strategy.calculate_offset(j, num_vols)
        y_center = cell_y + y_offset
        
        # Render frame using Frame class
        vertices, clip_path = frame_instance.render(
            ax, x_center, y_center, scaled_frame_width, scaled_frame_height
        )
        
        # Render image
        render_volume_image(ax, vol, vertices, clip_path, x_center, y_center, config, frame_instance)


def render_poster_to_buffer(poster_config, cover_data, schedule, format='png'):
    """
    Render the poster to an in-memory buffer (BytesIO) for live preview.
    
    Args:
        poster_config: PosterConfig instance
        cover_data: Dictionary mapping volume numbers to cover URLs
        schedule: List of (date, volumes) tuples
        format: Output format ('png' or 'svg'), defaults to 'png'
        
    Returns:
        BytesIO object containing the rendered image
    """
    # Temporarily update cover_urls for rendering
    from config import cover_urls
    original_cover_urls = cover_urls.copy()
    cover_urls.clear()
    cover_urls.update(cover_data)
    
    try:
        # Create frame instance from preset
        frame_instance = create_frame_from_preset(poster_config.shape_preset)
        
        # Create stagger strategy from preset
        stagger_strategy = create_stagger_from_preset(poster_config.stagger_preset)
        
        # Calculate layout dimensions
        fig_width, fig_height, cell_width, cell_height, min_cell_width, content_rows = \
            calculate_layout_dimensions(schedule, poster_config)
        
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))
        fig.patch.set_facecolor(poster_config.background_color)
        ax.set_facecolor(poster_config.background_color)
        ax.set_xlim(0, fig_width)
        ax.set_ylim(0, fig_height)
        ax.axis('off')
        
        # Render background line art first (behind everything, zorder=0)
        render_background_lineart(ax, fig_width, fig_height, poster_config)
        
        # Title
        title_y = fig_height - poster_config.title_row_height / 2
        ax.text(fig_width / 2, title_y, poster_config.title_text,
                ha='center', va='center', fontsize=poster_config.title_fontsize, fontweight=poster_config.title_fontweight,
                color=poster_config.title_color, fontfamily=poster_config.title_fontfamily,
                path_effects=[withStroke(linewidth=3, foreground=poster_config.background_color)])
        
        # Calculate starting position
        start_y = fig_height - poster_config.title_row_height
        
        # Render schedule items
        for idx, (date, vols) in enumerate(schedule):
            row = idx // poster_config.cols
            col = idx % poster_config.cols
            
            # Calculate cell position
            cell_x = col * (cell_width + poster_config.column_spacing) + cell_width / 2
            y_offset = row * (cell_height + poster_config.vertical_padding)
            cell_y = start_y - y_offset - cell_height / 2
            
            # Render the schedule item using frame instance and stagger strategy
            render_schedule_item(ax, date, vols, cell_x, cell_y, frame_instance, stagger_strategy, poster_config)
        
        # Configure SVG settings for Figma compatibility if needed
        if format.lower() == 'svg':
            # Critical: Set fonttype to 'none' so text remains editable in Figma/Illustrator
            # Without this, text gets converted to paths and becomes uneditable
            plt.rcParams['svg.fonttype'] = 'none'
        
        # Save to BytesIO buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format=format, dpi=poster_config.dpi, bbox_inches='tight',
                    facecolor=fig.get_facecolor(), edgecolor='none')
        buffer.seek(0)
        
        plt.close()
        
        return buffer
    finally:
        # Restore original cover_urls
        cover_urls.clear()
        cover_urls.update(original_cover_urls)


def create_poster(poster_config=None, output_path=None, format=None):
    """
    Main function to create and save the schedule poster to disk.
    Wrapper around render_poster_to_buffer that saves to file.
    
    Args:
        poster_config: PosterConfig instance (uses default if None)
        output_path: Optional custom output path (uses default if None)
        format: Optional format ('png' or 'svg'), auto-detected from extension if None
    
    Returns:
        Path to saved file
    """
    from config import schedule, cover_urls, config as default_config
    from manga_fetcher import MangaDexFetcher
    
    # Use provided config or default
    if poster_config is None:
        poster_config = default_config
    
    # Extract all unique volume numbers from schedule
    unique_volumes = set()
    for _, vols in schedule:
        unique_volumes.update(vols)
    
    # Fetch covers from MangaDex API
    print(f"\nFetching covers for {poster_config.manga_title}...")
    fetcher = MangaDexFetcher()
    mangadex_covers = fetcher.fetch_covers(poster_config.manga_title, unique_volumes)
    
    # Merge MangaDex results with manual overrides (manual takes precedence)
    merged_covers = {**mangadex_covers, **cover_urls}
    
    print(f"Loaded {len(merged_covers)} cover URL(s)\n")
    
    # Determine output path and format
    if output_path is None:
        os.makedirs(poster_config.output_dir, exist_ok=True)
        if format == 'svg':
            filename = poster_config.output_filename.replace('.png', '.svg')
        else:
            filename = poster_config.output_filename
        output_path = os.path.join(poster_config.output_dir, filename)
    
    # Auto-detect format from extension if not specified
    if format is None:
        if output_path.lower().endswith('.svg'):
            format = 'svg'
        else:
            format = 'png'
    
    # Render to buffer
    buffer = render_poster_to_buffer(poster_config, merged_covers, schedule, format=format)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Save to disk
    with open(output_path, 'wb') as f:
        f.write(buffer.getvalue())
    
    print(f"Saved as {output_path}")
    
    # Open the image (Windows specific)
    try:
        os.startfile(output_path)
    except:
        pass
    
    return output_path

