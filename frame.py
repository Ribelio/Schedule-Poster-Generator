"""
Frame classes for rendering volume frames in different shapes.
"""

import numpy as np
from matplotlib.patches import Polygon
from matplotlib.path import Path


class Frame:
    """
    Base class for frame shapes.
    Provides common functionality for rendering frames with shadows and borders.
    """
    
    def __init__(self, width, height, spacing=0.5, border_color='white', shadow_alpha=0.4):
        """
        Initialize frame with common parameters.
        
        Args:
            width: Frame width
            height: Frame height
            spacing: Space between frames in a row
            border_color: Color of the frame border
            shadow_alpha: Alpha transparency for the shadow
        """
        self.width = width
        self.height = height
        self.spacing = spacing
        self.border_color = border_color
        self.shadow_alpha = shadow_alpha
        self.shadow_offset = 0.15
    
    def calculate_vertices(self, x_center, y_center, scaled_width, scaled_height):
        """
        Calculate vertices for the frame shape.
        Must be implemented by subclasses.
        
        Args:
            x_center, y_center: Center position of the frame
            scaled_width: Scaled width (may differ from self.width)
            scaled_height: Scaled height (may differ from self.height)
            
        Returns:
            numpy array of shape (n, 2) with vertices
        """
        raise NotImplementedError("Subclasses must implement calculate_vertices")
    
    def render(self, ax, x_center, y_center, scaled_width, scaled_height, zorder_base=1):
        """
        Render the frame with shadow and border.
        
        Args:
            ax: Matplotlib axes
            x_center, y_center: Center position of the frame
            scaled_width: Scaled width of the frame
            scaled_height: Scaled height of the frame
            zorder_base: Base z-order for rendering
            
        Returns:
            tuple: (vertices, clip_path) for use in image clipping
        """
        # Calculate vertices for this shape
        vertices = self.calculate_vertices(x_center, y_center, scaled_width, scaled_height)
        
        # Create clipping path
        clip_path = Path(vertices)
        
        # Draw drop shadow
        shadow_vertices = vertices + np.array([self.shadow_offset, -self.shadow_offset])
        shadow = Polygon(shadow_vertices, closed=True,
                        facecolor='black', edgecolor='none',
                        alpha=self.shadow_alpha, zorder=zorder_base)
        ax.add_patch(shadow)
        
        # Draw main frame border
        frame = Polygon(vertices, closed=True,
                       edgecolor=self.border_color, linewidth=4,
                       facecolor='none', zorder=zorder_base + 3)
        ax.add_patch(frame)
        
        return vertices, clip_path


class ParallelogramFrame(Frame):
    """
    Parallelogram-shaped frame with configurable skew angle.
    """
    
    def __init__(self, width, height, spacing=0.5, skew_angle=15, 
                 border_color='white', shadow_alpha=0.4):
        """
        Initialize parallelogram frame.
        
        Args:
            width: Frame width
            height: Frame height
            spacing: Space between frames in a row
            skew_angle: Skew angle in degrees (positive = right-leaning)
            border_color: Color of the frame border
            shadow_alpha: Alpha transparency for the shadow
        """
        super().__init__(width, height, spacing, border_color, shadow_alpha)
        self.skew_angle = skew_angle
    
    def calculate_vertices(self, x_center, y_center, scaled_width, scaled_height):
        """
        Calculate the 4 corner points of a parallelogram.
        
        Args:
            x_center, y_center: Center point of parallelogram
            scaled_width: Scaled width of the parallelogram
            scaled_height: Scaled height of the parallelogram
            
        Returns:
            numpy array of shape (4, 2) with vertices in order:
            [bottom_left, bottom_right, top_right, top_left]
        """
        half_w = scaled_width / 2
        half_h = scaled_height / 2
        skew_offset = half_h * np.tan(np.radians(self.skew_angle))
        
        vertices = np.array([
            [x_center - half_w - skew_offset, y_center - half_h],  # Bottom Left
            [x_center + half_w - skew_offset, y_center - half_h],  # Bottom Right
            [x_center + half_w + skew_offset, y_center + half_h],  # Top Right
            [x_center - half_w + skew_offset, y_center + half_h]   # Top Left
        ])
        
        return vertices


class RhombusFrame(Frame):
    """
    Rhombus-shaped frame (diamond shape) with equal sides.
    """
    
    def __init__(self, width, height, spacing=0.5, rotation_angle=0,
                 border_color='white', shadow_alpha=0.4):
        """
        Initialize rhombus frame.
        
        Args:
            width: Frame width (horizontal extent)
            height: Frame height (vertical extent)
            spacing: Space between frames in a row
            rotation_angle: Rotation angle in degrees (0 = diamond pointing up)
            border_color: Color of the frame border
            shadow_alpha: Alpha transparency for the shadow
        """
        super().__init__(width, height, spacing, border_color, shadow_alpha)
        self.rotation_angle = rotation_angle
    
    def calculate_vertices(self, x_center, y_center, scaled_width, scaled_height):
        """
        Calculate the 4 corner points of a rhombus (diamond shape).
        
        Args:
            x_center, y_center: Center point of rhombus
            scaled_width: Scaled width of the rhombus
            scaled_height: Scaled height of the rhombus
            
        Returns:
            numpy array of shape (4, 2) with vertices in order:
            [top, right, bottom, left]
        """
        half_w = scaled_width / 2
        half_h = scaled_height / 2
        
        # Create diamond shape vertices (before rotation)
        vertices = np.array([
            [x_center, y_center + half_h],      # Top
            [x_center + half_w, y_center],      # Right
            [x_center, y_center - half_h],      # Bottom
            [x_center - half_w, y_center]       # Left
        ])
        
        # Apply rotation if needed
        if self.rotation_angle != 0:
            angle_rad = np.radians(self.rotation_angle)
            cos_a = np.cos(angle_rad)
            sin_a = np.sin(angle_rad)
            
            # Rotation matrix
            rotation_matrix = np.array([
                [cos_a, -sin_a],
                [sin_a, cos_a]
            ])
            
            # Translate to origin, rotate, translate back
            center = np.array([x_center, y_center])
            vertices = (vertices - center) @ rotation_matrix.T + center
        
        return vertices


def create_frame_from_preset(preset):
    """
    Factory function to create a Frame instance from a preset dictionary.
    
    Args:
        preset: Dictionary with frame configuration
        
    Returns:
        Frame instance
    """
    shape_type = preset.get('type', 'parallelogram')
    width = preset.get('width', 2.8)
    height = preset.get('height', 3.5)
    spacing = preset.get('spacing', 0.5)
    border_color = preset.get('border_color', 'white')
    shadow_alpha = preset.get('shadow_alpha', 0.4)
    
    if shape_type == 'parallelogram':
        skew_angle = preset.get('skew_angle', 15)
        return ParallelogramFrame(width, height, spacing, skew_angle, border_color, shadow_alpha)
    elif shape_type == 'rhombus':
        rotation_angle = preset.get('rotation_angle', 0)
        return RhombusFrame(width, height, spacing, rotation_angle, border_color, shadow_alpha)
    else:
        # Default to parallelogram if shape type not recognized
        skew_angle = preset.get('skew_angle', 15)
        return ParallelogramFrame(width, height, spacing, skew_angle, border_color, shadow_alpha)

