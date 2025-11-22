"""
Frame classes for rendering volume frames in different shapes.
"""

import numpy as np
from matplotlib.patches import Polygon
from matplotlib.path import Path
from PIL import Image, ImageDraw


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
    
    def get_bounding_box(self, vertices):
        """
        Calculate the bounding box of the frame vertices.
        
        Args:
            vertices: numpy array of shape (n, 2) with vertices
            
        Returns:
            tuple: (width, height) of the bounding box
        """
        min_x = vertices[:, 0].min()
        max_x = vertices[:, 0].max()
        min_y = vertices[:, 1].min()
        max_y = vertices[:, 1].max()
        
        width = max_x - min_x
        height = max_y - min_y
        
        return width, height
    
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
    
    def render_to_pil(self, canvas_width: int, canvas_height: int, 
                      x_center: float, y_center: float, 
                      scaled_width: float, scaled_height: float,
                      pixels_per_unit: float) -> tuple:
        """
        Render the frame to PIL images (shadow and border as separate layers).
        
        Args:
            canvas_width: Canvas width in pixels
            canvas_height: Canvas height in pixels
            x_center: X center position in figure units
            y_center: Y center position in figure units
            scaled_width: Scaled width in figure units
            scaled_height: Scaled height in figure units
            pixels_per_unit: Conversion factor from figure units to pixels
            
        Returns:
            tuple: (shadow_image, border_image, vertices, mask_image)
            - shadow_image: PIL Image with shadow (RGBA)
            - border_image: PIL Image with border (RGBA)
            - vertices: numpy array of vertices
            - mask_image: PIL Image with white mask shape (RGBA)
        """
        # Calculate vertices
        vertices = self.calculate_vertices(x_center, y_center, scaled_width, scaled_height)
        
        # Convert vertices to pixel coordinates
        # Note: PIL uses top-left origin, so we need to flip Y
        vertices_px = vertices.copy()
        vertices_px[:, 0] = vertices_px[:, 0] * pixels_per_unit
        vertices_px[:, 1] = canvas_height - (vertices_px[:, 1] * pixels_per_unit)  # Flip Y
        
        # Create shadow vertices
        shadow_offset_px = self.shadow_offset * pixels_per_unit
        shadow_vertices_px = vertices_px.copy()
        shadow_vertices_px[:, 0] += shadow_offset_px  # Shadow offset to the right
        shadow_vertices_px[:, 1] += shadow_offset_px  # Shadow offset down (in PIL: Y increases downward)
        
        # Create images
        shadow_img = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        border_img = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        mask_img = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        
        shadow_draw = ImageDraw.Draw(shadow_img)
        border_draw = ImageDraw.Draw(border_img)
        mask_draw = ImageDraw.Draw(mask_img)
        
        # Convert vertices to tuples for PIL
        shadow_points = [tuple(p) for p in shadow_vertices_px]
        border_points = [tuple(p) for p in vertices_px]
        mask_points = [tuple(p) for p in vertices_px]
        
        # Draw shadow
        shadow_alpha = int(255 * self.shadow_alpha)
        shadow_draw.polygon(shadow_points, fill=(0, 0, 0, shadow_alpha))
        
        # Draw border as outline only (thin stroke around the shape)
        # Border width is in points (1/72 inch), so convert to pixels
        # Original matplotlib used linewidth=4 (points)
        border_width_points = 4
        border_width = int(border_width_points * pixels_per_unit / 72.0)
        border_color_rgb = self._hex_to_rgb(self.border_color)
        
        # Draw outline by connecting vertices with lines
        # This creates a clean outline around the shape
        if len(border_points) >= 2:
            for i in range(len(border_points)):
                p1 = border_points[i]
                p2 = border_points[(i + 1) % len(border_points)]
                border_draw.line([p1, p2], fill=border_color_rgb + (255,), width=border_width)
        
        # Draw mask (white filled shape)
        mask_draw.polygon(mask_points, fill=(255, 255, 255, 255))
        
        return shadow_img, border_img, vertices, mask_img
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        elif len(hex_color) == 3:
            return tuple(int(c*2, 16) for c in hex_color)
        else:
            # Try to parse named colors
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


class RectangleFrame(Frame):
    """
    Rectangle-shaped frame.
    """
    
    def __init__(self, width, height, spacing=0.5, border_color='white', shadow_alpha=0.4):
        super().__init__(width, height, spacing, border_color, shadow_alpha)
    
    def calculate_vertices(self, x_center, y_center, scaled_width, scaled_height):
        """
        Calculate the 4 corner points of a rectangle.
        
        Args:
            x_center, y_center: Center point of rectangle
            scaled_width: Scaled width of the rectangle
            scaled_height: Scaled height of the rectangle
    
        Returns:
            numpy array of shape (4, 2) with vertices in order:
            [bottom_left, bottom_right, top_right, top_left]
        """
        return np.array([
            [x_center - scaled_width / 2, y_center - scaled_height / 2],  # Bottom Left
            [x_center + scaled_width / 2, y_center - scaled_height / 2],  # Bottom Right
            [x_center + scaled_width / 2, y_center + scaled_height / 2],  # Top Right
            [x_center - scaled_width / 2, y_center + scaled_height / 2]   # Top Left
        ])

class HexagonFrame(Frame):
    """
    Hexagon-shaped frame.
    """
    
    def __init__(self, width, height, spacing=0.5, border_color='white', shadow_alpha=0.4):
        super().__init__(width, height, spacing, border_color, shadow_alpha)
    
    def calculate_vertices(self, x_center, y_center, scaled_width, scaled_height):
        """
        Calculate the 6 corner points of a regular hexagon (point-top orientation).
        
        For a regular hexagon with points at top/bottom:
        - Top and bottom are single vertex points
        - Left and right sides have flat edges (two vertices each)
        - The width spans from leftmost to rightmost point
        - The height spans from top point to bottom point
        
        In a regular hexagon with point-top orientation:
        - The flat edges are at 60° angles from vertical
        - The horizontal distance from center to flat edge = height * tan(30°) = height / sqrt(3)
        - To fit within the given width, we use the minimum of (width/2) and (height/sqrt(3))
        
        Args:
            x_center, y_center: Center point of hexagon
            scaled_width: Scaled width of the hexagon (horizontal extent)
            scaled_height: Scaled height of the hexagon (vertical extent)
            
        Returns:
            numpy array of shape (6, 2) with vertices in counter-clockwise order:
            [top_point, top_right, bottom_right, bottom_point, bottom_left, top_left]
        """
        half_h = scaled_height / 2
        
        # For a regular hexagon, the flat edges are at 60° angles
        # The horizontal distance from center to flat edge = half_h * tan(30°) = half_h / sqrt(3)
        # Use the minimum of half_width and the calculated regular hexagon width
        sqrt3 = np.sqrt(3)
        regular_hex_half_w = half_h / sqrt3
        half_w = min(scaled_width / 2, regular_hex_half_w)
        
        # The vertical offset for the flat edge vertices
        # In a regular hexagon, the flat edges are at half the height
        flat_edge_y = half_h / 2
        
        return np.array([
            [x_center, y_center + half_h],                    # Top Point
            [x_center + half_w, y_center + flat_edge_y],      # Top Right
            [x_center + half_w, y_center - flat_edge_y],      # Bottom Right
            [x_center, y_center - half_h],                    # Bottom Point
            [x_center - half_w, y_center - flat_edge_y],      # Bottom Left
            [x_center - half_w, y_center + flat_edge_y]       # Top Left
        ])

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
    elif shape_type == 'rectangle':
        return RectangleFrame(width, height, spacing, border_color, shadow_alpha)
    elif shape_type == 'hexagon':
        return HexagonFrame(width, height, spacing, border_color, shadow_alpha)
    else:
        # Default to parallelogram if shape type not recognized
        skew_angle = preset.get('skew_angle', 15)
        return ParallelogramFrame(width, height, spacing, skew_angle, border_color, shadow_alpha)

