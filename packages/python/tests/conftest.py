"""Pytest configuration and fixtures."""

import pytest
from PIL import Image


@pytest.fixture
def small_test_image():
    """Create a small RGB test image for dithering tests."""
    return Image.new("RGB", (10, 10), color=(128, 128, 128))


@pytest.fixture
def gradient_image():
    """Create a gradient test image."""
    img = Image.new("RGB", (100, 100))
    pixels = img.load()
    for y in range(100):
        for x in range(100):
            value = int((x / 100) * 255)
            pixels[x, y] = (value, value, value)
    return img
