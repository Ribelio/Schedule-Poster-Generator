"""
Geometry and calculation utilities for layout and shapes.
"""

import numpy as np



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

