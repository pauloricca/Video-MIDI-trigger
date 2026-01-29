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

triggers:
  - name: "Top Left Trigger"
    position:
      x: 10          # X position in percentage (0-100)
      y: 10          # Y position in percentage (0-100)
      width: 5       # Width in percentage
      height: 5      # Height in percentage
    type: "brightness"
    threshold: 200   # Brightness threshold (0-255)
    midi:
      note: 60       # MIDI note number (0-127)
      velocity: 100  # Note velocity (0-127)
      channel: 0     # MIDI channel (0-15)
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
  - **type**: Supports "brightness", "darkness", "motion", and "range"
  - **threshold**: Brightness value (0-255) that activates the trigger (brightness/darkness), or average pixel difference (0-255) for motion detection
  - **min/max**: Brightness range (0-255) used to map CC values (range)
  - **debounce** (optional): Per-trigger debounce time in seconds. When a trigger becomes invalid, it will wait this duration before sending Note OFF. Overrides global default.
  - **throttle** (optional): Per-trigger throttle time in seconds. After deactivation, the trigger will wait this duration before it can reactivate. Overrides global default.
  - **midi**: MIDI message configuration
    - **note**: MIDI note number (0-127) for brightness/darkness/motion
    - **velocity**: Note velocity (0-127) for brightness/darkness/motion
    - **cc**: MIDI CC number (0-127) for range
    - **channel**: MIDI channel (0-15)

## Controls

- **q**: Quit the application
- **r**: Restart the video from the beginning

## How it Works

1. The application loads the specified YAML configuration file
2. Opens the video file specified in the configuration
3. For each frame:
   - Analyzes the brightness in each trigger area
   - Detects motion by comparing frame differences
   - Sends MIDI Note On/Off for brightness/darkness/motion triggers
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
