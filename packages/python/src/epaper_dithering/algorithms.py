"""Dithering algorithm implementations for e-paper displays."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

from .color_space import srgb_to_linear
from .palettes import ColorScheme


@dataclass(frozen=True)
class ErrorDiffusionKernel:
    """Error diffusion kernel specification.

    Defines how quantization error is distributed to neighboring pixels.
    Each kernel is characterized by a name, divisor, and list of offset weights.

    Attributes:
        name: Human-readable kernel name
        divisor: Normalization divisor for weights
        offsets: List of (dx, dy, weight) tuples where:
            - dx: horizontal offset (positive = right)
            - dy: vertical offset (positive = down)
            - weight: error weight (will be divided by divisor)
            Note: (0, 0) is current pixel (already processed)
    """

    name: str
    divisor: float
    offsets: list[tuple[int, int, float]]


# Error diffusion kernel definitions
# Each kernel represents a different error distribution strategy

FLOYD_STEINBERG = ErrorDiffusionKernel(
    name="Floyd-Steinberg",
    divisor=16,
    offsets=[
        (1, 0, 7),   # Right: 7/16
        (-1, 1, 3),  # Down-left: 3/16
        (0, 1, 5),   # Down: 5/16
        (1, 1, 1),   # Down-right: 1/16
    ],
)

BURKES = ErrorDiffusionKernel(
    name="Burkes",
    divisor=200,
    offsets=[
        (1, 0, 32), (2, 0, 12),  # Current row
        (-2, 1, 5), (-1, 1, 12), (0, 1, 26), (1, 1, 12), (2, 1, 5),  # Next row
    ],
)

SIERRA = ErrorDiffusionKernel(
    name="Sierra",
    divisor=32,
    offsets=[
        (1, 0, 5), (2, 0, 3),  # Current row
        (-2, 1, 2), (-1, 1, 4), (0, 1, 5), (1, 1, 4), (2, 1, 2),  # Row +1
        (-1, 2, 2), (0, 2, 3), (1, 2, 2),  # Row +2
    ],
)

SIERRA_LITE = ErrorDiffusionKernel(
    name="Sierra Lite",
    divisor=4,
    offsets=[
        (1, 0, 2),   # Right: 2/4
        (-1, 1, 1),  # Down-left: 1/4
        (0, 1, 1),   # Down: 1/4
    ],
)

ATKINSON = ErrorDiffusionKernel(
    name="Atkinson",
    divisor=8,
    offsets=[
        (1, 0, 1), (2, 0, 1),  # Current row
        (-1, 1, 1), (0, 1, 1), (1, 1, 1),  # Row +1
        (0, 2, 1),  # Row +2
    ],
)

STUCKI = ErrorDiffusionKernel(
    name="Stucki",
    divisor=42,
    offsets=[
        (1, 0, 8), (2, 0, 4),  # Current row
        (-2, 1, 2), (-1, 1, 4), (0, 1, 8), (1, 1, 4), (2, 1, 2),  # Row +1
        (-2, 2, 1), (-1, 2, 2), (0, 2, 4), (1, 2, 2), (2, 2, 1),  # Row +2
    ],
)

JARVIS_JUDICE_NINKE = ErrorDiffusionKernel(
    name="Jarvis-Judice-Ninke",
    divisor=48,
    offsets=[
        (1, 0, 7), (2, 0, 5),  # Current row
        (-2, 1, 3), (-1, 1, 5), (0, 1, 7), (1, 1, 5), (2, 1, 3),  # Row +1
        (-2, 2, 1), (-1, 2, 3), (0, 2, 5), (1, 2, 3), (2, 2, 1),  # Row +2
    ],
)


def get_palette_colors(color_scheme: ColorScheme) -> list[tuple[int, int, int]]:
    """Get RGB palette for color scheme.

    Args:
        color_scheme: Display color scheme

    Returns:
        List of RGB tuples for palette (order matters for encoding)
    """
    return list(color_scheme.palette.colors.values())


def find_closest_palette_color_linear(
    rgb_linear: tuple[float, float, float],
    palette_linear: list[tuple[float, float, float]],
) -> int:
    """Find closest palette color using perceptual weighting in linear space.

    Uses ITU-R BT.601 luma coefficients for perceptual weighting:
    - Red: 0.299 (moderate perceptual importance)
    - Green: 0.587 (most perceptually important)
    - Blue: 0.114 (least perceptually important)

    This better matches human vision compared to simple RGB Euclidean distance.

    Args:
        rgb_linear: Input RGB color in linear space [0.0-1.0]
        palette_linear: Palette colors in linear space [0.0-1.0]

    Returns:
        Index of closest palette color
    """
    # ITU-R BT.601 luma weights
    LUMA_WEIGHTS = np.array([0.299, 0.587, 0.114], dtype=np.float32)

    min_distance = float("inf")
    closest_idx = 0

    rgb_array = np.array(rgb_linear, dtype=np.float32)

    for idx, pal_color in enumerate(palette_linear):
        pal_array = np.array(pal_color, dtype=np.float32)

        # Weighted Euclidean distance
        diff = rgb_array - pal_array
        distance = np.sum(LUMA_WEIGHTS * (diff**2))

        if distance < min_distance:
            min_distance = distance
            closest_idx = idx

    return closest_idx


def error_diffusion_dither(
    image: Image.Image,
    color_scheme: ColorScheme,
    kernel: ErrorDiffusionKernel,
    serpentine: bool = True,
) -> Image.Image:
    """Generic error diffusion dithering with any kernel.

    This function handles all aspects of error diffusion dithering:
    - Image preprocessing (RGBA → RGB on white, gamma correction)
    - Palette conversion to linear space
    - Serpentine or raster scanning
    - Error diffusion using provided kernel
    - Output assembly

    Working in linear RGB space ensures that error distribution is
    perceptually correct. Errors are calculated and propagated in
    linear light values, not gamma-encoded sRGB.

    Args:
        image: Input image (any PIL mode)
        color_scheme: Target color scheme
        kernel: Error diffusion kernel specification
        serpentine: Use serpentine scanning to reduce directional artifacts

    Returns:
        Dithered palette image in sRGB

    Notes:
        - RGBA images are composited on WHITE background (e-paper assumption)
        - Error buffer is unbounded during processing (can go negative or >1.0)
        - Clamping only occurs when reading pixels for quantization
        - Serpentine scanning alternates row direction to eliminate worm artifacts
    """
    # ===== Image Preprocessing =====
    # Convert to RGB, handling alpha channel properly
    if image.mode == "RGBA":
        # Composite on WHITE background (e-paper displays have white base)
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])  # Use alpha as mask
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # ===== Color Space Conversion =====
    # Convert from sRGB [0-255] to linear RGB [0.0-1.0]
    pixels_srgb = np.array(image, dtype=np.uint8)
    pixels_linear = srgb_to_linear(pixels_srgb.astype(np.float32))
    height, width = pixels_linear.shape[:2]

    # Convert palette to linear space
    palette_srgb = get_palette_colors(color_scheme)
    palette_linear = [
        tuple(srgb_to_linear(np.array(color, dtype=np.float32)))
        for color in palette_srgb
    ]

    # ===== Output Preparation =====
    output = Image.new("P", (width, height))
    output_pixels = np.zeros((height, width), dtype=np.uint8)

    # ===== Error Diffusion Loop =====
    for y in range(height):
        # Serpentine scanning: alternate direction each row
        if serpentine and y % 2 == 1:
            x_range = range(width - 1, -1, -1)  # Right to left
        else:
            x_range = range(width)  # Left to right

        for x in x_range:
            # Read current pixel (clamped to valid range)
            # Note: pixels_linear buffer can be outside [0, 1] due to error accumulation
            old_pixel = tuple(np.clip(pixels_linear[y, x, :3], 0.0, 1.0))

            # Find closest palette color
            new_idx = find_closest_palette_color_linear(old_pixel, palette_linear)
            new_pixel = palette_linear[new_idx]

            # Store palette index
            output_pixels[y, x] = new_idx

            # Calculate quantization error (in linear space)
            error = np.array(
                [old_pixel[i] - new_pixel[i] for i in range(3)], dtype=np.float32
            )

            # Distribute error using kernel
            for dx, dy, weight in kernel.offsets:
                # Flip horizontal offset if serpentine on odd row
                if serpentine and y % 2 == 1:
                    dx = -dx

                nx, ny = x + dx, y + dy

                # Check bounds and distribute error
                if 0 <= nx < width and 0 <= ny < height:
                    pixels_linear[ny, nx] += error * (weight / kernel.divisor)

    # ===== Output Assembly =====
    output.putdata(output_pixels.flatten())

    # Set palette (in sRGB)
    flat_palette = [c for rgb in palette_srgb for c in rgb]
    output.putpalette(flat_palette)

    return output


# =============================================================================
# Individual Error Diffusion Algorithms (Thin Wrappers)
# =============================================================================
# Each function below is a thin wrapper around error_diffusion_dither()
# with a specific kernel. This eliminates code duplication while maintaining
# the original API.


def floyd_steinberg_dither(
    image: Image.Image, color_scheme: ColorScheme, serpentine: bool = True
) -> Image.Image:
    """Apply Floyd-Steinberg error diffusion dithering.

    Floyd-Steinberg kernel (divisor 16):
           X   7
       3   5   1

    Most popular error diffusion algorithm, good balance of quality and speed.

    Args:
        image: Input image
        color_scheme: Target color scheme
        serpentine: Use serpentine scanning (reduces artifacts)

    Returns:
        Dithered image
    """
    return error_diffusion_dither(image, color_scheme, FLOYD_STEINBERG, serpentine)


def burkes_dither(
    image: Image.Image, color_scheme: ColorScheme, serpentine: bool = True
) -> Image.Image:
    """Apply Burkes error diffusion dithering.

    Burkes kernel (divisor 200):
                 X  32  12
         5  12  26  12   5

    Args:
        image: Input image
        color_scheme: Target color scheme
        serpentine: Use serpentine scanning (reduces artifacts)

    Returns:
        Dithered image
    """
    return error_diffusion_dither(image, color_scheme, BURKES, serpentine)


def sierra_dither(
    image: Image.Image, color_scheme: ColorScheme, serpentine: bool = True
) -> Image.Image:
    """Apply Sierra error diffusion dithering.

    Sierra kernel (divisor 32):
               X   5   3
       2   4   5   4   2
           2   3   2

    Sierra-2-4A variant, balanced quality and performance.

    Args:
        image: Input image
        color_scheme: Target color scheme
        serpentine: Use serpentine scanning (reduces artifacts)

    Returns:
        Dithered image
    """
    return error_diffusion_dither(image, color_scheme, SIERRA, serpentine)


def sierra_lite_dither(
    image: Image.Image, color_scheme: ColorScheme, serpentine: bool = True
) -> Image.Image:
    """Apply Sierra Lite error diffusion dithering.

    Sierra Lite kernel (divisor 4):
         X   2
       1   1

    Fast, simple 3-neighbor algorithm.

    Args:
        image: Input image
        color_scheme: Target color scheme
        serpentine: Use serpentine scanning (reduces artifacts)

    Returns:
        Dithered image
    """
    return error_diffusion_dither(image, color_scheme, SIERRA_LITE, serpentine)


def atkinson_dither(
    image: Image.Image, color_scheme: ColorScheme, serpentine: bool = True
) -> Image.Image:
    """Apply Atkinson error diffusion dithering.

    Atkinson kernel (divisor 8):
           X   1   1
       1   1   1
           1

    Designed for early Macintosh computers, produces distinct artistic look.

    Args:
        image: Input image
        color_scheme: Target color scheme
        serpentine: Use serpentine scanning (reduces artifacts)

    Returns:
        Dithered image
    """
    return error_diffusion_dither(image, color_scheme, ATKINSON, serpentine)


def stucki_dither(
    image: Image.Image, color_scheme: ColorScheme, serpentine: bool = True
) -> Image.Image:
    """Apply Stucki error diffusion dithering.

    Stucki kernel (divisor 42):
               X   8   4
       2   4   8   4   2
       1   2   4   2   1

    High quality algorithm with wide error distribution.

    Args:
        image: Input image
        color_scheme: Target color scheme
        serpentine: Use serpentine scanning (reduces artifacts)

    Returns:
        Dithered image
    """
    return error_diffusion_dither(image, color_scheme, STUCKI, serpentine)


def jarvis_judice_ninke_dither(
    image: Image.Image, color_scheme: ColorScheme, serpentine: bool = True
) -> Image.Image:
    """Apply Jarvis-Judice-Ninke error diffusion dithering.

    Jarvis-Judice-Ninke kernel (divisor 48):
               X   7   5
       3   5   7   5   3
       1   3   5   3   1

    Highest quality algorithm with symmetrical error distribution.

    Args:
        image: Input image
        color_scheme: Target color scheme
        serpentine: Use serpentine scanning (reduces artifacts)

    Returns:
        Dithered image
    """
    return error_diffusion_dither(image, color_scheme, JARVIS_JUDICE_NINKE, serpentine)


# =============================================================================
# Non-Error-Diffusion Algorithms (TODO: Refactor in separate task)
# =============================================================================


def direct_palette_map(image: Image.Image, color_scheme: ColorScheme) -> Image.Image:
    """Map image colors directly to palette without dithering.

    Args:
        image: Input image
        color_scheme: Target color scheme

    Returns:
        Image with palette colors
    """
    # Handle alpha channel properly (composite on white)
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    palette = get_palette_colors(color_scheme)
    pixels = np.array(image)
    height, width = pixels.shape[:2]

    # Create output image
    output = Image.new("P", (width, height))
    output_pixels = np.zeros((height, width), dtype=np.uint8)

    # Map each pixel to closest palette color
    # TODO: Use linear space and weighted distance (like error diffusion)
    for y in range(height):
        for x in range(width):
            rgb = tuple(pixels[y, x, :3])
            # Find closest using simple Euclidean (legacy behavior)
            min_distance = float("inf")
            closest_idx = 0
            for idx, pal_color in enumerate(palette):
                distance = sum((int(a) - int(b)) ** 2 for a, b in zip(rgb, pal_color))
                if distance < min_distance:
                    min_distance = distance
                    closest_idx = idx
            output_pixels[y, x] = closest_idx

    output.putdata(output_pixels.flatten())

    # Set palette
    flat_palette = [c for rgb in palette for c in rgb]
    output.putpalette(flat_palette)

    return output


def ordered_dither(image: Image.Image, color_scheme: ColorScheme) -> Image.Image:
    """Apply ordered (Bayer) dithering with proper threshold comparison.

    Uses a normalized 4x4 Bayer matrix to add spatially-distributed noise
    before quantization. Unlike error diffusion, ordered dithering does not
    propagate errors between pixels, making it suitable for parallel processing.

    This implementation works in linear RGB space with proper gamma correction
    and uses small centered threshold offsets (not the broken 0-240 bias from
    the previous version).

    Args:
        image: Input image (any PIL mode)
        color_scheme: Target color scheme

    Returns:
        Dithered palette image

    Notes:
        - Bayer matrix normalized to [-0.5, 0.5] centered around 0
        - RGBA images composited on white background
        - Uses perceptual color distance (ITU-R BT.601 luma weights)
        - Works in linear RGB space for correct quantization
    """
    # Bayer 4x4 matrix normalized to [-0.5, 0.5] (centered around 0)
    # This provides small threshold variations without massive bias
    bayer_matrix = (
        np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]],
                 dtype=np.float32)
        / 16.0
        - 0.5
    )

    # ===== Image Preprocessing =====
    # Handle alpha channel
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # ===== Color Space Conversion =====
    # Convert to linear RGB for correct dithering
    pixels_srgb = np.array(image, dtype=np.uint8)
    pixels_linear = srgb_to_linear(pixels_srgb.astype(np.float32))
    height, width = pixels_linear.shape[:2]

    # Convert palette to linear
    palette_srgb = get_palette_colors(color_scheme)
    palette_linear = [
        tuple(srgb_to_linear(np.array(color, dtype=np.float32)))
        for color in palette_srgb
    ]

    # ===== Output Preparation =====
    output = Image.new("P", (width, height))
    output_pixels = np.zeros((height, width), dtype=np.uint8)

    # ===== Ordered Dithering =====
    for y in range(height):
        for x in range(width):
            # Get Bayer threshold for this position (small value in [-0.5, 0.5])
            threshold = bayer_matrix[y % 4, x % 4]

            # Add threshold to pixel (in linear space)
            # This creates spatially-distributed quantization points
            dithered_pixel = pixels_linear[y, x, :3] + threshold
            dithered_pixel = np.clip(dithered_pixel, 0.0, 1.0)

            # Find closest palette color using perceptual distance
            output_pixels[y, x] = find_closest_palette_color_linear(
                tuple(dithered_pixel), palette_linear
            )

    # ===== Output Assembly =====
    output.putdata(output_pixels.flatten())
    flat_palette = [c for rgb in palette_srgb for c in rgb]
    output.putpalette(flat_palette)

    return output
