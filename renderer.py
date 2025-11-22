"""
Rendering logic for creating the schedule poster using PIL.
Pure Python + Pillow rendering pipeline.
"""

import io
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Optional

from config import config
from image_utils import load_image, center_crop_zoom
from frame import create_frame_from_preset
from stagger import create_stagger_from_preset


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
        scale_factor = min(scale_factor, 1.0)
    else:
        scale_factor = 1.0
    
    return scale_factor


def calculate_max_item_width(schedule, frame_width, frame_spacing):
    """
    Calculate the maximum width needed for any schedule item.
    """
    reference_width = 2 * frame_width + frame_spacing
    max_item_width = 0
    
    for date, vols in schedule:
        num_vols = len(vols)
        if num_vols > 0:
            if num_vols <= 2:
                item_width = num_vols * frame_width + (num_vols - 1) * frame_spacing
            else:
                item_width = reference_width
            max_item_width = max(max_item_width, item_width)
    
    return max_item_width


def calculate_layout_dimensions(schedule, config):
    """
    Calculate layout dimensions based on schedule and configuration.
    
    Returns:
        Tuple of (fig_width, fig_height, cell_width, cell_height, min_cell_width, content_rows)
    """
    frame_width = config.shape_preset['width']
    frame_spacing = config.shape_preset['spacing']
    
    num_items = len(schedule)
    content_rows = (num_items + config.cols - 1) // config.cols
    
    max_item_width = calculate_max_item_width(schedule, frame_width, frame_spacing)
    min_cell_width = max_item_width + 2 * config.horizontal_padding
    
    fig_width = config.cols * min_cell_width + (config.cols - 1) * config.column_spacing
    fig_height = config.title_row_height + (content_rows * 5)
    
    cell_width = min_cell_width
    total_content_height = fig_height - config.title_row_height - config.bottom_margin
    cell_height = (total_content_height - (content_rows - 1) * config.vertical_padding) / content_rows
    
    return fig_width, fig_height, cell_width, cell_height, min_cell_width, content_rows


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    elif len(hex_color) == 3:
        return tuple(int(c*2, 16) for c in hex_color)
    else:
        # Named colors
        color_map = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'gold': (255, 215, 0),
            'yellow': (255, 255, 0),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
        }
        return color_map.get(hex_color.lower(), (255, 255, 255))


def get_font(fontfamily: str, size: int, bold: bool = False):
    """
    Get a PIL font object, with fallback to default font.
    
    Args:
        fontfamily: Font family name
        size: Font size in points
        bold: Whether to use bold weight
        
    Returns:
        PIL ImageFont object
    """
    try:
        # Try to load the specified font
        font_paths = [
            f"C:/Windows/Fonts/{fontfamily}.ttf",
            f"C:/Windows/Fonts/{fontfamily}.otf",
            f"C:/Windows/Fonts/{fontfamily.replace(' ', '')}.ttf",
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except:
                    continue
        
        # Try system font lookup
        try:
            return ImageFont.truetype(fontfamily, size)
        except:
            pass
    except:
        pass
    
    # Fallback to default font
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()


def draw_text_with_outline(draw: ImageDraw.Draw, text: str, position: Tuple[float, float],
                          font: ImageFont.FreeTypeFont, fill_color: Tuple[int, int, int],
                          outline_color: Tuple[int, int, int], outline_width: int = 2):
    """
    Draw text with an outline (stroke) effect.
    
    Args:
        draw: PIL ImageDraw object
        text: Text to draw
        position: (x, y) position (center)
        font: PIL Font object
        fill_color: RGB fill color
        outline_color: RGB outline color
        outline_width: Width of outline in pixels
    """
    x, y = position
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Adjust position for center alignment
    x -= text_width / 2
    y -= text_height / 2
    
    # Draw outline by drawing text multiple times with offset
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx*dx + dy*dy <= outline_width*outline_width:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color + (255,))
    
    # Draw main text
    draw.text((x, y), text, font=font, fill=fill_color + (255,))


def render_text_layer(canvas_width: int, canvas_height: int, text: str,
                     x: float, y: float, fontsize: int, color: str,
                     fontfamily: str = 'sans-serif', bold: bool = False,
                     outline_color: Optional[str] = None, outline_width: int = 2,
                     pixels_per_unit: float = 1.0) -> Image.Image:
    """
    Render a text layer as a PIL Image.
    
    Args:
        canvas_width: Canvas width in pixels
        canvas_height: Canvas height in pixels
        text: Text to render
        x: X position in figure units
        y: Y position in figure units
        fontsize: Font size in points
        color: Text color (hex string)
        fontfamily: Font family name
        bold: Whether text is bold
        outline_color: Optional outline color (hex string)
        outline_width: Outline width in pixels
        pixels_per_unit: Conversion factor
        
    Returns:
        PIL Image with text rendered
    """
    img = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Convert position to pixels (flip Y for PIL coordinates)
    x_px = x * pixels_per_unit
    y_px = canvas_height - (y * pixels_per_unit)
    
    # Get font (fontsize is in points, convert to pixels: 1 point = 1/72 inch)
    # So: pixels = points * (DPI / 72)
    font_pixel_size = int(fontsize * pixels_per_unit / 72.0)
    font = get_font(fontfamily, font_pixel_size, bold)
    
    # Get colors
    fill_rgb = hex_to_rgb(color)
    outline_rgb = hex_to_rgb(outline_color) if outline_color else None
    
    if outline_rgb:
        draw_text_with_outline(draw, text, (x_px, y_px), font, fill_rgb, outline_rgb, outline_width)
    else:
        # Get text bbox for centering
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text((x_px - text_width/2, y_px - text_height/2), text, 
                 font=font, fill=fill_rgb + (255,))
    
    return img


def render_background_lineart_layer(canvas_width: int, canvas_height: int,
                                    config, pixels_per_unit: float) -> Optional[Image.Image]:
    """
    Render background line art as a layer.
    
    Returns:
        PIL Image with line art, or None if disabled/not found
    """
    if not config.background_lineart_enabled:
        return None
    
    if not os.path.exists(config.background_lineart_path):
        print(f"Warning: Background line art not found at {config.background_lineart_path}")
        return None
    
    try:
        img = Image.open(config.background_lineart_path)
        
        # Convert to RGBA
        if img.mode != 'RGBA':
            if img.mode == 'RGB':
                img = img.convert('RGBA')
            else:
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    rgb_img.paste(img, mask=img.split()[3])
                else:
                    rgb_img.paste(img)
                img = rgb_img.convert('RGBA')
        
        # Calculate target size (fit to width, preserve aspect)
        target_width = canvas_width
        aspect_ratio = img.width / img.height
        target_height = int(target_width / aspect_ratio)
        
        # Resize
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Ensure RGBA mode
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Apply alpha transparency factor
        # Multiply existing alpha channel by the factor
        alpha_factor = config.background_lineart_alpha
        r, g, b, a = img.split()
        
        # Multiply alpha channel by factor
        alpha_array = np.array(a, dtype=np.float32)
        alpha_array = (alpha_array * alpha_factor).astype(np.uint8)
        new_alpha = Image.fromarray(alpha_array, mode='L')
        
        # Recombine with new alpha
        img = Image.merge('RGBA', (r, g, b, new_alpha))
        
        # Center on canvas
        canvas_img = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        y_offset = (canvas_height - target_height) // 2
        canvas_img.paste(img, (0, y_offset), img)
        
        return canvas_img
    except Exception as e:
        print(f"Warning: Failed to load background line art: {e}")
        return None


def render_volume_image_layer(canvas_width: int, canvas_height: int,
                              vol: int, vertices: np.ndarray,
                              x_center: float, y_center: float,
                              config, frame_instance,
                              pixels_per_unit: float, cover_data: dict) -> Optional[Image.Image]:
    """
    Render a volume cover image layer.
    
    Returns:
        PIL Image with the cover image, or None if image fails to load
    """
    # Load image
    img_pil = load_image(cover_data.get(vol, ""), volume=vol)
    
    if img_pil is None:
        return None
    
    # Apply center-crop-zoom
    img_cropped = center_crop_zoom(img_pil, config.zoom_factor)
    
    # Get bounding box
    frame_width, frame_height = frame_instance.get_bounding_box(vertices)
    
    # Calculate target size (fit to width with padding)
    padding_factor = 1.05
    target_width_px = int(frame_width * pixels_per_unit * padding_factor)
    aspect_ratio = img_cropped.width / img_cropped.height
    target_height_px = int(target_width_px / aspect_ratio)
    
    # Resize image
    img_resized = img_cropped.resize((target_width_px, target_height_px), 
                                     Image.Resampling.LANCZOS)
    
    # Calculate position
    vertical_shift_px = target_height_px * config.vertical_offset
    x_px = int(x_center * pixels_per_unit - target_width_px / 2)
    y_px = int(canvas_height - (y_center * pixels_per_unit) - target_height_px / 2 - vertical_shift_px)
    
    # Create canvas
    canvas_img = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
    canvas_img.paste(img_resized, (x_px, y_px), img_resized if img_resized.mode == 'RGBA' else None)
    
    return canvas_img




def composite_flat(canvas_width: int, canvas_height: int, layers: List[Image.Image]) -> Image.Image:
    """
    Composite multiple layers into a single flat image for preview.
    
    Args:
        canvas_width: Canvas width in pixels
        canvas_height: Canvas height in pixels
        layers: List of PIL Images to composite
        
    Returns:
        Composite PIL Image
    """
    result = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
    
    for layer in layers:
        if layer:
            result = Image.alpha_composite(result, layer)
    
    return result


def render_poster_to_buffer(poster_config, cover_data, schedule, format='png'):
    """
    Render the poster to an in-memory buffer (BytesIO) for live preview.
    
    Args:
        poster_config: PosterConfig instance
        cover_data: Dictionary mapping volume numbers to cover URLs
        schedule: List of (date, volumes) tuples
        format: Output format ('png'), defaults to 'png'
        
    Returns:
        BytesIO object containing the rendered image
    """
    # Temporarily update cover_urls for rendering
    from config import cover_urls
    original_cover_urls = cover_urls.copy()
    cover_urls.clear()
    cover_urls.update(cover_data)
    
    try:
        # Calculate dimensions
        fig_width, fig_height, cell_width, cell_height, min_cell_width, content_rows = \
            calculate_layout_dimensions(schedule, poster_config)
        
        # Convert to pixels (figure units are in inches, so multiply by DPI)
        pixels_per_unit = poster_config.dpi  # 1 inch = DPI pixels
        canvas_width = int(fig_width * pixels_per_unit)
        canvas_height = int(fig_height * pixels_per_unit)
        
        # Create frame and stagger instances
        frame_instance = create_frame_from_preset(poster_config.shape_preset)
        stagger_strategy = create_stagger_from_preset(poster_config.stagger_preset)
        
        # Collect all layers
        layers = []
        
        # Background color
        bg_color = hex_to_rgb(poster_config.background_color)
        bg_img = Image.new('RGBA', (canvas_width, canvas_height), bg_color + (255,))
        layers.append(bg_img)
        
        # Background line art
        lineart_img = render_background_lineart_layer(canvas_width, canvas_height, 
                                                      poster_config, pixels_per_unit)
        if lineart_img:
            layers.append(lineart_img)
        
        # Title
        title_y = fig_height - poster_config.title_row_height / 2
        title_img = render_text_layer(
            canvas_width, canvas_height, poster_config.title_text,
            fig_width / 2, title_y, poster_config.title_fontsize,
            poster_config.title_color, poster_config.title_fontfamily,
            bold=(poster_config.title_fontweight == 'bold'),
            outline_color=poster_config.background_color, outline_width=3,
            pixels_per_unit=pixels_per_unit
        )
        layers.append(title_img)
        
        # Calculate starting position
        start_y = fig_height - poster_config.title_row_height
        
        # Render schedule items
        for idx, (date, vols) in enumerate(schedule):
            row = idx // poster_config.cols
            col = idx % poster_config.cols
            
            cell_x = col * (cell_width + poster_config.column_spacing) + cell_width / 2
            y_offset = row * (cell_height + poster_config.vertical_padding)
            cell_y = start_y - y_offset - cell_height / 2
            
            # Date text
            date_y = cell_y + frame_instance.height / 2 + 0.4
            date_img = render_text_layer(
                canvas_width, canvas_height, date,
                cell_x, date_y, poster_config.date_fontsize,
                poster_config.text_color, poster_config.title_fontfamily,
                bold=True, outline_color=poster_config.background_color,
                outline_width=2, pixels_per_unit=pixels_per_unit
            )
            layers.append(date_img)
            
            # Volume text
            vol_text = format_volume_text(vols)
            vol_y = cell_y + frame_instance.height / 2 + 0.15
            vol_img = render_text_layer(
                canvas_width, canvas_height, vol_text,
                cell_x, vol_y, poster_config.volume_fontsize,
                poster_config.text_color, 'sans-serif',
                outline_color=poster_config.background_color,
                outline_width=2, pixels_per_unit=pixels_per_unit
            )
            layers.append(vol_img)
            
            # Calculate scale factor
            num_vols = len(vols)
            scale_factor = calculate_scale_factor(num_vols, frame_instance.width, frame_instance.spacing)
            scaled_frame_width = frame_instance.width * scale_factor
            scaled_frame_height = frame_instance.height * scale_factor
            
            # Calculate spacing
            reference_width = 2 * frame_instance.width + frame_instance.spacing
            total_scaled_frames_width = num_vols * scaled_frame_width
            num_gaps = num_vols - 1
            if num_gaps > 0:
                available_space_for_gaps = reference_width - total_scaled_frames_width
                scaled_frame_spacing = available_space_for_gaps / num_gaps
            else:
                scaled_frame_spacing = 0
            
            # Render frames
            for j, vol in enumerate(vols):
                total_width = num_vols * scaled_frame_width + (num_vols - 1) * scaled_frame_spacing
                start_x = cell_x - total_width / 2
                x_center = start_x + j * (scaled_frame_width + scaled_frame_spacing) + scaled_frame_width / 2
                
                y_offset_stagger = stagger_strategy.calculate_offset(j, num_vols)
                y_center = cell_y + y_offset_stagger
                
                # Render frame
                shadow_img, border_img, vertices, mask_img = frame_instance.render_to_pil(
                    canvas_width, canvas_height, x_center, y_center,
                    scaled_frame_width, scaled_frame_height, pixels_per_unit
                )
                
                layers.append(shadow_img)
                layers.append(border_img)
                
                # Render cover image with mask
                cover_img = render_volume_image_layer(
                    canvas_width, canvas_height, vol, vertices,
                    x_center, y_center, poster_config, frame_instance,
                    pixels_per_unit, cover_data
                )
                
                if cover_img and mask_img:
                    # Apply mask to cover image (both are canvas-sized)
                    # Convert mask to grayscale (L mode) for compositing
                    # The mask has white where we want to show, black/transparent elsewhere
                    mask_l = mask_img.convert('L')
                    # Create masked cover: use mask to determine visibility
                    cover_masked = Image.new('RGBA', cover_img.size, (0, 0, 0, 0))
                    # Composite: where mask is white, show cover; where black, show transparent
                    cover_masked = Image.composite(cover_img, cover_masked, mask_l)
                    layers.append(cover_masked)
                elif cover_img:
                    layers.append(cover_img)
        
        # Composite all layers
        result = composite_flat(canvas_width, canvas_height, layers)
        
        # Convert to RGB if needed for PNG
        if result.mode == 'RGBA':
            rgb_result = Image.new('RGB', result.size, hex_to_rgb(poster_config.background_color))
            rgb_result.paste(result, mask=result.split()[3])
            result = rgb_result
        
        # Save to buffer
        buffer = io.BytesIO()
        result.save(buffer, format='PNG', dpi=(poster_config.dpi, poster_config.dpi))
        buffer.seek(0)
        
        return buffer
    finally:
        # Restore original cover_urls
        cover_urls.clear()
        cover_urls.update(original_cover_urls)


def create_poster(poster_config=None, output_path=None, format=None):
    """
    Main function to create and save the schedule poster to disk.
    
    Args:
        poster_config: PosterConfig instance (uses default if None)
        output_path: Optional custom output path (uses default if None)
        format: Optional format ('png'), auto-detected from extension if None
    
    Returns:
        Path to saved file
    """
    from config import schedule, cover_urls, config as default_config
    from manga_fetcher import MangaDexFetcher
    
    if poster_config is None:
        poster_config = default_config
    
    # Extract unique volumes
    unique_volumes = set()
    for _, vols in schedule:
        unique_volumes.update(vols)
    
    # Fetch covers
    print(f"\nFetching covers for {poster_config.manga_title}...")
    fetcher = MangaDexFetcher()
    mangadex_covers = fetcher.fetch_covers(poster_config.manga_title, unique_volumes)
    merged_covers = {**mangadex_covers, **cover_urls}
    print(f"Loaded {len(merged_covers)} cover URL(s)\n")
    
    # Determine output path and format
    if output_path is None:
        os.makedirs(poster_config.output_dir, exist_ok=True)
        filename = poster_config.output_filename
        output_path = os.path.join(poster_config.output_dir, filename)
    
    # Auto-detect format from extension (default to PNG)
    if format is None:
        format = 'png'
    
    # Render to PNG
    buffer = render_poster_to_buffer(poster_config, merged_covers, schedule, format='png')
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(buffer.getvalue())
    print(f"Saved as {output_path}")
    
    # Open the file (Windows specific)
    try:
        os.startfile(output_path)
    except:
        pass
    
    return output_path
