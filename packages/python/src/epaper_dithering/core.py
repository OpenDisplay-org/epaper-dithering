"""Main dithering interface."""

from __future__ import annotations

import logging

from PIL import Image

from . import algorithms
from .enums import DitherMode
from .palettes import ColorScheme

_LOGGER = logging.getLogger(__name__)


def dither_image(
        image: Image.Image,
        color_scheme: ColorScheme,
        mode: DitherMode = DitherMode.BURKES
) -> Image.Image:
    """Apply dithering to image for e-paper display.

    Args:
        image: Input image (RGB or RGBA)
        color_scheme: Target display color scheme
        mode: Dithering algorithm (default: BURKES)

    Returns:
        Dithered palette image matching color scheme

    Examples:
        >>> from PIL import Image
        >>> from epaper_dithering import dither_image, ColorScheme, DitherMode
        >>>
        >>> img = Image.open("photo.jpg")
        >>> dithered = dither_image(img, ColorScheme.BWR, DitherMode.FLOYD_STEINBERG)
        >>> dithered.save("dithered.png")
    """
    _LOGGER.debug("Applying %s dithering for %s color scheme", mode.name, color_scheme.name)

    match mode:
        case DitherMode.NONE:
            return algorithms.direct_palette_map(image, color_scheme)
        case DitherMode.ORDERED:
            return algorithms.ordered_dither(image, color_scheme)
        case DitherMode.FLOYD_STEINBERG:
            return algorithms.floyd_steinberg_dither(image, color_scheme)
        case DitherMode.ATKINSON:
            return algorithms.atkinson_dither(image, color_scheme)
        case DitherMode.STUCKI:
            return algorithms.stucki_dither(image, color_scheme)
        case DitherMode.SIERRA:
            return algorithms.sierra_dither(image, color_scheme)
        case DitherMode.SIERRA_LITE:
            return algorithms.sierra_lite_dither(image, color_scheme)
        case DitherMode.JARVIS_JUDICE_NINKE:
            return algorithms.jarvis_judice_ninke_dither(image, color_scheme)
        case _:  # BURKES or fallback
            return algorithms.burkes_dither(image, color_scheme)
