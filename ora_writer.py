"""
OpenRaster (.ora) file writer for creating layered image files compatible with GIMP/Krita.

An ORA file is a ZIP archive containing:
- mimetype: The MIME type "image/openraster"
- stack.xml: XML describing the layer hierarchy
- data/: Directory containing PNG files for each layer
"""

import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from typing import Optional, List
from PIL import Image


class OpenRasterWriter:
    """
    Writer for creating OpenRaster (.ora) files with layered structure.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize the OpenRaster writer.
        
        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
        """
        self.width = width
        self.height = height
        self.layers: List[dict] = []
        self.group_stack: List[ET.Element] = []
        self.root_stack = ET.Element('stack')
        self.root_stack.set('w', str(width))
        self.root_stack.set('h', str(height))
        self.current_stack = self.root_stack
        self.layer_counter = 0
        self.data_files: List[tuple] = []  # List of (filename, PIL Image) tuples
        
    def add_layer(self, image: Image.Image, name: str, x: int = 0, y: int = 0,
                  opacity: float = 1.0, composite_op: str = 'svg:src-over',
                  visible: bool = True) -> str:
        """
        Add a layer to the ORA file.
        
        Args:
            image: PIL Image object (will be converted to RGBA if needed)
            name: Layer name
            x: X position of the layer
            y: Y position of the layer
            opacity: Opacity (0.0 to 1.0)
            composite_op: Composite operation (e.g., 'svg:src-over', 'svg:dst-in')
            visible: Whether the layer is visible
            
        Returns:
            Layer filename (e.g., 'data/layer_0.png')
        """
        # Ensure image is RGBA
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Generate layer filename
        layer_filename = f"data/layer_{self.layer_counter}.png"
        self.layer_counter += 1
        
        # Store image for later writing
        self.data_files.append((layer_filename, image))
        
        # Create layer element
        layer_elem = ET.Element('layer')
        layer_elem.set('name', name)
        layer_elem.set('src', layer_filename)
        layer_elem.set('x', str(int(x)))
        layer_elem.set('y', str(int(y)))
        layer_elem.set('opacity', str(opacity))
        layer_elem.set('composite-op', composite_op)
        layer_elem.set('visibility', 'visible' if visible else 'hidden')
        
        # Add to current stack
        self.current_stack.append(layer_elem)
        
        return layer_filename
    
    def start_group(self, name: str, opacity: float = 1.0, 
                    composite_op: str = 'svg:src-over', 
                    isolation: bool = False,
                    visible: bool = True):
        """
        Start a new layer group (stack).
        
        Args:
            name: Group name
            opacity: Group opacity (0.0 to 1.0)
            composite_op: Composite operation for the group
            isolation: Whether to enable isolation (for masking)
            visible: Whether the group is visible
        """
        # Create new stack element
        stack_elem = ET.Element('stack')
        stack_elem.set('name', name)
        stack_elem.set('opacity', str(opacity))
        stack_elem.set('composite-op', composite_op)
        stack_elem.set('visibility', 'visible' if visible else 'hidden')
        
        if isolation:
            stack_elem.set('isolation', 'true')
        
        # Add to current stack and push to stack
        self.current_stack.append(stack_elem)
        self.group_stack.append(self.current_stack)
        self.current_stack = stack_elem
    
    def end_group(self):
        """
        End the current layer group.
        """
        if self.group_stack:
            self.current_stack = self.group_stack.pop()
        else:
            raise ValueError("No group to end")
    
    def add_mask_group(self, name: str, mask_image: Image.Image, 
                       content_image: Image.Image, 
                       mask_x: int = 0, mask_y: int = 0,
                       content_x: int = 0, content_y: int = 0,
                       opacity: float = 1.0, visible: bool = True):
        """
        Add a mask group using the "Destination In" composite operation.
        
        This creates a group with isolation enabled, containing:
        1. The content image (bottom layer)
        2. The mask image (top layer) with composite-op="svg:dst-in"
        
        Args:
            name: Group name
            mask_image: PIL Image for the mask (white = visible, black = hidden)
            content_image: PIL Image for the content
            mask_x: X position of mask
            mask_y: Y position of mask
            content_x: X position of content
            content_y: Y position of content
            opacity: Group opacity
            visible: Whether the group is visible
        """
        self.start_group(name, opacity=opacity, isolation=True, visible=visible)
        
        # Add content image first (bottom layer)
        self.add_layer(content_image, f"{name} - Content", 
                      x=content_x, y=content_y, 
                      opacity=1.0, composite_op='svg:src-over')
        
        # Add mask image on top with dst-in composite operation
        self.add_layer(mask_image, f"{name} - Mask", 
                      x=mask_x, y=mask_y,
                      opacity=1.0, composite_op='svg:dst-in')
        
        self.end_group()
    
    def save(self, filepath: str):
        """
        Save the ORA file to disk.
        
        Args:
            filepath: Output file path
        """
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Write mimetype (must be first, uncompressed)
            zf.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
            
            # Write all layer images
            for filename, image in self.data_files:
                img_buffer = BytesIO()
                image.save(img_buffer, format='PNG')
                zf.writestr(filename, img_buffer.getvalue())
            
            # Write stack.xml
            tree = ET.ElementTree(self.root_stack)
            xml_buffer = BytesIO()
            tree.write(xml_buffer, encoding='utf-8', xml_declaration=True)
            zf.writestr('stack.xml', xml_buffer.getvalue())
    
    def save_to_buffer(self) -> BytesIO:
        """
        Save the ORA file to an in-memory buffer.
        
        Returns:
            BytesIO object containing the ORA file
        """
        buffer = BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Write mimetype (must be first, uncompressed)
            zf.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
            
            # Write all layer images
            for filename, image in self.data_files:
                img_buffer = BytesIO()
                image.save(img_buffer, format='PNG')
                zf.writestr(filename, img_buffer.getvalue())
            
            # Write stack.xml
            tree = ET.ElementTree(self.root_stack)
            xml_buffer = BytesIO()
            tree.write(xml_buffer, encoding='utf-8', xml_declaration=True)
            zf.writestr('stack.xml', xml_buffer.getvalue())
        
        buffer.seek(0)
        return buffer

