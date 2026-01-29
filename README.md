# Video-MIDI-trigger

A Python application that triggers MIDI messages based on visual events in a video. Monitor specific areas of a video for brightness changes and send corresponding MIDI notes or CC values.

## Features

- Video playback with real-time trigger detection
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
python -m venv .venv
source .venv/bin/activate
pyenv local 3.9.18
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## Usage

Run the application with a configuration file name as an argument:

```bash
source .venv/bin/activate
python video-midi-trigger.py road
```

This will load the `road.yaml` configuration file.

## Configuration

Create a YAML configuration file (e.g., `road.yaml`) with the following structure:

```yaml
source: "path/to/your/video.mp4"

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
```

### Configuration Parameters

- **source**: Path to the video file (relative or absolute) or `"camera"` to use the webcam
- **camera** (optional): Settings applied when `source: "camera"`
  - **width**: Camera capture width (default 640)
  - **height**: Camera capture height (default 480)
  - **fps**: Target camera FPS (default 30)
- **debounce** (optional): Global default debounce time in seconds (default 0). Prevents triggers from deactivating too quickly.
- **throttle** (optional): Global default throttle time in seconds (default 0). Prevents triggers from reactivating too quickly.
- **Live reload**: The app watches the YAML file and reloads trigger values on change. Changing `device` or `source` requires a restart to take effect.
- **triggers**: List of trigger definitions
  - **name**: Descriptive name for the trigger
  - **position**: Location and size of the trigger area
    - **x, y**: Position as percentage of frame dimensions (0-100)
    - **width, height**: Size as percentage of frame dimensions (0-100)
  - **type**: Supports "brightness", "darkness", "motion", "difference", and "range"
    - **brightness**: Triggers when the area becomes brighter than the threshold
    - **darkness**: Triggers when the area becomes darker than the threshold
    - **motion**: Triggers when the difference from the previous frame exceeds the threshold
    - **difference**: Triggers when the difference from the first frame exceeds the threshold (reset with 'r' key)
    - **range**: Maps brightness to a MIDI CC value
  - **threshold**: Brightness value (0-255) that activates the trigger (brightness/darkness), or average pixel difference (0-255) for motion/difference detection
  - **min/max**: Brightness range (0-255) used to map CC values (range)
  - **debounce** (optional): Per-trigger debounce time in seconds. When a trigger becomes invalid, it will wait this duration before sending Note OFF. Overrides global default.
  - **throttle** (optional): Per-trigger throttle time in seconds. After deactivation, the trigger will wait this duration before it can reactivate. Overrides global default.
  - **midi**: MIDI message configuration
    - **note**: MIDI note number (0-127) for brightness/darkness/motion/difference
    - **velocity**: Note velocity for brightness/darkness/motion/difference. Can be:
      - **Fixed velocity**: A number between 0-127 (e.g., `velocity: 100`)
      - **Variable velocity**: A dict with min/max mappings based on detected value:
        ```yaml
        velocity:
          min: [detected_value, velocity_value]  # e.g., [2, 80]
          max: [detected_value, velocity_value]  # e.g., [20, 127]
        ```
        The velocity will be interpolated between min and max based on the detected brightness/motion value.
        Values outside the range are clamped to min/max velocity.
    - **cc**: MIDI CC number (0-127) for range
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
- **r**: Reset the first frame for difference triggers

## How it Works

1. The application loads the specified YAML configuration file
2. Opens the video file specified in the configuration
3. For each frame:
   - Analyzes the brightness in each trigger area
   - Detects motion by comparing frame differences (previous frame for "motion", first frame for "difference")
   - Sends MIDI Note On/Off for brightness/darkness/motion/difference triggers
   - Sends MIDI CC values for range triggers (mapped from min/max)
4. Displays the video with visual overlays showing trigger areas:
   - Red rectangle: Inactive trigger
   - Green rectangle: Active trigger

## Requirements

- Python 3.7+
- OpenCV (opencv-python)
- PyYAML
- python-rtmidi
- NumPy

## MIDI Setup

The application will automatically:
- Connect to the first available MIDI port if one exists
- Create a virtual MIDI port named "Video-MIDI-Trigger" if no ports are available

You can use software like DAWs, synthesizers, or MIDI monitoring tools to receive the MIDI messages.

## Example

An example configuration file `road.yaml` is included in the repository. You'll need to update the `source` to point to an actual video file on your system (or set it to `"camera"`).
