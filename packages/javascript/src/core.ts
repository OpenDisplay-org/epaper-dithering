import type { ImageBuffer, PaletteImageBuffer } from './types';
import { DitherMode } from './enums';
import { ColorScheme } from './palettes';
import * as algorithms from './algorithms';

/**
 * Apply dithering algorithm to image for e-paper display
 *
 * @param image - Input image buffer (RGBA format)
 * @param colorScheme - Target e-paper color scheme
 * @param mode - Dithering algorithm (default: BURKES)
 * @returns Palette-indexed image buffer
 *
 * @example
 * ```typescript
 * const dithered = ditherImage(imageBuffer, ColorScheme.BWR, DitherMode.FLOYD_STEINBERG);
 * ```
 */
export function ditherImage(
  image: ImageBuffer,
  colorScheme: ColorScheme,
  mode: DitherMode = DitherMode.BURKES
): PaletteImageBuffer {
  switch (mode) {
    case DitherMode.NONE:
      return algorithms.directPaletteMap(image, colorScheme);
    case DitherMode.ORDERED:
      return algorithms.orderedDither(image, colorScheme);
    case DitherMode.FLOYD_STEINBERG:
      return algorithms.floydSteinbergDither(image, colorScheme);
    case DitherMode.ATKINSON:
      return algorithms.atkinsonDither(image, colorScheme);
    case DitherMode.STUCKI:
      return algorithms.stuckiDither(image, colorScheme);
    case DitherMode.SIERRA:
      return algorithms.sierraDither(image, colorScheme);
    case DitherMode.SIERRA_LITE:
      return algorithms.sierraLiteDither(image, colorScheme);
    case DitherMode.JARVIS_JUDICE_NINKE:
      return algorithms.jarvisJudiceNinkeDither(image, colorScheme);
    case DitherMode.BURKES:
    default:
      return algorithms.burkesDither(image, colorScheme);
  }
}