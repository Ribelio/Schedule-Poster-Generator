"""
Geometry and calculation utilities for layout and shapes.
"""

import numpy as np


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


def calculate_max_item_width(schedule, frame_width, frame_spacing):
    """
    Calculate the maximum width needed for any schedule item.
    
    Args:
        schedule: List of (date, volumes) tuples
        frame_width: Width of a single frame
        frame_spacing: Spacing between frames
        
    Returns:
        Maximum width needed for the widest item
    """
    max_item_width = 0
    for date, vols in schedule:
        num_vols = len(vols)
        if num_vols > 0:
            # Width needed: num_vols * frame_width + (num_vols - 1) * frame_spacing
            item_width = num_vols * frame_width + (num_vols - 1) * frame_spacing
            max_item_width = max(max_item_width, item_width)
    return max_item_width


def calculate_layout_dimensions(schedule, cols, frame_width, frame_spacing, 
                                horizontal_padding, column_spacing, 
                                title_row_height, vertical_padding, bottom_margin):
    """
    Calculate layout dimensions based on schedule and configuration.
    
    Returns:
        Tuple of (fig_width, fig_height, cell_width, cell_height, min_cell_width, content_rows)
    """
    num_items = len(schedule)
    content_rows = (num_items + cols - 1) // cols
    
    # Calculate maximum item width
    max_item_width = calculate_max_item_width(schedule, frame_width, frame_spacing)
    min_cell_width = max_item_width + 2 * horizontal_padding
    
    # Calculate figure width
    fig_width = cols * min_cell_width + (cols - 1) * column_spacing
    
    # Calculate figure height
    fig_height = title_row_height + (content_rows * 5)  # Title row + content rows
    
    # Calculate cell dimensions
    cell_width = min_cell_width
    total_content_height = fig_height - title_row_height - bottom_margin
    cell_height = (total_content_height - (content_rows - 1) * vertical_padding) / content_rows
    
    return fig_width, fig_height, cell_width, cell_height, min_cell_width, content_rows

