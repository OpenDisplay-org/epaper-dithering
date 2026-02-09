import type { RGB, ColorPalette } from './types';

/**
 * E-paper display color schemes
 * Values match firmware conventions (0-5)
 */
export enum ColorScheme {
  MONO = 0,
  BWR = 1,
  BWY = 2,
  BWRY = 3,
  BWGBRY = 4,
  GRAYSCALE_4 = 5,
}

const PALETTES: Record<ColorScheme, ColorPalette> = {
  [ColorScheme.MONO]: {
    colors: {
      black: { r: 0, g: 0, b: 0 },
      white: { r: 255, g: 255, b: 255 },
    },
    accent: 'black',
  },
  [ColorScheme.BWR]: {
    colors: {
      black: { r: 0, g: 0, b: 0 },
      white: { r: 255, g: 255, b: 255 },
      red: { r: 255, g: 0, b: 0 },
    },
    accent: 'red',
  },
  [ColorScheme.BWY]: {
    colors: {
      black: { r: 0, g: 0, b: 0 },
      white: { r: 255, g: 255, b: 255 },
      yellow: { r: 255, g: 255, b: 0 },
    },
    accent: 'yellow',
  },
  [ColorScheme.BWRY]: {
    colors: {
      black: { r: 0, g: 0, b: 0 },
      white: { r: 255, g: 255, b: 255 },
      yellow: { r: 255, g: 255, b: 0 },
      red: { r: 255, g: 0, b: 0 },
    },
    accent: 'red',
  },
  [ColorScheme.BWGBRY]: {
    colors: {
      black: { r: 0, g: 0, b: 0 },
      white: { r: 255, g: 255, b: 255 },
      yellow: { r: 255, g: 255, b: 0 },
      red: { r: 255, g: 0, b: 0 },
      blue: { r: 0, g: 0, b: 255 },
      green: { r: 0, g: 255, b: 0 },
    },
    accent: 'red',
  },
  [ColorScheme.GRAYSCALE_4]: {
    colors: {
      black: { r: 0, g: 0, b: 0 },
      gray1: { r: 85, g: 85, b: 85 },
      gray2: { r: 170, g: 170, b: 170 },
      white: { r: 255, g: 255, b: 255 },
    },
    accent: 'black',
  },
};

/**
 * Get color palette for a color scheme
 */
export function getPalette(scheme: ColorScheme): ColorPalette {
  return PALETTES[scheme];
}

/**
 * Get number of colors in a color scheme
 */
export function getColorCount(scheme: ColorScheme): number {
  return Object.keys(PALETTES[scheme].colors).length;
}

/**
 * Create ColorScheme from firmware integer value
 */
export function fromValue(value: number): ColorScheme {
  if (value < 0 || value > 5) {
    throw new Error(`Invalid color scheme value: ${value}`);
  }
  return value as ColorScheme;
}