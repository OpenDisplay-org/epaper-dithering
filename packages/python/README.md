# epaper-dithering

Dithering algorithms optimized for e-ink/e-paper displays with limited color palettes.

## Installation

```bash
pip install epaper-dithering
```

## Features

- **Perceptually Correct**: Uses linear RGB color space with gamma correction for accurate error diffusion
- **8 Dithering Algorithms**: From simple ordered dithering to high-quality Jarvis-Judice-Ninke
- **6 Color Schemes**: Support for mono, 3-color, 4-color, and 6-color e-paper displays
- **Serpentine Scanning**: Reduces directional artifacts in error diffusion (enabled by default)
- **RGBA Support**: Automatic compositing on white background for transparent images

## Quick Start

```python
from PIL import Image
from epaper_dithering import dither_image, ColorScheme, DitherMode

# Load your image
image = Image.open("photo.jpg")

# Apply dithering for a black/white/red display
dithered = dither_image(image, ColorScheme.BWR, DitherMode.FLOYD_STEINBERG)

# Save result
dithered.save("output.png")
```

## Supported Color Schemes

- **MONO** - Black and white (1-bit)
- **BWR** - Black, white, red (3-color)
- **BWY** - Black, white, yellow (3-color)
- **BWRY** - Black, white, red, yellow (4-color)
- **BWGBRY** - Black, white, green, blue, red, yellow (6-color Spectra)
- **GRAYSCALE_4** - 4-level grayscale

## Dithering Algorithms

| Algorithm | Quality | Speed | Best For |
|-----------|---------|-------|----------|
| NONE | Lowest | Fastest | Testing, simple graphics |
| ORDERED | Low | Very Fast | Patterns, textures |
| SIERRA_LITE | Medium | Fast | Quick results |
| BURKES | Good | Medium | General purpose (default) |
| FLOYD_STEINBERG | Good | Medium | Popular standard |
| SIERRA | High | Medium | Balanced quality |
| ATKINSON | Good | Medium | High contrast, artistic |
| STUCKI | Very High | Slow | Maximum quality |
| JARVIS_JUDICE_NINKE | Highest | Slowest | Smooth gradients |

## Usage Examples

### Basic Usage

```python
from PIL import Image
from epaper_dithering import dither_image, ColorScheme, DitherMode

# Load image
img = Image.open("photo.jpg")

# Apply Floyd-Steinberg dithering for BWR display
result = dither_image(img, ColorScheme.BWR, DitherMode.FLOYD_STEINBERG)
result.save("dithered.png")
```

### All Color Schemes

```python
from epaper_dithering import ColorScheme

# Black and white only
dithered = dither_image(img, ColorScheme.MONO)

# Black, white, and red (common for e-paper tags)
dithered = dither_image(img, ColorScheme.BWR)

# Grayscale (4 levels)
dithered = dither_image(img, ColorScheme.GRAYSCALE_4)

# 6-color display (Spectra)
dithered = dither_image(img, ColorScheme.BWGBRY)
```

### Advanced Options

#### Serpentine Scanning

By default, error diffusion algorithms use serpentine scanning (alternating scan direction per row) to reduce directional artifacts and "worm" patterns. You can disable this for raster scanning:

```python
# Default: serpentine scanning (recommended for best quality)
result = dither_image(img, ColorScheme.BWR, DitherMode.FLOYD_STEINBERG, serpentine=True)

# Disable serpentine for raster scanning (left-to-right only)
result = dither_image(img, ColorScheme.BWR, DitherMode.FLOYD_STEINBERG, serpentine=False)
```

Note: The `serpentine` parameter only affects error diffusion algorithms (Floyd-Steinberg, Burkes, Atkinson, Sierra, Sierra Lite, Stucki, Jarvis-Judice-Ninke). It has no effect on NONE and ORDERED modes.

#### RGBA Images

Images with transparency (RGBA mode) are automatically composited on a white background, matching the typical appearance of e-paper displays:

```python
# RGBA images are handled automatically
rgba_img = Image.open("transparent.png")  # Has alpha channel
result = dither_image(rgba_img, ColorScheme.BWR)
# Transparent areas become white
```


## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ --cov=src/epaper_dithering

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/epaper_dithering
```

## Credits

Originally developed as part of [py-opendisplay](https://github.com/OpenDisplay-org/py-opendisplay).
Extracted to enable reuse across multiple e-paper display projects.