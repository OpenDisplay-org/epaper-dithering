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
        mode: DitherMode = DitherMode.BURKES,
        serpentine: bool = True
) -> Image.Image:
    """Apply dithering to image for e-paper display.

    Args:
        image: Input image (RGB or RGBA)
        color_scheme: Target display color scheme
        mode: Dithering algorithm (default: BURKES)
        serpentine: Use serpentine scanning for error diffusion (default: True).
            Alternates scan direction each row to reduce directional artifacts.
            Only applies to error diffusion algorithms, ignored for NONE and ORDERED.

    Returns:
        Dithered palette image matching color scheme

    Examples:
        >>> from PIL import Image
        >>> from epaper_dithering import dither_image, ColorScheme, DitherMode
        >>>
        >>> img = Image.open("photo.jpg")
        >>> dithered = dither_image(img, ColorScheme.BWR, DitherMode.FLOYD_STEINBERG)
        >>> dithered.save("dithered.png")
        >>>
        >>> # Disable serpentine if you prefer raster scanning
        >>> dithered_raster = dither_image(img, ColorScheme.BWR,
        ...                                DitherMode.FLOYD_STEINBERG, serpentine=False)

    Notes:
        v2.0.0 changes:
        - Now works in linear RGB space with gamma correction for perceptually correct results
        - RGBA images composite on white background (e-paper assumption)
        - Serpentine scanning enabled by default to reduce worm artifacts
    """
    _LOGGER.debug("Applying %s dithering for %s color scheme", mode.name, color_scheme.name)

    match mode:
        case DitherMode.NONE:
            return algorithms.direct_palette_map(image, color_scheme)
        case DitherMode.ORDERED:
            return algorithms.ordered_dither(image, color_scheme)
        case DitherMode.FLOYD_STEINBERG:
            return algorithms.floyd_steinberg_dither(image, color_scheme, serpentine)
        case DitherMode.ATKINSON:
            return algorithms.atkinson_dither(image, color_scheme, serpentine)
        case DitherMode.STUCKI:
            return algorithms.stucki_dither(image, color_scheme, serpentine)
        case DitherMode.SIERRA:
            return algorithms.sierra_dither(image, color_scheme, serpentine)
        case DitherMode.SIERRA_LITE:
            return algorithms.sierra_lite_dither(image, color_scheme, serpentine)
        case DitherMode.JARVIS_JUDICE_NINKE:
            return algorithms.jarvis_judice_ninke_dither(image, color_scheme, serpentine)
        case _:  # BURKES or fallback
            return algorithms.burkes_dither(image, color_scheme, serpentine)
