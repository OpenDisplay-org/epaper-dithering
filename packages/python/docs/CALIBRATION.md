# E-Paper Display Color Calibration Guide

This guide explains how to measure the actual RGB values of your e-paper display for accurate dithering results.

## Why Measure Your Display?

E-paper displays use reflective technology, making their colors significantly darker than pure RGB values:

- **Pure RGB assumption**: White=(255,255,255), Red=(255,0,0)
- **Reality**: White≈(180-200), Red≈(115-125) — **30-87% darker**

Using measured values ensures dithered images match your display's actual appearance.

## Measurement Methods

### Method 1: Camera Calibration (Recommended)

Best balance of accuracy and accessibility. Requires a camera and basic photo editing software.

#### Equipment Needed
- Camera or smartphone with manual exposure control
- Photo editing software (Photoshop, GIMP, Preview, etc.)
- White reference card (optional but recommended)
- Consistent lighting environment (daylight 6500K recommended)

#### Procedure

1. **Prepare Display**
   - Display full-screen color patches on your e-paper display
   - Let display fully refresh (wait for refresh to complete)
   - Ensure display is clean (no dust or fingerprints)

2. **Set Up Photography**
   - Place display in consistent, diffuse lighting
   - Avoid direct sunlight or harsh shadows
   - Avoid reflections from light sources
   - Use manual camera settings:
     - ISO: 100-400 (low noise)
     - White balance: Daylight (6500K) or custom
     - Focus: Manual, centered on display

3. **Photograph Each Color**
   - Take photos of each full-screen color patch
   - Fill frame with display (avoid borders/bezels)
   - Take 3-5 photos per color for averaging
   - Ensure consistent camera position and settings

4. **Sample RGB Values**
   - Open photos in editing software
   - Use eyedropper/color picker tool
   - Sample from **center** of display (avoid edges)
   - Take 5-10 samples per color, average the values
   - Avoid pixels near screen edges (may have artifacts)

5. **Average and Record**
   ```
   Color: White
   Samples: (182,185,174), (179,183,171), (181,184,173), (180,182,172), (178,181,170)
   Average: (180, 183, 172)
   ```

#### Tips for Best Results
- Photograph in RAW format if possible (more color accuracy)
- Use gray card for white balance calibration
- Ensure camera is perpendicular to display
- Avoid shadows from yourself or camera
- Take measurements at same time of day (consistent lighting)

### Method 2: Colorimeter (Most Accurate)

Professional method using hardware colorimeter. Best accuracy but requires specialized equipment.

#### Equipment Needed
- X-Rite i1Display, Datacolor SpyderX, or similar colorimeter
- Calibration software (usually included with device)

#### Procedure

1. **Calibrate Colorimeter**
   - Follow manufacturer's calibration procedure
   - Ensure device is clean and working properly

2. **Measure Display**
   - Display full-screen color patches
   - Place colorimeter on center of display
   - Follow software instructions for measurement
   - Record L\*a\*b\* or XYZ values

3. **Convert to sRGB**
   - Most calibration software can export sRGB RGB values
   - If you have L\*a\*b\* or XYZ, convert using standard color space transforms
   - Ensure values are in [0-255] range

### Method 3: Manual Tuning (Iterative)

Visual comparison method. Less accurate but requires no special equipment.

#### Procedure

1. **Start with Reference**
   - Use theoretical values or values from similar displays
   - For your display type, check library's pre-defined constants

2. **Dither Test Image**
   - Use image with known colors (color checker, gradient)
   - Dither with current palette values
   - Display on e-paper

3. **Compare and Adjust**
   - Photograph both dithered output and actual display
   - Compare colors side-by-side
   - Adjust RGB values incrementally:
     - If display is darker: reduce RGB values by 10-20 units
     - If colors are too warm/cool: adjust individual channels
   - Re-dither and test again

4. **Iterate**
   - Repeat until visual match is satisfactory
   - This method typically requires 5-10 iterations per color

## Color Order Requirement

**CRITICAL**: Color names and order MUST match the corresponding `ColorScheme`!

### Example: BWR Scheme

```python
# CORRECT - matches ColorScheme.BWR order
HANSHOW_BWR = ColorPalette(
    colors={
        'black': (5, 5, 5),
        'white': (200, 200, 200),
        'red': (120, 15, 5),
    },
    accent='red'
)

# WRONG - reordered colors will break encoding!
HANSHOW_BWR_WRONG = ColorPalette(
    colors={
        'white': (200, 200, 200),  # ❌ Wrong order
        'black': (5, 5, 5),          # ❌ Wrong order
        'red': (120, 15, 5),
    },
    accent='red'
)
```

### Checking Color Order

To verify your palette order matches the reference scheme:

```python
from epaper_dithering import ColorScheme

# Check reference order
scheme = ColorScheme.BWR
print(list(scheme.palette.colors.keys()))
# Output: ['black', 'white', 'red']

# Your measured palette MUST use the same order
```

## Creating Your ColorPalette

Once you have measured RGB values, create a `ColorPalette`:

```python
from epaper_dithering import ColorPalette

# Example: Measured values for a BWR display
my_display = ColorPalette(
    colors={
        'black': (5, 5, 5),           # Measured
        'white': (185, 190, 180),     # Measured
        'red': (120, 15, 5),          # Measured
    },
    accent='red'  # Primary accent color for this scheme
)
```

### Accent Color

The `accent` parameter specifies the primary accent color for the display. This is typically:
- **BWR/BWY**: 'red' or 'yellow'
- **BWRY**: 'red' (most displays)
- **BWGBRY**: 'red' (most common)
- **MONO**: 'black'
- **GRAYSCALE_4**: 'black'

## Using Measured Colors

### Option 1: Direct Use

```python
from epaper_dithering import dither_image, ColorPalette, DitherMode

my_measured = ColorPalette(
    colors={'black': (5,5,5), 'white': (180,180,170), 'red': (115,12,2)},
    accent='red'
)

result = dither_image(image, my_measured, DitherMode.FLOYD_STEINBERG)
```

### Option 2: Add to Library

Edit `src/epaper_dithering/palettes.py` and add your constant:

```python
# At end of file
MY_DISPLAY = ColorPalette(
    colors={
        'black': (5, 5, 5),
        'white': (185, 190, 180),
        'red': (120, 15, 5),
    },
    accent='red'
)
```

Then export in `__init__.py`:

```python
from .palettes import (
    # ... existing imports
    MY_DISPLAY,  # Add this
)

__all__ = [
    # ... existing exports
    "MY_DISPLAY",  # Add this
]
```

Now you can use it like any built-in palette:

```python
from epaper_dithering import dither_image, MY_DISPLAY
result = dither_image(image, MY_DISPLAY)
```

## Validation

### Visual Check

1. Dither a test image with your measured palette
2. Display on e-paper
3. Photograph the display
4. Compare dithered image to photograph — they should match closely

### Sanity Checks

```python
# All RGB values should be 0-255
assert all(0 <= c <= 255 for rgb in palette.colors.values() for c in rgb)

# Real displays are darker than pure RGB
# White should be < 255
assert palette.colors['white'][0] < 255

# Black might be slightly above 0 (LCD backlight bleed)
# But typically very close to 0
assert palette.colors['black'][0] < 20

# Colored pixels are typically much darker than pure RGB
# E.g., Red (255,0,0) becomes (115-125, 10-20, 0-10)
```

## Common Issues

### Colors Too Dark/Light

- **Too dark**: Your lighting was too dim during photography
  - Solution: Re-photograph in brighter, more consistent lighting
  - Or: Increase measured RGB values by 10-15% across all channels

- **Too light**: Display wasn't fully refreshed or camera overexposed
  - Solution: Ensure display completes full refresh before photographing
  - Reduce camera exposure or ISO

### Color Cast (Tint)

- **Too warm** (yellowish): White balance issue
  - Solution: Use daylight white balance (6500K)
  - Or: Adjust blue channel upward

- **Too cool** (bluish): Opposite of above
  - Solution: Adjust red/yellow channels upward

### Inconsistent Results

- **Different values each time**: Lighting inconsistency
  - Solution: Always measure in the same location/time
  - Use controlled lighting if possible

## Example Measurements

### Reference: Waveshare 7.3" F (from esp32-photoframe)

```python
WAVESHARE_7_3_F_REFERENCE = ColorPalette(
    colors={
        'black': (2, 2, 2),
        'white': (179, 182, 171),
        'yellow': (201, 184, 0),
        'red': (117, 10, 0),
        'blue': (0, 47, 107),
        'green': (33, 69, 40),
    },
    accent='red'
)
```

**Note**: Your display of the same model may vary by ±10-20 RGB units due to manufacturing tolerances and aging.

## Contributing Your Measurements

If you've measured your display and want to contribute to the library:

1. See bottom of `palettes.py`
2. Submit a pull request or open an issue on GitHub with your data
3. Help other users with the same display!

## References

### Color Science Standards
- [IEC 61966-2-1 (sRGB standard)](https://en.wikipedia.org/wiki/SRGB)
- [ColorChecker Reference](https://en.wikipedia.org/wiki/ColorChecker)
- [Digital Color Management (Book)](https://www.wiley.com/en-us/Digital+Color+Management%3A+Encoding+Solutions%2C+2nd+Edition-p-9780470512449)

### Measurement Methodology
This calibration guide draws heavily from the excellent work by the e-paper community:

- **[esp32-photoframe](https://github.com/aitjcize/esp32-photoframe)** by [@aitjcize](https://github.com/aitjcize)
  - [Measured Palette Documentation](https://raw.githubusercontent.com/aitjcize/esp32-photoframe/refs/heads/main/docs/MEASURED_PALETTE.md)
  - Pioneer in measuring actual e-paper display colors
  - Camera calibration methodology and reference values
  - Real-world measurements for Waveshare 7.3" 7-color displays