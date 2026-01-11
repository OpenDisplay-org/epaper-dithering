"""E-ink display dithering algorithms.

A standalone library providing multiple dithering algorithms optimized
for limited-color e-paper/e-ink displays.
"""

from .core import dither_image
from .enums import DitherMode
from .palettes import ColorPalette, ColorScheme

__version__ = "0.1.0"

__all__ = [
    "dither_image",
    "DitherMode",
    "ColorPalette",
    "ColorScheme",
]
