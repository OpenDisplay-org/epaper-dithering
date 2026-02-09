"""Tests for LAB color matching and perceptual color science."""

import numpy as np
import pytest
from PIL import Image

from epaper_dithering import ColorScheme, DitherMode, dither_image
from epaper_dithering.color_space_lab import rgb_to_lab


class TestLABConversion:
    """Test RGB to LAB conversion accuracy."""

    def test_white_converts_to_l100(self):
        """Pure white in linear RGB should produce L*=100, a=0, b=0."""
        white = np.array([1.0, 1.0, 1.0])
        lab = rgb_to_lab(white)
        assert lab[0] == pytest.approx(100.0, abs=0.1)
        assert lab[1] == pytest.approx(0.0, abs=0.5)
        assert lab[2] == pytest.approx(0.0, abs=0.5)

    def test_black_converts_to_l0(self):
        """Pure black should produce L*=0, a=0, b=0."""
        black = np.array([0.0, 0.0, 0.0])
        lab = rgb_to_lab(black)
        assert lab[0] == pytest.approx(0.0, abs=0.1)
        assert lab[1] == pytest.approx(0.0, abs=0.5)
        assert lab[2] == pytest.approx(0.0, abs=0.5)

    def test_midgray_lightness(self):
        """50% linear gray should produce L* around 76 (perceptual midpoint)."""
        gray = np.array([0.5, 0.5, 0.5])
        lab = rgb_to_lab(gray)
        assert 70 < lab[0] < 80, f"50% linear gray L* should be ~76, got {lab[0]:.1f}"

    def test_red_has_positive_a(self):
        """Pure red should have positive a* (red-green axis)."""
        red = np.array([1.0, 0.0, 0.0])
        lab = rgb_to_lab(red)
        assert lab[1] > 50, f"Red should have high positive a*, got {lab[1]:.1f}"

    def test_batch_matches_single(self):
        """Batch conversion should match individual conversions."""
        colors = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        batch = rgb_to_lab(colors)
        for i in range(3):
            single = rgb_to_lab(colors[i])
            np.testing.assert_allclose(batch[i], single, atol=1e-10)


class TestColorMatchingAccuracy:
    """Test LCH-weighted color matching on measured palettes."""

    def test_bright_green_matches_green_not_yellow(self):
        """Bright green should match palette green, not yellow.

        With the SPECTRA measured palette, green is very dark (L~31) while
        yellow is bright (L~75). The LCH-weighted distance fixes this by
        de-emphasizing lightness and emphasizing hue.
        """
        from epaper_dithering import SPECTRA_7_3_6COLOR

        green_img = Image.new("RGB", (10, 10), (100, 255, 40))
        result = dither_image(green_img, SPECTRA_7_3_6COLOR, DitherMode.NONE)

        pixels = list(result.get_flattened_data())
        green_idx = 5  # SPECTRA order: black=0, white=1, yellow=2, red=3, blue=4, green=5
        assert all(p == green_idx for p in pixels), \
            f"Bright green should map to palette green (idx 5), got indices: {set(pixels)}"

    def test_pure_blue_matches_blue_not_black(self):
        """Blue should match palette blue, not black.

        The SPECTRA measured black has a slight blue tint (26,13,35).
        """
        from epaper_dithering import SPECTRA_7_3_6COLOR

        blue_img = Image.new("RGB", (10, 10), (0, 0, 255))
        result = dither_image(blue_img, SPECTRA_7_3_6COLOR, DitherMode.NONE)

        pixels = list(result.get_flattened_data())
        blue_idx = 4
        assert all(p == blue_idx for p in pixels), \
            f"Pure blue should map to palette blue (idx 4), got indices: {set(pixels)}"

    def test_measured_vs_pure_produces_different_output(self):
        """Measured colors should produce different dithering than pure RGB."""
        from epaper_dithering import ColorPalette

        gradient = Image.new("RGB", (50, 50), (128, 128, 128))

        pure = ColorScheme.BWR
        measured = ColorPalette(
            colors={'black': (5, 5, 5), 'white': (180, 180, 170), 'red': (115, 12, 2)},
            accent='red'
        )

        result_pure = dither_image(gradient, pure, DitherMode.FLOYD_STEINBERG)
        result_measured = dither_image(gradient, measured, DitherMode.FLOYD_STEINBERG)

        assert not np.array_equal(np.array(result_pure), np.array(result_measured))
