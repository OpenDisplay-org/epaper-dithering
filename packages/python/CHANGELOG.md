# Changelog

## [0.3.0](https://github.com/OpenDisplay-org/epaper-dithering/compare/python-v0.2.0...python-v0.3.0) (2026-02-02)


### ⚠ BREAKING CHANGES

* Dithering output has changed due to color science improvements:
    - All algorithms now work in linear RGB space with IEC 61966-2-1 sRGB gamma correction
    - Color matching uses ITU-R BT.601 perceptual luma weighting instead of Euclidean distance
    - RGBA images now composite on white background (e-paper assumption) instead of black
    - Ordered dithering completely rewritten to fix broken 0-240 bias bug

### Features

* implement reference-quality color science for dithering ([e151fbf](https://github.com/OpenDisplay-org/epaper-dithering/commit/e151fbfd836176e32adf9a290f55d242167def82))

## [0.2.0](https://github.com/OpenDisplay-org/epaper-dithering/compare/python-v0.1.0...python-v0.2.0) (2026-01-16)


### ⚠ BREAKING CHANGES

* initial release with dithering algorithms for e-paper displays

### Features

* initial release with dithering algorithms for e-paper displays ([03a5b4e](https://github.com/OpenDisplay-org/epaper-dithering/commit/03a5b4e59f5b3531b7607478f6ab6cc097a7feab))

## 0.1.0 (2026-01-11)


### ⚠ BREAKING CHANGES

* initial release with dithering algorithms for e-paper displays

### Features

* initial release with dithering algorithms for e-paper displays ([03a5b4e](https://github.com/OpenDisplay-org/epaper-dithering/commit/03a5b4e59f5b3531b7607478f6ab6cc097a7feab))
