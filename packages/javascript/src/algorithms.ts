import type { RGB, ImageBuffer, PaletteImageBuffer } from './types';
import { ColorScheme, getPalette } from './palettes';

/**
 * Get RGB palette colors from color scheme
 */
export function getPaletteColors(scheme: ColorScheme): RGB[] {
  const palette = getPalette(scheme);
  return Object.values(palette.colors);
}

/**
 * Find closest palette color using Euclidean distance
 */
export function findClosestPaletteColor(rgb: RGB, palette: RGB[]): number {
  let minDistance = Infinity;
  let closestIdx = 0;

  for (let i = 0; i < palette.length; i++) {
    const pal = palette[i];
    // Euclidean distance in RGB space
    const distance =
      (rgb.r - pal.r) ** 2 + (rgb.g - pal.g) ** 2 + (rgb.b - pal.b) ** 2;

    if (distance < minDistance) {
      minDistance = distance;
      closestIdx = i;
    }
  }

  return closestIdx;
}

/**
 * Error diffusion kernel entry
 */
interface ErrorKernel {
  dx: number;
  dy: number;
  weight: number;
}

/**
 * Apply error diffusion dithering with specified kernel
 */
function errorDiffusionDither(
  image: ImageBuffer,
  colorScheme: ColorScheme,
  kernel: ErrorKernel[]
): PaletteImageBuffer {
  const { width, height } = image;
  const palette = getPaletteColors(colorScheme);

  // Convert RGBA to RGB float array for error accumulation
  const pixels = new Float32Array(width * height * 3);
  for (let i = 0; i < width * height; i++) {
    pixels[i * 3] = image.data[i * 4]; // R
    pixels[i * 3 + 1] = image.data[i * 4 + 1]; // G
    pixels[i * 3 + 2] = image.data[i * 4 + 2]; // B
  }

  const indices = new Uint8Array(width * height);

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = y * width + x;
      const pixelIdx = idx * 3;

      // Get old pixel (truncate, no clamping - matches Python behavior)
      const oldPixel: RGB = {
        r: Math.trunc(pixels[pixelIdx]),
        g: Math.trunc(pixels[pixelIdx + 1]),
        b: Math.trunc(pixels[pixelIdx + 2]),
      };

      // Find closest palette color
      const newIdx = findClosestPaletteColor(oldPixel, palette);
      const newPixel = palette[newIdx];
      indices[idx] = newIdx;

      // Calculate quantization error
      const errorR = oldPixel.r - newPixel.r;
      const errorG = oldPixel.g - newPixel.g;
      const errorB = oldPixel.b - newPixel.b;

      // Distribute error to neighbors using kernel
      for (const { dx, dy, weight } of kernel) {
        const nx = x + dx;
        const ny = y + dy;

        if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
          const neighborIdx = (ny * width + nx) * 3;
          pixels[neighborIdx] += errorR * weight;
          pixels[neighborIdx + 1] += errorG * weight;
          pixels[neighborIdx + 2] += errorB * weight;
        }
      }
    }
  }

  return { width, height, indices, palette };
}

/**
 * Direct palette mapping without dithering (NONE)
 */
export function directPaletteMap(
  image: ImageBuffer,
  colorScheme: ColorScheme
): PaletteImageBuffer {
  const { width, height } = image;
  const palette = getPaletteColors(colorScheme);
  const indices = new Uint8Array(width * height);

  for (let i = 0; i < width * height; i++) {
    const rgb: RGB = {
      r: image.data[i * 4],
      g: image.data[i * 4 + 1],
      b: image.data[i * 4 + 2],
    };
    indices[i] = findClosestPaletteColor(rgb, palette);
  }

  return { width, height, indices, palette };
}

/**
 * Ordered dithering using 4x4 Bayer matrix
 */
export function orderedDither(
  image: ImageBuffer,
  colorScheme: ColorScheme
): PaletteImageBuffer {
  const bayerMatrix = new Uint8Array([
    0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5,
  ]).map((v) => v * 16);

  const { width, height } = image;
  const palette = getPaletteColors(colorScheme);
  const indices = new Uint8Array(width * height);

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = y * width + x;
      const dataIdx = idx * 4;

      // Get threshold from Bayer matrix
      const threshold = bayerMatrix[(y % 4) * 4 + (x % 4)];

      // Add threshold noise (clamp to 0-255 like Python's np.clip)
      const rgb: RGB = {
        r: Math.max(0, Math.min(255, Math.trunc(image.data[dataIdx] + threshold))),
        g: Math.max(0, Math.min(255, Math.trunc(image.data[dataIdx + 1] + threshold))),
        b: Math.max(0, Math.min(255, Math.trunc(image.data[dataIdx + 2] + threshold))),
      };

      indices[idx] = findClosestPaletteColor(rgb, palette);
    }
  }

  return { width, height, indices, palette };
}

/**
 * Burkes dithering (divisor 200)
 * Kernel:
 *          X  32  12
 *   5  12  26  12   5
 */
export function burkesDither(
  image: ImageBuffer,
  colorScheme: ColorScheme
): PaletteImageBuffer {
  const kernel: ErrorKernel[] = [
    { dx: 1, dy: 0, weight: 32 / 200 },
    { dx: 2, dy: 0, weight: 12 / 200 },
    { dx: -2, dy: 1, weight: 5 / 200 },
    { dx: -1, dy: 1, weight: 12 / 200 },
    { dx: 0, dy: 1, weight: 26 / 200 },
    { dx: 1, dy: 1, weight: 12 / 200 },
    { dx: 2, dy: 1, weight: 5 / 200 },
  ];

  return errorDiffusionDither(image, colorScheme, kernel);
}

/**
 * Floyd-Steinberg dithering (divisor 16)
 * Most popular error diffusion algorithm
 * Kernel:
 *      X   7
 *  3   5   1
 */
export function floydSteinbergDither(
  image: ImageBuffer,
  colorScheme: ColorScheme
): PaletteImageBuffer {
  const kernel: ErrorKernel[] = [
    { dx: 1, dy: 0, weight: 7 / 16 },
    { dx: -1, dy: 1, weight: 3 / 16 },
    { dx: 0, dy: 1, weight: 5 / 16 },
    { dx: 1, dy: 1, weight: 1 / 16 },
  ];

  return errorDiffusionDither(image, colorScheme, kernel);
}

/**
 * Sierra dithering (divisor 32)
 * Kernel:
 *          X   5   3
 *   2   4   5   4   2
 *       2   3   2
 */
export function sierraDither(
  image: ImageBuffer,
  colorScheme: ColorScheme
): PaletteImageBuffer {
  const kernel: ErrorKernel[] = [
    { dx: 1, dy: 0, weight: 5 / 32 },
    { dx: 2, dy: 0, weight: 3 / 32 },
    { dx: -2, dy: 1, weight: 2 / 32 },
    { dx: -1, dy: 1, weight: 4 / 32 },
    { dx: 0, dy: 1, weight: 5 / 32 },
    { dx: 1, dy: 1, weight: 4 / 32 },
    { dx: 2, dy: 1, weight: 2 / 32 },
    { dx: -1, dy: 2, weight: 2 / 32 },
    { dx: 0, dy: 2, weight: 3 / 32 },
    { dx: 1, dy: 2, weight: 2 / 32 },
  ];

  return errorDiffusionDither(image, colorScheme, kernel);
}

/**
 * Sierra Lite dithering (divisor 4)
 * Fastest error diffusion algorithm
 * Kernel:
 *     X   2
 * 1   1
 */
export function sierraLiteDither(
  image: ImageBuffer,
  colorScheme: ColorScheme
): PaletteImageBuffer {
  const kernel: ErrorKernel[] = [
    { dx: 1, dy: 0, weight: 2 / 4 },
    { dx: -1, dy: 1, weight: 1 / 4 },
    { dx: 0, dy: 1, weight: 1 / 4 },
  ];

  return errorDiffusionDither(image, colorScheme, kernel);
}

/**
 * Atkinson dithering (divisor 8)
 * Created by Bill Atkinson for original Macintosh
 * Kernel:
 *      X   1   1
 *  1   1   1
 *      1
 */
export function atkinsonDither(
  image: ImageBuffer,
  colorScheme: ColorScheme
): PaletteImageBuffer {
  const kernel: ErrorKernel[] = [
    { dx: 1, dy: 0, weight: 1 / 8 },
    { dx: 2, dy: 0, weight: 1 / 8 },
    { dx: -1, dy: 1, weight: 1 / 8 },
    { dx: 0, dy: 1, weight: 1 / 8 },
    { dx: 1, dy: 1, weight: 1 / 8 },
    { dx: 0, dy: 2, weight: 1 / 8 },
  ];

  return errorDiffusionDither(image, colorScheme, kernel);
}

/**
 * Stucki dithering (divisor 42)
 * High quality error diffusion
 * Kernel:
 *          X   8   4
 *   2   4   8   4   2
 *   1   2   4   2   1
 */
export function stuckiDither(
  image: ImageBuffer,
  colorScheme: ColorScheme
): PaletteImageBuffer {
  const kernel: ErrorKernel[] = [
    { dx: 1, dy: 0, weight: 8 / 42 },
    { dx: 2, dy: 0, weight: 4 / 42 },
    { dx: -2, dy: 1, weight: 2 / 42 },
    { dx: -1, dy: 1, weight: 4 / 42 },
    { dx: 0, dy: 1, weight: 8 / 42 },
    { dx: 1, dy: 1, weight: 4 / 42 },
    { dx: 2, dy: 1, weight: 2 / 42 },
    { dx: -2, dy: 2, weight: 1 / 42 },
    { dx: -1, dy: 2, weight: 2 / 42 },
    { dx: 0, dy: 2, weight: 4 / 42 },
    { dx: 1, dy: 2, weight: 2 / 42 },
    { dx: 2, dy: 2, weight: 1 / 42 },
  ];

  return errorDiffusionDither(image, colorScheme, kernel);
}

/**
 * Jarvis-Judice-Ninke dithering (divisor 48)
 * Highest quality, slowest algorithm
 * Kernel:
 *          X   7   5
 *   3   5   7   5   3
 *   1   3   5   3   1
 */
export function jarvisJudiceNinkeDither(
  image: ImageBuffer,
  colorScheme: ColorScheme
): PaletteImageBuffer {
  const kernel: ErrorKernel[] = [
    { dx: 1, dy: 0, weight: 7 / 48 },
    { dx: 2, dy: 0, weight: 5 / 48 },
    { dx: -2, dy: 1, weight: 3 / 48 },
    { dx: -1, dy: 1, weight: 5 / 48 },
    { dx: 0, dy: 1, weight: 7 / 48 },
    { dx: 1, dy: 1, weight: 5 / 48 },
    { dx: 2, dy: 1, weight: 3 / 48 },
    { dx: -2, dy: 2, weight: 1 / 48 },
    { dx: -1, dy: 2, weight: 3 / 48 },
    { dx: 0, dy: 2, weight: 5 / 48 },
    { dx: 1, dy: 2, weight: 3 / 48 },
    { dx: 2, dy: 2, weight: 1 / 48 },
  ];

  return errorDiffusionDither(image, colorScheme, kernel);
}