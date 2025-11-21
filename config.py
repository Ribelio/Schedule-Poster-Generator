"""
Configuration file for the Schedule Poster Generator.
Contains schedule data, cover URLs, and visual settings.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

# ============================================================================
# SCHEDULE DATA
# ============================================================================

# Manga title for MangaDex API lookup
MANGA_TITLE = "Choujin X"

# List of dates and volume pairs
schedule: List[Tuple[str, List[int]]] = [
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
cover_urls: Dict[int, str] = {
    # Manual overrides can be added here if needed
    # Example: 1: "https://example.com/volume1.jpg"
}

# ============================================================================
# CONFIGURATION DATACLASS
# ============================================================================

@dataclass
class PosterConfig:
    """Configuration dataclass for poster generation settings."""
    
    # Manga title
    manga_title: str = MANGA_TITLE
    
    # Image processing settings
    zoom_factor: float = 1.1  # Center-crop-zoom factor: Higher values = more zoom into center
    vertical_offset: float = -0.10  # Vertical offset for image positioning (positive = higher)
    
    # Layout settings
    cols: int = 3  # Number of columns in the grid
    title_row_height: float = 3.0  # Height reserved for title row
    vertical_padding: float = 1  # Padding between content rows
    bottom_margin: float = 1.0  # Bottom margin
    horizontal_padding: float = 0.5  # Horizontal padding on each side of cell
    column_spacing: float = 0.5  # Spacing between columns
    
    # Shape preset configuration
    # Each preset defines the frame shape and its parameters.
    # To add new shapes, create a new Frame subclass in frame.py
    # and update the create_frame_from_preset() factory function.
    shape_preset: Dict = None
    
    # Stagger strategy configuration
    # Controls vertical positioning of frames within a cell
    stagger_preset: Dict = None
    
    # Title settings
    title_fontsize: int = 42
    title_fontweight: str = 'bold'
    title_color: str = 'white'
    title_fontfamily: str = 'Courier New'
    
    # Text settings
    date_fontsize: int = 18
    volume_fontsize: int = 14
    text_color: str = 'white'
    
    # Color scheme
    background_color: str = '#1a1a1a'
    frame_border_color: str = 'white'
    
    # Background line art settings
    background_lineart_enabled: bool = True  # Set to False to disable background
    background_lineart_path: str = "output/images/background_lineart.png"
    background_lineart_alpha: float = 0.15  # Transparency (0.0 = fully transparent, 1.0 = opaque)
    background_lineart_color: str = 'white'  # Color for the line art (if using monochrome)
    
    # Output settings
    output_dir: str = "output/images"
    dpi: int = 200
    
    def __post_init__(self):
        """Initialize preset dictionaries if not provided."""
        if self.shape_preset is None:
            self.shape_preset = {
                'type': 'parallelogram',  # Shape type: 'parallelogram', 'rhombus', 'rectangle', 'hexagon', etc.
                'width': 1.5,            # Frame width
                'height': 2.5,            # Frame height
                'spacing': 0.0,           # Space between frames in a row
                'border_color': 'gold',  # Frame border color
                'shadow_alpha': 0.4,      # Shadow transparency (0.0-1.0)
                # Shape-specific parameters (add more as needed for different shapes)
                'skew_angle': -15,         # degrees (for parallelogram only)
                'rotation_angle': 0,      # degrees (for rhombus only, 0 = diamond pointing up)
            }
        
        if self.stagger_preset is None:
            self.stagger_preset = {
                'type': 'none',      # Stagger type: 'none', 'alternating', 'staircase'
                'offset': 0.1,       # Vertical distance per step (in figure units)
            }
    
    @property
    def title_text(self) -> str:
        """Generate title text from manga title."""
        return f"{self.manga_title} Book Club Schedule"
    
    @property
    def output_filename(self) -> str:
        """Generate output filename from manga title."""
        return f"{self.manga_title}_schedule.png"


# Create default config instance
config = PosterConfig()

