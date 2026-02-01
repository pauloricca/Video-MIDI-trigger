# Visual Feedback in Creation Mode

## Overview
When you press 'c' to enter creation mode and start clicking to add points, you'll see real-time visual feedback on the video window.

## Visual Elements

### Points (Circles)
- **First Point** (Start of shape):
  - Green filled circle (8px radius)
  - White border (2px)
  - Larger than other points to indicate it's the starting point

- **Subsequent Points**:
  - Yellow filled circles (6px radius)
  - White border (2px)
  - Slightly smaller than the first point

### Lines
- **Connecting Lines** (between consecutive points):
  - Yellow color `(0, 255, 255)` in BGR
  - 2px thickness
  - Connects each point to the next in sequence

- **Closure Line** (only shown when 3+ points exist):
  - Yellow color `(0, 255, 255)` in BGR
  - 1px thickness (thinner than connecting lines)
  - Connects the last point back to the first point
  - Shows you what the final closed shape will look like

## Example Progression

### After 1 Click:
```
● (Green circle at first click location)
```

### After 2 Clicks:
```
● ────── ● 
(Green)    (Yellow)
```
Yellow line connects the two points

### After 3 Clicks:
```
    ●
   ╱ ╲
  ╱   ╲
 ●─────●
```
- Green circle at first point
- Yellow circles at second and third points
- Yellow lines connecting all three
- Thin yellow line closing the triangle

### After 4+ Clicks:
```
  ●─────●
  │     │
  │     │
  ●─────●
```
- Green circle at first point
- Yellow circles at all other points
- Yellow lines connecting consecutive points
- Thin yellow line from last back to first

## Color Reference (BGR format)
- Yellow: `(0, 255, 255)`
- Green: `(0, 255, 0)`
- White: `(255, 255, 255)`

## Usage Flow
1. Press 'c' to enter creation mode
2. See console message: "=== CREATION MODE ==="
3. Click on video to add points
4. Watch as each point appears with a circle
5. See lines automatically drawn between points
6. When you have 3+ points, see the closure line
7. Press BACKSPACE to remove the last point (visual feedback updates)
8. Press ENTER to save the trigger

## Visual Overlay Drawing Order
1. All regular triggers are drawn first
2. Creation mode overlay is drawn on top
3. This ensures your new shape is always visible above existing triggers

## Technical Notes
- Points are converted from percentage coordinates to pixel coordinates for drawing
- The overlay is redrawn every frame, so it moves/scales with the video
- All drawing happens in `_draw_creation_overlay()` method
- Called from `process_frame()` when `creation_mode` is True and points exist
