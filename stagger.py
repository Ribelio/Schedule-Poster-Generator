"""
Stagger strategy classes for vertical positioning of frames within cells.
"""


class StaggerStrategy:
    """
    Base class for stagger strategies.
    Provides interface for calculating vertical offsets to stagger frame positions.
    """

    def __init__(self, offset=0.3):
        """
        Initialize stagger strategy.

        Args:
            offset: Vertical distance per step (in figure units)
        """
        self.offset = offset

    def calculate_offset(self, index, total_items):
        """
        Calculate the vertical offset for a frame at the given index.
        Must be implemented by subclasses.

        Args:
            index: Zero-based index of the frame (0, 1, 2, ...)
            total_items: Total number of frames in the group

        Returns:
            float: Vertical offset (positive = down, negative = up)
        """
        raise NotImplementedError("Subclasses must implement calculate_offset")


class AlternatingStagger(StaggerStrategy):
    """
    Alternating stagger strategy (zig-zag pattern).
    Even indices shift UP, odd indices shift DOWN.
    Offsets are centered to ensure uniform padding distribution.
    """

    def calculate_offset(self, index, total_items):
        """
        Calculate alternating offset: even indices up, odd indices down.
        Offsets are centered so the total sum is zero, ensuring uniform padding.

        Args:
            index: Zero-based index of the frame
            total_items: Total number of frames in the group

        Returns:
            float: Vertical offset (centered around 0)
        """
        # Calculate base alternating pattern
        if index % 2 == 0:
            # Even index: shift UP (negative offset)
            base_offset = -self.offset
        else:
            # Odd index: shift DOWN (positive offset)
            base_offset = self.offset

        # Center the offsets by subtracting the mean
        # For alternating pattern, mean depends on number of items
        if total_items % 2 == 0:
            # Even number of items: equal up/down, mean is 0
            mean_offset = 0.0
        else:
            # Odd number of items: one more "up" than "down"
            # Mean = -offset / total_items
            mean_offset = -self.offset / total_items

        # Return centered offset
        return base_offset - mean_offset


class StaircaseStagger(StaggerStrategy):
    """
    Staircase stagger strategy (continuous diagonal slide).
    Frames descend in steps, centered around the group center.
    """

    def calculate_offset(self, index, total_items):
        """
        Calculate staircase offset with centering.
        For n items, offsets are centered: [-(n-1)/2, ..., -1, 0, 1, ..., (n-1)/2]

        Examples:
        - 3 items: [-1, 0, 1]
        - 4 items: [-1.5, -0.5, 0.5, 1.5]
        - 5 items: [-2, -1, 0, 1, 2]

        Args:
            index: Zero-based index of the frame
            total_items: Total number of frames in the group

        Returns:
            float: Vertical offset (centered around 0)
        """
        # Calculate centered offset
        # For n items, we want: [-(n-1)/2, ..., -1, 0, 1, ..., (n-1)/2]
        center_index = (total_items - 1) / 2.0
        relative_position = index - center_index

        # Multiply by offset to get the actual shift
        return relative_position * self.offset


def create_stagger_from_preset(preset):
    """
    Factory function to create a StaggerStrategy instance from a preset dictionary.

    Args:
        preset: Dictionary with stagger configuration

    Returns:
        StaggerStrategy instance
    """
    stagger_type = preset.get("type", "none")
    offset = preset.get("offset", 0.3)

    if stagger_type == "alternating":
        return AlternatingStagger(offset)
    elif stagger_type == "staircase":
        return StaircaseStagger(offset)
    elif stagger_type == "none":
        # No stagger - return a strategy that always returns 0
        class NoStagger(StaggerStrategy):
            def calculate_offset(self, index, total_items):
                return 0.0

        return NoStagger(offset)
    else:
        # Default to no stagger if type not recognized
        class NoStagger(StaggerStrategy):
            def calculate_offset(self, index, total_items):
                return 0.0

        return NoStagger(offset)
