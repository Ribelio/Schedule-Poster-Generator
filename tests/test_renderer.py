import pytest
from renderer import format_volume_text, calculate_scale_factor, calculate_max_item_width

def test_format_volume_text():
    assert format_volume_text([1]) == "Volume 1"
    assert format_volume_text([1, 2]) == "Volumes 1 & 2"
    assert format_volume_text([1, 2, 3]) == "Volumes 1, 2 & 3"
    assert format_volume_text([5, 8, 10, 12]) == "Volumes 5, 8, 10 & 12"

def test_calculate_scale_factor():
    frame_width = 100
    frame_spacing = 10
    
    # Case 1: 1 volume (should be cap at 1.0)
    assert calculate_scale_factor(1, frame_width, frame_spacing) == 1.0
    
    # Case 2: 2 volumes (reference width, should be 1.0)
    assert calculate_scale_factor(2, frame_width, frame_spacing) == 1.0
    
    # Case 3: 3 volumes (should be scaled down)
    # Reference width = 2*100 + 10 = 210
    # Unscaled 3 width = 3*100 + 2*10 = 320
    # Expected scale = 210 / 320 = 0.65625
    expected = 210 / 320
    assert calculate_scale_factor(3, frame_width, frame_spacing) == pytest.approx(expected)

def test_calculate_max_item_width():
    frame_width = 100
    frame_spacing = 10
    expected_max = 2 * frame_width + frame_spacing  # 210
    
    # Schedule with mixed volume counts
    schedule = [
        ("Date 1", [1]),       # Width: 100
        ("Date 2", [1, 2]),    # Width: 210
        ("Date 3", [1, 2, 3])  # Width: 210 (scaled to reference)
    ]
    
    max_width = calculate_max_item_width(schedule, frame_width, frame_spacing)
    assert max_width == expected_max

