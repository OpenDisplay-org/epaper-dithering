# @opendisplay/epaper-dithering

High-quality dithering algorithms for e-paper/e-ink displays, implemented in TypeScript. Works in both browser and Node.js environments.

## Features

- **9 Dithering Algorithms**: From fast ordered dithering to high-quality error diffusion
- **6 Color Schemes**: MONO, BWR, BWY, BWRY, BWGBRY (Spectra 6), GRAYSCALE_4
- **Universal**: Works in browser (Canvas API) and Node.js (with sharp/jimp)
- **Zero Dependencies**: Pure TypeScript, no image library dependencies
- **Fast**: Optimized typed array operations
- **Type-Safe**: Full TypeScript support with exported types

## Installation

```bash
npm install @opendisplay/epaper-dithering
# or
bun add @opendisplay/epaper-dithering
# or
yarn add @opendisplay/epaper-dithering
```

## Quick Start

### Browser (Canvas API)

```typescript
import { ditherImage, ColorScheme, DitherMode } from '@opendisplay/epaper-dithering';

// Load image
const img = new Image();
img.src = 'photo.jpg';
await img.decode();

// Convert to ImageBuffer
const canvas = document.createElement('canvas');
canvas.width = img.width;
canvas.height = img.height;
const ctx = canvas.getContext('2d')!;
ctx.drawImage(img, 0, 0);
const imageData = ctx.getImageData(0, 0, img.width, img.height);

const imageBuffer = {
  width: imageData.width,
  height: imageData.height,
  data: imageData.data,
};

// Dither
const dithered = ditherImage(
  imageBuffer,
  ColorScheme.BWR,
  DitherMode.FLOYD_STEINBERG
);

// Render result
const resultCanvas = document.createElement('canvas');
resultCanvas.width = dithered.width;
resultCanvas.height = dithered.height;
const resultCtx = resultCanvas.getContext('2d')!;
const resultData = resultCtx.createImageData(dithered.width, dithered.height);

for (let i = 0; i < dithered.indices.length; i++) {
  const color = dithered.palette[dithered.indices[i]];
  resultData.data[i * 4] = color.r;
  resultData.data[i * 4 + 1] = color.g;
  resultData.data[i * 4 + 2] = color.b;
  resultData.data[i * 4 + 3] = 255;
}

resultCtx.putImageData(resultData, 0, 0);
document.body.appendChild(resultCanvas);
```

### Node.js (with sharp)

```typescript
import sharp from 'sharp';
import { ditherImage, ColorScheme, DitherMode } from '@opendisplay/epaper-dithering';

// Load image
const { data, info } = await sharp('photo.jpg')
  .ensureAlpha()
  .raw()
  .toBuffer({ resolveWithObject: true });

const imageBuffer = {
  width: info.width,
  height: info.height,
  data: new Uint8ClampedArray(data),
};

// Dither
const dithered = ditherImage(imageBuffer, ColorScheme.BWR, DitherMode.BURKES);

// Convert back to RGBA
const rgbaBuffer = Buffer.alloc(dithered.width * dithered.height * 4);
for (let i = 0; i < dithered.indices.length; i++) {
  const color = dithered.palette[dithered.indices[i]];
  rgbaBuffer[i * 4] = color.r;
  rgbaBuffer[i * 4 + 1] = color.g;
  rgbaBuffer[i * 4 + 2] = color.b;
  rgbaBuffer[i * 4 + 3] = 255;
}

// Save
await sharp(rgbaBuffer, {
  raw: {
    width: dithered.width,
    height: dithered.height,
    channels: 4,
  },
})
  .png()
  .toFile('dithered.png');
```

## API Reference

### `ditherImage(image, colorScheme, mode?)`

Apply dithering algorithm to image for e-paper display.

**Parameters:**
- `image: ImageBuffer` - Input image in RGBA format
- `colorScheme: ColorScheme` - Target e-paper color scheme
- `mode?: DitherMode` - Dithering algorithm (default: `DitherMode.BURKES`)

**Returns:** `PaletteImageBuffer` - Palette-indexed image with color information

### Color Schemes

```typescript
enum ColorScheme {
  MONO = 0,          // Black & White (2 colors)
  BWR = 1,           // Black, White, Red (3 colors)
  BWY = 2,           // Black, White, Yellow (3 colors)
  BWRY = 3,          // Black, White, Red, Yellow (4 colors)
  BWGBRY = 4,        // Black, White, Green, Blue, Red, Yellow (6 colors)
  GRAYSCALE_4 = 5,   // 4-level grayscale
}
```

### Dither Modes

```typescript
enum DitherMode {
  NONE = 0,                  // No dithering (direct palette mapping)
  BURKES = 1,                // Burkes (default - good quality/speed balance)
  ORDERED = 2,               // Ordered (4×4 Bayer matrix - fast)
  FLOYD_STEINBERG = 3,       // Floyd-Steinberg (most popular)
  ATKINSON = 4,              // Atkinson (classic Macintosh style)
  STUCKI = 5,                // Stucki (high quality)
  SIERRA = 6,                // Sierra (high quality)
  SIERRA_LITE = 7,           // Sierra Lite (fast)
  JARVIS_JUDICE_NINKE = 8,   // Jarvis-Judice-Ninke (highest quality, slowest)
}
```

## Algorithm Comparison

| Algorithm | Quality | Speed | Use Case |
|-----------|---------|-------|----------|
| NONE | Lowest | Fastest | Testing, solid colors |
| ORDERED | Low | Very Fast | Simple images, patterns |
| SIERRA_LITE | Medium | Fast | Quick previews |
| BURKES | Good | Medium | **Default - best balance** |
| FLOYD_STEINBERG | Good | Medium | Popular choice, smooth gradients |
| ATKINSON | Good | Medium | Classic retro aesthetic |
| SIERRA | High | Medium | Detailed images |
| STUCKI | Very High | Slow | Photos, high detail |
| JARVIS_JUDICE_NINKE | Highest | Slowest | Maximum quality |

## Types

```typescript
interface RGB {
  r: number; // 0-255
  g: number; // 0-255
  b: number; // 0-255
}

interface ImageBuffer {
  width: number;
  height: number;
  data: Uint8ClampedArray; // RGBA format
}

interface PaletteImageBuffer {
  width: number;
  height: number;
  indices: Uint8Array;      // Palette index per pixel
  palette: RGB[];           // Available colors
}

interface ColorPalette {
  readonly colors: Record<string, RGB>;
  readonly accent: string;
}
```

## Helper Functions

### `getPalette(scheme: ColorScheme): ColorPalette`

Get color palette for a color scheme.

### `getColorCount(scheme: ColorScheme): number`

Get number of colors in a color scheme.

### `fromValue(value: number): ColorScheme`

Create ColorScheme from firmware integer value (0-5).

## Performance

Expected performance on an 800×600 image:
- **ORDERED**: ~50ms
- **SIERRA_LITE**: ~100ms
- **BURKES/FLOYD_STEINBERG**: ~150ms
- **SIERRA/ATKINSON**: ~200ms
- **STUCKI/JARVIS**: ~300ms

Performance varies by device and JavaScript engine.

## Related Projects

- **Python**: [`epaper-dithering`](https://pypi.org/project/epaper-dithering/) - Python implementation
- **OpenDisplay**: [`py-opendisplay`](https://github.com/OpenDisplay-org/py-opendisplay) - Python library for OpenDisplay BLE Devices