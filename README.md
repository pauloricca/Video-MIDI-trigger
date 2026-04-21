# Video-MIDI-trigger

A Python application that triggers MIDI messages based on visual events in a video. Monitor specific areas of a video for brightness changes and send corresponding MIDI notes or CC values.

## Features

- Video playback with real-time trigger detection
- **MIDI file recording** - Records all MIDI events to a file for perfect audio-video synchronization
- YAML-based configuration for easy setup
- Multiple trigger areas with independent MIDI mappings
- Brightness-based trigger detection
- Visual feedback with colored overlays
- Automatic video looping
- Virtual MIDI port support

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
uv python install 3.10
uv sync --python 3.10
```

## Usage

Run the application with a configuration file name as an argument:

```bash
uv run python video-midi-trigger.py road
```

This will load the `road.yaml` configuration file and automatically record MIDI events to `road.midi`.

### Command-Line Options

```bash
uv run python video-midi-trigger.py <config_name> [--no-save] [--split-midi-channels]
```

- `config_name`: Name of the configuration file (without .yaml extension)
- `--no-save`: Disable MIDI file recording (only send real-time MIDI)

**Examples:**

```bash
# Normal usage - records MIDI to file
uv run python video-midi-trigger.py myproject

# Disable MIDI file recording - only real-time MIDI output
uv run python video-midi-trigger.py myproject --no-save
uv run python video-midi-trigger.py myproject --split-midi-channels
```

## Configuration

Create a YAML configuration file (e.g., `road.yaml`) with the following structure:

```yaml
source: "path/to/your/video.mp4"
device: "IAC Driver Bus 1"  # Optional global default MIDI device

# Optional: Global defaults for all triggers
debounce: 0.5  # Wait 0.5s before deactivating (prevents flickering)
throttle: 1.0  # Wait 1.0s before allowing reactivation

triggers:
  - name: "Top Left Trigger"
    position:
      x: 10          # X position in percentage (0-100)
      y: 10          # Y position in percentage (0-100)
      width: 5       # Width in percentage
      height: 5      # Height in percentage
    type: "brightness"
    threshold: 200   # Brightness threshold (0-255)
    debounce: 0.3    # Optional: Override global debounce for this trigger
    throttle: 2.0    # Optional: Override global throttle for this trigger
    device: "S-1 MIDI IN"  # Optional: Override MIDI device for this trigger
    midi:
      note: 60       # MIDI note number (0-127)
      velocity: 100  # Fixed velocity (0-127)
      channel: 0     # MIDI channel (0-15)
  
  - name: "Motion Trigger with Variable Velocity"
    position:
      x: 50
      y: 50
      width: 10
      height: 10
    type: "motion"
    threshold: 5
    midi:
      note: 62       # MIDI note number
      velocity:      # Variable velocity based on detected motion
        min: [2, 80]    # Low motion (2) -> low velocity (80)
        max: [20, 127]  # High motion (20) -> high velocity (127)
      channel: 0
  
  # Arbitrary shape trigger using a triangle (shape only - no position)
  - name: "Triangle Area"
    shape:           # Define arbitrary shape with points (x, y in percentage)
      - [25, 25]     # Top vertex
      - [20, 45]     # Bottom left vertex
      - [50, 45]     # Bottom right vertex
    type: "brightness"
    threshold: 180
    midi:
      note: 64
      velocity: 110
      channel: 0
  
  - name: "Difference Trigger"
    position:
      x: 50
      y: 70
      width: 10
      height: 10
    type: "difference"
    threshold: 10
    midi:
      note: 64       # MIDI note number
      velocity: 100
      channel: 0

  - name: "Fixed CC Trigger"
    position:
      x: 30
      y: 70
      width: 10
      height: 10
    type: "brightness"
    threshold: 200
    midi:
      cc: 32
      value: 127
      off_value: 0   # Optional: send on deactivate
      channel: 0
  
  - name: "Difference Range"
    position:
      x: 75
      y: 75
      width: 10
      height: 20
    type: "difference range"
    min: 0     # Minimum difference value
    max: 50    # Maximum difference value
    midi:
      cc: 21
      channel: 0
```

### Configuration Parameters

- **source**: Path to a video file (relative or absolute), a direct video stream URL (`http/https/rtsp/rtmp`), a YouTube URL (`youtube.com` or `youtu.be`), `"camera"` to use the first available camera, or a camera name printed at startup (e.g. `FaceTime HD Camera`)
- **YouTube URLs**: Downloaded automatically via `yt-dlp` to a persistent local cache file (`.youtube-cache/<video_id>.mp4`) and reused on later runs.
- **youtube_cache_dir** (optional): Directory for cached YouTube downloads (default `.youtube-cache`, relative to the YAML file directory).
- **camera** (optional): Settings applied when `source: "camera"`
  - **width**: Camera capture width (default 640)
  - **height**: Camera capture height (default 480)
  - **fps**: Target camera FPS (default 30)
- **mirror** (optional): Mirror the camera image horizontally (default false). Only applies when using a camera source.
- **scale** (optional): Scale the source frame by a ratio (default 1.0). Applies to camera or video sources.
- **overlay** (optional): RGBA overlay applied across the whole video/image source before triggers are drawn, e.g. `[0, 80, 120, 100]`. RGB uses standard RGB ordering; alpha can be `0-255` or `0.0-1.0`.
- **device** (optional): Global default MIDI output device name. Used when a trigger does not specify its own device.
- **debounce** (optional): Global default debounce time in seconds (default 0). Prevents triggers from deactivating too quickly.
- **throttle** (optional): Global default throttle time in seconds (default 0). Prevents triggers from reactivating too quickly.
- **colour** / **color** (optional): Global default trigger display color in RGB. Accepts either `[r, g, b]` or `[[inactive_r, inactive_g, inactive_b], [active_r, active_g, active_b]]`.
- **Live reload**: The app watches the YAML file and reloads trigger values on change. Changing the global `device` or `source` requires a restart to take effect.
- **triggers**: List of trigger definitions
  - **name**: Descriptive name for the trigger
  - **position** OR **shape**: Define the trigger area (mutually exclusive - use one or the other)
    - **position**: Rectangular trigger area (traditional method)
      - **x, y**: Position as percentage of frame dimensions (0-100)
      - **width, height**: Size as percentage of frame dimensions (0-100)
    - **shape**: Arbitrary shape trigger (alternative to position)
      - Array of points `[x, y]` in percentage coordinates (0-100)
      - **1 point**: Single pixel trigger
      - **2 points**: Line trigger
      - **3+ points**: Polygon trigger (filled)
      - Example: `shape: [[25, 25], [20, 45], [50, 45]]` defines a triangle
      - The bounding box is automatically calculated from the shape points
  - **type**: Supports "brightness", "darkness", "motion", "difference", "range", and "difference range"
    - **brightness**: Triggers when the area becomes brighter than the threshold
    - **darkness**: Triggers when the area becomes darker than the threshold
    - **motion**: Triggers when the difference from the previous frame exceeds the threshold
    - **difference**: Triggers when the difference from the first frame exceeds the threshold (reset with 'r' key)
    - **range**: Maps brightness to a MIDI CC value
    - **difference range**: Maps difference from first frame to a MIDI CC value (reset with 'r' key)
  - **threshold**: Brightness value (0-255) that activates the trigger (brightness/darkness), or average pixel difference (0-255) for motion/difference detection
  - **min/max**: Brightness range (0-255) for range triggers, or difference range (0-255) for difference range triggers
  - **debounce** (optional): Per-trigger debounce time in seconds. When a trigger becomes invalid, it will wait this duration before sending Note OFF. Overrides global default.
  - **throttle** (optional): Per-trigger throttle time in seconds. After deactivation, the trigger will wait this duration before it can reactivate. Overrides global default.
  - **colour** / **color** (optional): Per-trigger display color in RGB. Accepts either `[r, g, b]` (inactive is auto-dimmed), or `[[inactive_r, inactive_g, inactive_b], [active_r, active_g, active_b]]` for explicit inactive/active colors.
  - **device** (optional): Per-trigger MIDI output device name. Overrides the global `device` for this trigger.
  - **midi**: MIDI message configuration
    - **note**: MIDI note number (0-127) or note name for brightness/darkness/motion/difference (e.g. `C`, `D#4`, `Eb2`). If no octave is provided, octave 4 is assumed (so `C` = middle C = 60).
      - For brightness/darkness/motion/difference, you can use either `note` + `velocity` **or** `cc` + `value`.
    - **velocity**: Note velocity for brightness/darkness/motion/difference (note mode only). Can be:
      - **Fixed velocity**: A number between 0-127 (e.g., `velocity: 100`)
      - **Variable velocity**: A dict with min/max mappings based on detected value:
        ```yaml
        velocity:
          min: [detected_value, velocity_value]  # e.g., [2, 80]
          max: [detected_value, velocity_value]  # e.g., [20, 127]
        ```
        The velocity will be interpolated between min and max based on the detected brightness/motion value.
        Values outside the range are clamped to min/max velocity.
    - **cc**: MIDI CC number (0-127) for range/difference range, or fixed CC triggers (brightness/darkness/motion/difference)
    - **value**: Fixed CC value (0-127) for brightness/darkness/motion/difference when using `cc`
    - **off_value** (optional): CC value sent on deactivation for fixed CC triggers
    - **channel**: MIDI channel (0-15)

### Debounce and Throttle Behavior

**Debounce** prevents triggers from deactivating too quickly:
- When a trigger condition becomes false, the trigger waits for the debounce duration before sending Note OFF
- If the trigger becomes valid again during the debounce period, Note OFF is never sent
- Useful for preventing flickering when a trigger oscillates around the threshold

**Throttle** prevents triggers from reactivating too quickly:
- After a trigger deactivates (sends Note OFF), it cannot reactivate for the throttle duration
- Even if the trigger condition becomes true during the throttle period, Note ON is not sent
- Useful for preventing rapid retriggering in noisy conditions

**Example Timeline:**
```
Time:     0s    1s    2s    3s    4s    5s    6s
Condition: ON   OFF   ON    ON    OFF   ON    ON
Debounce=1s, Throttle=2s:
MIDI:     ON         OFF              (blocked) ON
          ^          ^                          ^
          |          |                          |
      Immediate  Waits 1s              Waits 2s from OFF
```

### Arbitrary Shapes

You can define **arbitrary shapes** as an alternative to rectangular trigger areas. Use `shape` instead of `position` to create custom trigger regions.

**Shape Definition:**
- Use `shape` instead of `position` (they are mutually exclusive)
- Each point is defined as `[x, y]` in percentage coordinates (0-100)
- The bounding box is automatically calculated from the shape points

**Shape Types:**

**Single Pixel (1 point):**
```yaml
shape: [[50, 50]]  # Trigger on a single pixel at center
```

**Line (2 points):**
```yaml
shape: [[10, 10], [90, 90]]  # Diagonal line trigger
```

**Polygon (3+ points):**
```yaml
shape: 
  - [50, 20]   # Top point
  - [20, 80]   # Bottom left
  - [80, 80]   # Bottom right
# Creates a filled triangle trigger area
```

**How it works:**
- The shape is converted to a pixel mask
- Only pixels inside the shape are analyzed for brightness/motion/difference
- The bounding box is automatically calculated for efficient processing
- Works with all trigger types (brightness, darkness, motion, difference, range)

**Example Configuration:**
```yaml
- name: "Diamond Motion Detector"
  shape:           # Use shape instead of position
    - [50, 40]   # Top
    - [60, 50]   # Right
    - [50, 60]   # Bottom
    - [40, 50]   # Left
  type: "motion"
  threshold: 15
  midi:
    note: 72
    velocity: 100
    channel: 0
```

**Note:** You cannot use both `position` and `shape` in the same trigger - use one or the other.

### Variable Velocity

**Variable velocity** allows the MIDI note velocity to change dynamically based on the detected value (brightness, darkness, or motion).

**Configuration:**
```yaml
velocity:
  min: [detected_value, velocity_value]  # e.g., [2, 80]
  max: [detected_value, velocity_value]  # e.g., [20, 127]
```

**How it works:**
- When the detected value is at or below `min[0]`, velocity is set to `min[1]`
- When the detected value is at or above `max[0]`, velocity is set to `max[1]`
- For values in between, velocity is linearly interpolated
- Velocity is always clamped to the MIDI range (0-127)

**Example for motion trigger:**
```yaml
velocity:
  min: [2, 80]    # Subtle motion (2) -> soft velocity (80)
  max: [20, 127]  # Strong motion (20) -> loud velocity (127)
```
- If motion detected = 2 → velocity = 80
- If motion detected = 11 → velocity ≈ 104 (interpolated)
- If motion detected = 20 → velocity = 127
- If motion detected = 25 → velocity = 127 (clamped to max)

This is particularly useful for:
- **Motion triggers**: Louder notes for more vigorous movement
- **Brightness triggers**: Velocity matching light intensity
- **Darkness triggers**: Dynamic response to shadow depth

## Controls

- **q**: Quit the application
- **r**: Restart the video from the beginning (also resets the first frame for difference triggers)

## MIDI File Recording

The application automatically records all MIDI events to a `.midi` file while playing. This enables perfect audio-video synchronization when creating final audio renders.

### How It Works

1. **Automatic Recording**: All MIDI events sent during playback are simultaneously recorded to a file
2. **Video Frame-Based Timing**: Events are timestamped based on the video's frame position (not playback time), ensuring perfect sync even if playback is slow
3. **Single Loop Recording**: For looping videos, only the first loop is recorded (subsequent loops don't add to the file)
4. **Automatic Naming**: The MIDI file uses the same name as your YAML config (e.g., `myconfig.yaml` → `myconfig.midi`)
5. **Optional Channel Splits**: With `--split-midi-channels`, the app writes one file per note channel and a separate CC file (e.g., `myconfig-ch-01.midi`, `myconfig-ch-02.midi`, `myconfig-cc.midi`)
5. **Saved on Exit**: The MIDI file is automatically saved when you:
   - Press 'q' to quit
   - Press Ctrl+C to interrupt
   - Close the application window

### Timing Accuracy

**Important:** MIDI timing is based on **video frame position**, not playback time. This means:
- If your computer plays the video slowly (due to processing load), the MIDI file timing is **not affected**
- Timing is calculated as `current_frame_number / fps`, ensuring sample-accurate synchronization
- When you import the MIDI file into your DAW with the original video, they will be perfectly in sync

Example: A video at 30fps with an event at frame 15 will always be recorded at 0.5 seconds in the MIDI file, regardless of how long it took to actually play back that frame.

### Using the MIDI File

After recording, you can:
- Import the `.midi` file into your DAW alongside the video
- The timing will be perfectly synchronized with the video
- All MIDI events (notes, velocities, CCs) are preserved
- The file uses standard MIDI format and works with any DAW or MIDI software

### Example Workflow

```bash
# Run the application with your config
python video-midi-trigger.py myproject

# The app plays the video and shows: "MIDI recording: Will save to myproject.midi"
# Triggers activate during playback, sending MIDI in real-time
# Press 'q' to quit when done

# Result: myproject.midi file is created with all events
# Import both myproject.mp4 and myproject.midi into your DAW
# Perfect sync guaranteed!
```

## How it Works

1. The application loads the specified YAML configuration file
2. Opens the video file specified in the configuration
3. For each frame:
   - Analyzes the brightness in each trigger area
   - Detects motion by comparing frame differences (previous frame for "motion", first frame for "difference")
   - Sends MIDI Note On/Off for brightness/darkness/motion/difference triggers
   - **Records MIDI events to file with video-relative timestamps**
   - Sends MIDI CC values for range triggers (mapped from brightness) and difference range triggers (mapped from first frame difference)
4. Displays the video with visual overlays showing trigger areas:
   - Red rectangle: Inactive trigger
   - Green rectangle: Active trigger
5. **Saves the MIDI file when you quit the application**

## Requirements

- Python 3.7+
- OpenCV (opencv-python)
- PyYAML
- python-rtmidi
- NumPy
- mido (for MIDI file creation)

## MIDI Setup

The application will automatically:
- Connect to the first available MIDI port if one exists
- Create a virtual MIDI port named "Video-MIDI-Trigger" if no ports are available

You can use software like DAWs, synthesizers, or MIDI monitoring tools to receive the MIDI messages.

## Example

An example configuration file `road.yaml` is included in the repository. You'll need to update the `source` to point to an actual video file on your system (or set it to `"camera"`).
