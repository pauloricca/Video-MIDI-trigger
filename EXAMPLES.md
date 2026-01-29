# Example Configuration Files

This directory contains example YAML configuration files for the Video-MIDI Trigger application.

## Trigger Types

The application supports four trigger types:

1. **brightness** - Triggers when average brightness exceeds a threshold
2. **darkness** - Triggers when average brightness falls below a threshold
3. **motion** - Triggers when average pixel difference between frames exceeds a threshold
4. **range** - Continuously sends CC values based on brightness level within a range

## road.yaml

The included `road.yaml` file demonstrates the basic configuration structure with three triggers:

1. **Top Left Trigger** - Monitors the top-left area (10%, 10%) for brightness >= 200
2. **Top Right Trigger** - Monitors the top-right area (85%, 10%) for brightness >= 180  
3. **Bottom Center Trigger** - Monitors the bottom-center area (47.5%, 80%) for brightness >= 150

## motion-test.yaml

Demonstrates the motion trigger type for detecting movement in the video:

1. **Motion Trigger** - Triggers when the average pixel difference between consecutive frames exceeds 10

The motion trigger is useful for detecting movement in specific areas of the video, such as cars passing through an intersection, people walking, or any other moving objects.

## all-triggers.yaml

A comprehensive example showing all four trigger types in a single configuration:

1. **Brightness Trigger** - Top-left area, activates when brightness > 200
2. **Darkness Trigger** - Top-right area, activates when brightness < 50
3. **Motion Trigger** - Center area, activates when pixel difference > 15
4. **Range Trigger** - Bottom-left area, sends CC values based on brightness level

This example is useful for understanding how different trigger types work together and can be configured.

## debounce-throttle-test.yaml

Demonstrates the use of debounce and throttle parameters to control trigger timing:

1. **Global Defaults Trigger** - Uses global debounce (0.5s) and throttle (1.0s) settings
2. **Custom Timing Trigger** - Custom debounce (0.2s) and throttle (2.0s) for motion detection
3. **Immediate Response Trigger** - Debounce and throttle disabled (0s) for instant response

**Debounce**: Prevents triggers from deactivating too quickly. When a trigger becomes invalid, it waits this duration before sending Note OFF. Useful for preventing flickering.

**Throttle**: Prevents triggers from reactivating too quickly. After deactivation, the trigger waits this duration before it can reactivate. Useful for preventing rapid retriggering.

Both parameters can be set globally (affecting all triggers) and overridden per-trigger. They work with brightness, darkness, and motion trigger types.

## variable-velocity-test.yaml

Demonstrates variable velocity based on detected values:

1. **Motion Variable Velocity** - Velocity changes based on motion intensity (subtle motion → soft velocity, strong motion → loud velocity)
2. **Brightness Variable Velocity** - Velocity scales with brightness level
3. **Fixed Velocity** - Traditional fixed velocity for comparison

**Variable Velocity Format:**
```yaml
velocity:
  min: [detected_value, velocity_value]  # e.g., [2, 80]
  max: [detected_value, velocity_value]  # e.g., [20, 127]
```

The first value in each array is the detected brightness/motion/darkness value, and the second is the MIDI velocity to use. Values are interpolated linearly between min and max, and clamped outside the range.

This is particularly useful for:
- **Motion triggers**: Louder notes for more vigorous movement
- **Brightness triggers**: Velocity matching light intensity
- Creating more expressive and dynamic MIDI performances

## Creating Your Own Configuration

To create a custom configuration:

1. Copy `road.yaml` to a new file (e.g., `myconfig.yaml`)
2. Update the `source` to point to your video file (or set it to `"camera"`)
3. (Optional) Add a `camera` block to set width/height/fps when using the webcam
3. Define your triggers with appropriate positions and thresholds
4. Run with: `python video-midi-trigger.py myconfig`

## Testing Without a Video File

If you don't have a video file yet, you can create a simple test video using OpenCV:

```python
import cv2
import numpy as np

# Create a 30-second test video with moving white circle
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('test_video.mp4', fourcc, 30.0, (640, 480))

for i in range(900):  # 30 seconds at 30fps
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw a moving circle
    x = int(320 + 250 * np.sin(i * 0.02))
    y = int(240 + 150 * np.cos(i * 0.03))
    cv2.circle(frame, (x, y), 30, (255, 255, 255), -1)
    out.write(frame)

out.release()
print("Test video created: test_video.mp4")
```

Then update your YAML file to use `test_video.mp4` as the video path.
