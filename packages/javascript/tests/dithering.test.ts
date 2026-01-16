import { describe, it, expect } from 'vitest';
import {
  ditherImage,
  DitherMode,
  ColorScheme,
  getPalette,
  getColorCount,
  fromValue,
} from '../src';
import { createTestImage, createGradient } from './fixtures';

describe('Dithering Algorithms', () => {
  it.each(Object.values(DitherMode).filter((v) => typeof v === 'number'))(
    'produces valid output for mode %s',
    (mode) => {
      const image = createTestImage(10, 10, { r: 128, g: 128, b: 128 });
      const result = ditherImage(image, ColorScheme.BWR, mode as DitherMode);

      expect(result.width).toBe(10);
      expect(result.height).toBe(10);
      expect(result.indices.length).toBe(100);
      expect(result.palette.length).toBe(3);
    }
  );

  it.each(Object.values(ColorScheme).filter((v) => typeof v === 'number'))(
    'works with color scheme %s',
    (scheme) => {
      const image = createTestImage(10, 10, { r: 128, g: 128, b: 128 });
      const result = ditherImage(
        image,
        scheme as ColorScheme,
        DitherMode.BURKES
      );

      expect(result.palette.length).toBeGreaterThan(0);
    }
  );

  it('handles RGBA input correctly', () => {
    const image = createTestImage(10, 10, { r: 128, g: 128, b: 128 });
    const result = ditherImage(image, ColorScheme.BWR, DitherMode.BURKES);

    expect(result).toBeDefined();
    expect(result.width).toBe(10);
    expect(result.height).toBe(10);
  });

  it('produces different output for different algorithms', () => {
    const image = createGradient(100, 100);

    const burkes = ditherImage(image, ColorScheme.MONO, DitherMode.BURKES);
    const floydSteinberg = ditherImage(
      image,
      ColorScheme.MONO,
      DitherMode.FLOYD_STEINBERG
    );

    // Results should be different (different error diffusion patterns)
    let differences = 0;
    for (let i = 0; i < burkes.indices.length; i++) {
      if (burkes.indices[i] !== floydSteinberg.indices[i]) {
        differences++;
      }
    }

    expect(differences).toBeGreaterThan(0);
  });

  it('default mode is BURKES', () => {
    const image = createTestImage(10, 10, { r: 128, g: 128, b: 128 });

    const withDefault = ditherImage(image, ColorScheme.BWR);
    const withBurkes = ditherImage(image, ColorScheme.BWR, DitherMode.BURKES);

    expect(withDefault.indices).toEqual(withBurkes.indices);
  });
});

describe('ColorScheme', () => {
  it('has correct color counts', () => {
    expect(getColorCount(ColorScheme.MONO)).toBe(2);
    expect(getColorCount(ColorScheme.BWR)).toBe(3);
    expect(getColorCount(ColorScheme.BWY)).toBe(3);
    expect(getColorCount(ColorScheme.BWRY)).toBe(4);
    expect(getColorCount(ColorScheme.BWGBRY)).toBe(6);
    expect(getColorCount(ColorScheme.GRAYSCALE_4)).toBe(4);
  });

  it('fromValue works correctly', () => {
    expect(fromValue(0)).toBe(ColorScheme.MONO);
    expect(fromValue(1)).toBe(ColorScheme.BWR);
    expect(() => fromValue(99)).toThrow();
  });

  it('palette colors are valid RGB', () => {
    for (const scheme of Object.values(ColorScheme).filter(
      (v) => typeof v === 'number'
    )) {
      const palette = getPalette(scheme as ColorScheme);
      for (const color of Object.values(palette.colors)) {
        expect(color.r).toBeGreaterThanOrEqual(0);
        expect(color.r).toBeLessThanOrEqual(255);
        expect(color.g).toBeGreaterThanOrEqual(0);
        expect(color.g).toBeLessThanOrEqual(255);
        expect(color.b).toBeGreaterThanOrEqual(0);
        expect(color.b).toBeLessThanOrEqual(255);
      }
    }
  });

  it('palettes have correct accent colors', () => {
    expect(getPalette(ColorScheme.MONO).accent).toBe('black');
    expect(getPalette(ColorScheme.BWR).accent).toBe('red');
    expect(getPalette(ColorScheme.BWY).accent).toBe('yellow');
    expect(getPalette(ColorScheme.BWRY).accent).toBe('red');
    expect(getPalette(ColorScheme.BWGBRY).accent).toBe('red');
    expect(getPalette(ColorScheme.GRAYSCALE_4).accent).toBe('black');
  });
});

describe('DitherMode', () => {
  it('has all expected modes', () => {
    expect(DitherMode.NONE).toBe(0);
    expect(DitherMode.BURKES).toBe(1);
    expect(DitherMode.ORDERED).toBe(2);
    expect(DitherMode.FLOYD_STEINBERG).toBe(3);
    expect(DitherMode.ATKINSON).toBe(4);
    expect(DitherMode.STUCKI).toBe(5);
    expect(DitherMode.SIERRA).toBe(6);
    expect(DitherMode.SIERRA_LITE).toBe(7);
    expect(DitherMode.JARVIS_JUDICE_NINKE).toBe(8);
  });
});