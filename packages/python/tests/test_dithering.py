"""Tests for dithering functionality."""

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
