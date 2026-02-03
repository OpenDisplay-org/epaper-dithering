"""LAB color space conversions for perceptually accurate color matching.

CIELAB (L*a*b*) is a color space designed to be perceptually uniform, meaning
equal distances in LAB space represent equal perceived color differences.

Why LAB for E-Paper Dithering:
------------------------------
RGB Euclidean distance doesn't match human color perception. Even with luma
weighting, RGB distance can incorrectly match colors. For example, yellow
(255,255,0) is "close" to many skin tones in RGB space, causing faces to
appear too yellow.

LAB fixes this by using perceptually uniform distances. The same Euclidean
distance formula works correctly in LAB space without any weighting needed.

Implementation:
--------------
- RGB → XYZ → LAB conversion using D65 illuminant (standard daylight)
- Simple Euclidean distance in LAB space (no weights needed)
- Significantly improves color accuracy for 6-color displays

Performance:
-----------
Optimized implementation pre-converts palette to LAB once before dithering loops,
eliminating redundant conversions. Error diffusion algorithms are 5-10x faster
than naive LAB implementation with minimal overhead vs RGB matching.

References:
----------
- CIE 1976 L*a*b* color space
- http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
"""

from __future__ import annotations

import numpy as np


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """Convert RGB to CIELAB color space.

    Args:
        rgb: RGB values in [0, 1] range. Shape: (..., 3)

    Returns:
        LAB values. L in [0, 100], a and b in [-128, 127]. Shape: (..., 3)
    """
    # RGB -> XYZ (using D65 illuminant, sRGB primaries)
    # Matrix from http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
    M = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041]
    ], dtype=np.float32)

    # RGB is already in linear space from srgb_to_linear
    xyz = rgb @ M.T

    # XYZ -> LAB
    # Reference white D65
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883

    # Normalize
    xyz_norm = xyz / np.array([Xn, Yn, Zn], dtype=np.float32)

    # Apply nonlinear function
    epsilon = 216 / 24389  # 0.008856
    kappa = 24389 / 27  # 903.3

    def f(t):
        """LAB nonlinear function."""
        mask = t > epsilon
        result = np.empty_like(t)
        result[mask] = np.cbrt(t[mask])
        result[~mask] = (kappa * t[~mask] + 16) / 116
        return result

    fx = f(xyz_norm[..., 0])
    fy = f(xyz_norm[..., 1])
    fz = f(xyz_norm[..., 2])

    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)

    return np.stack([L, a, b], axis=-1)


def find_closest_color_lab_preconverted(
    rgb_linear_pixel: np.ndarray,
    palette_lab: np.ndarray,
) -> int:
    """Find closest palette color using pre-converted LAB palette.

    Optimized for per-pixel matching in error diffusion loops where the palette
    is constant and can be pre-converted to LAB once before the loop.

    Args:
        rgb_linear_pixel: Single pixel in linear RGB space. Shape: (3,)
        palette_lab: Palette colors already in LAB space. Shape: (num_colors, 3)
            Use rgb_to_lab(palette_linear) to pre-convert before loop.

    Returns:
        Index of closest palette color (scalar int)
    """
    # Convert only the pixel to LAB (palette already converted)
    lab_pixel = rgb_to_lab(rgb_linear_pixel)  # (3,)

    # Compute distances to all palette colors
    diff = lab_pixel - palette_lab  # (num_colors, 3)
    distances = np.sum(diff ** 2, axis=-1)  # (num_colors,)

    # Return index of minimum distance
    return int(np.argmin(distances))


def find_closest_palette_color_lab(
    rgb_linear: np.ndarray,
    palette_linear: np.ndarray,
) -> np.ndarray:
    """Find closest palette color using LAB color space.

    LAB is perceptually uniform, so Euclidean distance in LAB space
    accurately represents perceived color difference.

    This function converts both pixels and palette to LAB, making it suitable
    for batch operations. For per-pixel loops with constant palettes, use
    find_closest_color_lab_preconverted() instead for better performance.

    Args:
        rgb_linear: Linear RGB values. Shape:
            - (3,) for single pixel
            - (height, width, 3) for entire image
        palette_linear: Palette colors in linear space. Shape: (num_colors, 3)

    Returns:
        Palette indices. Shape matches input without last dimension:
            - scalar for single pixel
            - (height, width) for image
    """
    # Convert to LAB
    lab_pixel = rgb_to_lab(rgb_linear)
    lab_palette = rgb_to_lab(palette_linear)

    # Vectorized palette matching using broadcasting
    # (..., 1, 3) - (1, colors, 3) -> (..., colors, 3)
    diff = lab_pixel[..., np.newaxis, :] - lab_palette[np.newaxis, :, :]

    # Simple Euclidean distance in LAB space (no weighting needed!)
    # LAB is designed to be perceptually uniform
    distances = np.sum(diff ** 2, axis=-1)

    # Find minimum: (...,)
    return np.argmin(distances, axis=-1)  # type: ignore[no-any-return]
