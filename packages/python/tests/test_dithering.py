"""Tests for dithering functionality."""

import numpy as np
import pytest
from PIL import Image

from epaper_dithering import ColorScheme, DitherMode, dither_image


class TestDitheringAlgorithms:
    """Test all dithering algorithms."""

    @pytest.mark.parametrize("mode", list(DitherMode))
    def test_all_modes_produce_valid_output(self, small_test_image, mode):
        """Test each dithering mode produces valid palette image."""
        result = dither_image(small_test_image, ColorScheme.BWR, mode)

        assert result.mode == 'P', f"Output should be palette mode, got {result.mode}"
        assert result.size == small_test_image.size, "Output size should match input"

        # Verify palette was set
        palette = result.getpalette()
        assert palette is not None, "Output should have a palette"

    @pytest.mark.parametrize("scheme", list(ColorScheme))
    def test_all_color_schemes(self, small_test_image, scheme):
        """Test each color scheme works correctly."""
        result = dither_image(small_test_image, scheme, DitherMode.BURKES)

        assert result.mode == 'P'
        palette = result.getpalette()
        assert len(palette) >= scheme.color_count * 3, "Palette should contain all scheme colors"

    def test_output_image_type(self, small_test_image):
        """Test output is PIL Image."""
        result = dither_image(small_test_image, ColorScheme.MONO, DitherMode.FLOYD_STEINBERG)
        assert isinstance(result, Image.Image)

    def test_rgba_input_handling(self):
        """Test RGBA images are handled correctly."""
        rgba_img = Image.new("RGBA", (10, 10), color=(128, 128, 128, 255))
        result = dither_image(rgba_img, ColorScheme.BWR, DitherMode.BURKES)

        assert result.mode == 'P'
        assert result.size == rgba_img.size


class TestColorSchemes:
    """Test color scheme definitions."""

    def test_scheme_has_correct_palette(self):
        """Test color schemes have expected color counts."""
        assert ColorScheme.MONO.color_count == 2
        assert ColorScheme.BWR.color_count == 3
        assert ColorScheme.BWY.color_count == 3
        assert ColorScheme.BWRY.color_count == 4
        assert ColorScheme.BWGBRY.color_count == 6
        assert ColorScheme.GRAYSCALE_4.color_count == 4

    def test_palette_colors_valid(self):
        """Test all palette colors are valid RGB tuples."""
        for scheme in ColorScheme:
            for color in scheme.palette.colors.values():
                assert len(color) == 3, "RGB tuple should have 3 values"
                assert all(0 <= c <= 255 for c in color), "RGB values should be 0-255"

    def test_accent_color_defined(self):
        """Test each scheme has an accent color."""
        for scheme in ColorScheme:
            assert scheme.accent_color in scheme.palette.colors, \
                f"Accent color '{scheme.accent_color}' should be in palette"

    def test_from_value_method(self):
        """Test ColorScheme.from_value() works correctly."""
        assert ColorScheme.from_value(0) == ColorScheme.MONO
        assert ColorScheme.from_value(1) == ColorScheme.BWR

        with pytest.raises(ValueError):
            ColorScheme.from_value(99)


class TestDitherMode:
    """Test DitherMode enum."""

    def test_all_modes_defined(self):
        """Test all expected dithering modes are defined."""
        expected_modes = [
            DitherMode.NONE,
            DitherMode.BURKES,
            DitherMode.ORDERED,
            DitherMode.FLOYD_STEINBERG,
            DitherMode.ATKINSON,
            DitherMode.STUCKI,
            DitherMode.SIERRA,
            DitherMode.SIERRA_LITE,
            DitherMode.JARVIS_JUDICE_NINKE,
        ]

        for mode in expected_modes:
            assert mode in DitherMode

    def test_mode_values(self):
        """Test DitherMode values match expected integers."""
        assert DitherMode.NONE == 0
        assert DitherMode.BURKES == 1
        assert DitherMode.FLOYD_STEINBERG == 3


class TestColorScience:
    """Test v2.0.0 color science improvements."""

    def test_gamma_correction_improves_midtones(self):
        """Test that gamma correction prevents dark crushing in midtones.

        With proper gamma correction, all 4 grayscale levels should be used
        in a gradient, not just black and white.
        """
        # Create gradient from black to white
        gradient = Image.new("RGB", (256, 64))
        for x in range(256):
            for y in range(64):
                gradient.putpixel((x, y), (x, x, x))

        result = dither_image(gradient, ColorScheme.GRAYSCALE_4, DitherMode.FLOYD_STEINBERG)

        # Analyze histogram of palette usage
        histogram = result.histogram()[:4]  # First 4 entries (grayscale palette)

        # All 4 grays should be used (not just black/white)
        assert all(count > 0 for count in histogram), \
            f"All 4 grayscale levels should be used, got counts: {histogram}"

        # Middle grays should be used significantly (not crushed to extremes)
        assert histogram[1] > 100, "Gray1 should be used in midtones"
        assert histogram[2] > 100, "Gray2 should be used in midtones"

    def test_alpha_composites_on_white(self):
        """Test RGBA images composite on white background, not black.

        This tests that alpha handling is correct. With proper compositing,
        semi-transparent white on white should stay white, and
        semi-transparent black should not composite on black background.
        """
        # Create semi-transparent white (should stay mostly white on white background)
        rgba_white = Image.new("RGBA", (10, 10), (255, 255, 255, 128))
        result_white = dither_image(rgba_white, ColorScheme.MONO, DitherMode.NONE)
        histogram_white = result_white.histogram()

        # Should map to white (compositing white on white = white)
        assert histogram_white[1] > histogram_white[0], \
            f"Semi-transparent white should stay white, got {histogram_white[:2]}"

        # Also test that transparent areas are handled
        # Create image with transparent pixels
        rgba_transparent = Image.new("RGBA", (10, 10), (0, 0, 0, 0))  # Fully transparent
        result_transparent = dither_image(rgba_transparent, ColorScheme.MONO, DitherMode.NONE)
        histogram_transparent = result_transparent.histogram()

        # Fully transparent should become white (background color)
        assert histogram_transparent[1] == 100, \
            f"Fully transparent should become white background, got {histogram_transparent[:2]}"

    def test_serpentine_parameter_works(self):
        """Test serpentine parameter can be enabled/disabled."""
        # Create a gradient image (not solid color) so error diffusion has visible effect
        # Solid colors have no error to diffuse, making serpentine differences invisible
        gradient = Image.new("RGB", (100, 100))
        pixels = gradient.load()
        for y in range(100):
            for x in range(100):
                # Horizontal gradient from black to white
                gray_value = int(x * 255 / 99)
                pixels[x, y] = (gray_value, gray_value, gray_value)

        # Test with serpentine enabled (default)
        result_serpentine = dither_image(
            gradient, ColorScheme.MONO, DitherMode.FLOYD_STEINBERG, serpentine=True
        )

        # Test with serpentine disabled
        result_raster = dither_image(
            gradient, ColorScheme.MONO, DitherMode.FLOYD_STEINBERG, serpentine=False
        )

        # Both should produce valid output
        assert result_serpentine.mode == 'P'
        assert result_raster.mode == 'P'

        # Results should be different (serpentine changes the pattern)
        array_serpentine = np.array(result_serpentine)
        array_raster = np.array(result_raster)
        assert not np.array_equal(array_serpentine, array_raster), \
            "Serpentine should produce different output than raster"

    def test_deterministic_output(self):
        """Test that dithering produces identical output on repeated runs."""
        img = Image.new("RGB", (50, 50), (128, 128, 128))

        result1 = dither_image(img, ColorScheme.BWR, DitherMode.FLOYD_STEINBERG)
        result2 = dither_image(img, ColorScheme.BWR, DitherMode.FLOYD_STEINBERG)

        # Should be exactly identical
        assert np.array_equal(np.array(result1), np.array(result2)), \
            "Dithering should be deterministic"

    def test_ordered_dithering_uses_threshold_correctly(self):
        """Test ordered dithering produces reasonable distribution.

        This verifies the fix for the broken 0-240 bias in the old implementation.
        With LAB color matching, sRGB 186 (50% linear) produces approximately
        25% black due to perceptual lightness calculations.
        """
        # sRGB 186 ≈ 50% linear light
        # With LAB: L* ≈ 75 (perceptual lightness), closer to white perceptually
        gray = Image.new("RGB", (16, 16), (186, 186, 186))
        result = dither_image(gray, ColorScheme.MONO, DitherMode.ORDERED)

        pixels = list(result.getdata())

        # Should be mix of black (0) and white (1)
        unique = set(pixels)
        assert len(unique) == 2, f"Should use both black and white, got {unique}"
        assert 0 in unique and 1 in unique

        # With LAB color matching, this gray produces ~25% black (perceptually lighter)
        black_count = pixels.count(0)
        white_count = pixels.count(1)
        ratio = black_count / (black_count + white_count)
        assert 0.20 < ratio < 0.35, \
            f"Should be ~25% black with LAB matching, got ratio {ratio:.2f}"

    def test_all_error_diffusion_with_serpentine(self):
        """Test all error diffusion algorithms accept serpentine parameter."""
        img = Image.new("RGB", (20, 20), (100, 100, 100))

        error_diffusion_modes = [
            DitherMode.FLOYD_STEINBERG,
            DitherMode.BURKES,
            DitherMode.ATKINSON,
            DitherMode.STUCKI,
            DitherMode.SIERRA,
            DitherMode.SIERRA_LITE,
            DitherMode.JARVIS_JUDICE_NINKE,
        ]

        for mode in error_diffusion_modes:
            # Should work with serpentine=True
            result_true = dither_image(img, ColorScheme.MONO, mode, serpentine=True)
            assert result_true.mode == 'P', f"{mode.name} should work with serpentine=True"

            # Should work with serpentine=False
            result_false = dither_image(img, ColorScheme.MONO, mode, serpentine=False)
            assert result_false.mode == 'P', f"{mode.name} should work with serpentine=False"


class TestMeasuredPalettes:
    """Test v0.4.0 measured palette functionality."""

    def test_dithering_accepts_colorpalette(self, small_test_image):
        """Test ColorPalette accepted by dither_image."""
        from epaper_dithering import ColorPalette

        measured = ColorPalette(
            colors={'black': (2, 2, 2), 'white': (179, 182, 171), 'red': (117, 10, 0)},
            accent='red'
        )
        result = dither_image(small_test_image, measured, DitherMode.BURKES)

        assert result.mode == 'P'
        assert result.size == small_test_image.size

    def test_measured_vs_pure_produces_different_output(self):
        """Test measured colors produce different output than pure RGB."""
        from epaper_dithering import ColorPalette

        # Create simple gradient
        gradient = Image.new("RGB", (50, 50), (128, 128, 128))

        pure = ColorScheme.BWR
        measured = ColorPalette(
            colors={'black': (5, 5, 5), 'white': (180, 180, 170), 'red': (115, 12, 2)},
            accent='red'
        )

        result_pure = dither_image(gradient, pure, DitherMode.FLOYD_STEINBERG)
        result_measured = dither_image(gradient, measured, DitherMode.FLOYD_STEINBERG)

        # Should be different
        assert not np.array_equal(np.array(result_pure), np.array(result_measured))

    def test_backward_compatibility_colorscheme(self, small_test_image):
        """Test existing ColorScheme API still works unchanged."""
        # This is the v1.x/v2.0 API - should still work
        result = dither_image(small_test_image, ColorScheme.BWR)
        assert result.mode == 'P'

    def test_predefined_measured_palettes_work(self, small_test_image):
        """Test exported measured palette constants."""
        from epaper_dithering import HANSHOW_BWR, MONO_4_26, SPECTRA_7_3_6COLOR

        # Test 6-color palette
        result = dither_image(small_test_image, SPECTRA_7_3_6COLOR, DitherMode.BURKES)
        assert result.mode == 'P'

        # Test mono palette
        result = dither_image(small_test_image, MONO_4_26, DitherMode.FLOYD_STEINBERG)
        assert result.mode == 'P'

        # Test BWR palette
        result = dither_image(small_test_image, HANSHOW_BWR, DitherMode.SIERRA)
        assert result.mode == 'P'

    def test_bright_green_matches_green_not_yellow(self):
        """Test that bright green pixels match palette green, not yellow.

        With the SPECTRA measured palette, green is very dark (L~31) while
        yellow is bright (L~75). Naive LAB distance would match bright green
        to yellow due to the lightness gap. The LCH-weighted distance fixes
        this by de-emphasizing lightness and emphasizing hue.
        """
        from epaper_dithering import SPECTRA_7_3_6COLOR

        # Bright saturated green — should match green, not yellow
        green_img = Image.new("RGB", (10, 10), (100, 255, 40))
        result = dither_image(green_img, SPECTRA_7_3_6COLOR, DitherMode.NONE)

        # SPECTRA palette order: black=0, white=1, yellow=2, red=3, blue=4, green=5
        pixels = list(result.getdata())
        green_idx = 5
        assert all(p == green_idx for p in pixels), \
            f"Bright green should map to palette green (idx 5), got indices: {set(pixels)}"

    def test_pure_blue_matches_blue_not_black(self):
        """Test that blue pixels match palette blue, not black.

        The SPECTRA measured black has a slight blue tint (26,13,35).
        The matching should not confuse blue with black.
        """
        from epaper_dithering import SPECTRA_7_3_6COLOR

        blue_img = Image.new("RGB", (10, 10), (0, 0, 255))
        result = dither_image(blue_img, SPECTRA_7_3_6COLOR, DitherMode.NONE)

        # SPECTRA palette order: black=0, white=1, yellow=2, red=3, blue=4, green=5
        pixels = list(result.getdata())
        blue_idx = 4
        assert all(p == blue_idx for p in pixels), \
            f"Pure blue should map to palette blue (idx 4), got indices: {set(pixels)}"
