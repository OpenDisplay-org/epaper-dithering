/**
 * Dithering algorithm modes
 * Values match firmware conventions (0-8)
 */
export enum DitherMode {
  NONE = 0,
  BURKES = 1,
  ORDERED = 2,
  FLOYD_STEINBERG = 3,
  ATKINSON = 4,
  STUCKI = 5,
  SIERRA = 6,
  SIERRA_LITE = 7,
  JARVIS_JUDICE_NINKE = 8,
}