# Example Configuration Files

This directory contains example YAML configuration files for the Video-MIDI Trigger application.

## road.yaml

The included `road.yaml` file demonstrates the basic configuration structure with three triggers:

1. **Top Left Trigger** - Monitors the top-left area (10%, 10%) for brightness >= 200
2. **Top Right Trigger** - Monitors the top-right area (85%, 10%) for brightness >= 180  
3. **Bottom Center Trigger** - Monitors the bottom-center area (47.5%, 80%) for brightness >= 150

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
