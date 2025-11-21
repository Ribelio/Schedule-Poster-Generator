"""
Configuration file for the Schedule Poster Generator.
Contains schedule data, cover URLs, and visual settings.
"""

# ============================================================================
# SCHEDULE DATA
# ============================================================================

# Manga title for MangaDex API lookup
MANGA_TITLE = "Choujin X"

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

# URLs for volume covers (manual overrides - will be merged with MangaDex results)
# Leave empty to use only MangaDex, or specify manual URLs for specific volumes
cover_urls = {
    # Manual overrides can be added here if needed
    # Example: 1: "https://example.com/volume1.jpg"
}

# ============================================================================
# VISUAL SETTINGS
# ============================================================================

# Image processing settings
ZOOM_FACTOR = 0.95  # Center-crop-zoom factor: Higher values = more zoom into center
VERTICAL_OFFSET = -0.1  # Vertical offset for image positioning (positive = higher)

# Layout settings
COLS = 3  # Number of columns in the grid
TITLE_ROW_HEIGHT = 3.0  # Height reserved for title row
VERTICAL_PADDING = 1  # Padding between content rows
BOTTOM_MARGIN = 1.0  # Bottom margin
HORIZONTAL_PADDING = 0.5  # Horizontal padding on each side of cell
COLUMN_SPACING = 0.5    # Spacing between columns

# ============================================================================
# SHAPE PRESETS
# ============================================================================

# Shape preset configuration
# Each preset defines the frame shape and its parameters.
# To add new shapes, create a new Frame subclass in frame.py
# and update the create_frame_from_preset() factory function.
SHAPE_PRESET = {
    'type': 'parallelogram',  # Shape type: 'parallelogram', 'rhombus', 'rectangle', 'hexagon', etc.
    'width': 2.8,            # Frame width
    'height': 3.5,            # Frame height
    'spacing': 0.5,           # Space between frames in a row
    'border_color': 'white',  # Frame border color
    'shadow_alpha': 0.4,      # Shadow transparency (0.0-1.0)
    # Shape-specific parameters (add more as needed for different shapes)
    'skew_angle': 15,         # degrees (for parallelogram only)
    'rotation_angle': 0,      # degrees (for rhombus only, 0 = diamond pointing up)
}

# Legacy frame parameters (kept for backward compatibility, derived from preset)
FRAME_WIDTH = SHAPE_PRESET['width']
FRAME_HEIGHT = SHAPE_PRESET['height']
FRAME_SPACING = SHAPE_PRESET['spacing']
SKEW_ANGLE = SHAPE_PRESET['skew_angle']

# ============================================================================
# STAGGER STRATEGY PRESETS
# ============================================================================

# Stagger strategy configuration
# Controls vertical positioning of frames within a cell
STAGGER_PRESET = {
    'type': 'staircase',      # Stagger type: 'none', 'alternating', 'staircase'
    'offset': 0.3,       # Vertical distance per step (in figure units)
}

# Title settings
TITLE_TEXT = f"{MANGA_TITLE} Book Club Schedule"
TITLE_FONTSIZE = 42
TITLE_FONTWEIGHT = 'bold'
TITLE_COLOR = 'white'
TITLE_FONTFAMILY = 'Courier New'

# Text settings
DATE_FONTSIZE = 18
VOLUME_FONTSIZE = 14
TEXT_COLOR = 'white'

# Color scheme
BACKGROUND_COLOR = '#1a1a1a'
FRAME_BORDER_COLOR = 'white'

# Background line art settings
BACKGROUND_LINEART_ENABLED = True  # Set to False to disable background
# Path to line art image (supports PNG, JPG formats)
BACKGROUND_LINEART_PATH = "output/images/background_lineart.png"
BACKGROUND_LINEART_ALPHA = 0.15  # Transparency (0.0 = fully transparent, 1.0 = opaque)
BACKGROUND_LINEART_COLOR = 'white'  # Color for the line art (if using monochrome)

# Output settings
OUTPUT_DIR = "output/images"
OUTPUT_FILENAME = f"{MANGA_TITLE}_schedule.png"
DPI = 200

