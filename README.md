# epaper-dithering

A monorepo containing dithering algorithm implementations for e-paper/e-ink displays in multiple languages.

## Packages

### Python (`packages/python/`)

Dithering algorithms for e-paper displays. Published to PyPI as `epaper-dithering`.

**Installation:**
```bash
pip install epaper-dithering
```

**Usage:**
```python
from PIL import Image
from epaper_dithering import dither_image, ColorScheme, DitherMode

img = Image.open("photo.jpg")
dithered = dither_image(img, ColorScheme.BWR, DitherMode.FLOYD_STEINBERG)
dithered.save("output.png")
```

See [`packages/python/README.md`](packages/python/README.md) for detailed documentation.

### JavaScript (Coming Soon)

JavaScript/TypeScript implementation for browser and Node.js environments.
Will be published to npm as `@opendisplay/epaper-dithering`.

## Features

- **8 Dithering Algorithms**: From fast ordered dithering to high-quality Jarvis-Judice-Ninke
- **6 Color Schemes**: MONO, BWR, BWY, BWRY, BWGBRY (Spectra 6), GRAYSCALE_4

## Development

### Python Development

```bash
cd packages/python
uv sync --all-extras
uv run pytest tests/ -v
```

### Repository Structure

```
epaper-dithering/
├── packages/
│   ├── python/          # Python implementation
│   │   ├── src/
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── javascript/      # JS implementation (future)
├── fixtures/            # Shared test fixtures
│   ├── images/          # Input test images
│   └── expected/        # Expected dithered outputs
├── docs/                # Shared documentation
└── README.md
```

### Future plans
 - JavaScript implementation
 - Base colors on real e-paper display colors
 - Add an s curve for tone mapping
 - Combine implementations into a single rust implementation with bindings for other languages
