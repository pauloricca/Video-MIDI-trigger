#!/usr/bin/env python3
"""
Video-MIDI Trigger
A Python application that triggers MIDI messages based on visual events in a video.
"""

import sys
import yaml
import cv2
import numpy as np
import rtmidi
import os
import time
from pathlib import Path


class MIDIController:
    """Handles MIDI output."""
    
    def __init__(self, device_name=None):
        self.midi_out = rtmidi.MidiOut()
        available_ports = self.midi_out.get_ports()
        
        if available_ports:
            print("MIDI: Available output devices:")
            for i, name in enumerate(available_ports):
                print(f"  [{i}] {name}")
        else:
            print("MIDI: No output devices found.")
        
        # Try to open a port, create virtual port if none available
        if available_ports:
            port_index = 0
            if device_name:
                match_index = None
                for i, name in enumerate(available_ports):
                    if name == device_name:
                        match_index = i
                        break
                if match_index is None:
                    for i, name in enumerate(available_ports):
                        if name.lower() == device_name.lower():
                            match_index = i
                            break
                if match_index is None:
                    raise ValueError(
                        f"MIDI device '{device_name}' not found. "
                        f"Available devices: {available_ports}"
                    )
                port_index = match_index
            
            self.midi_out.open_port(port_index)
            print(f"MIDI: Connected to {available_ports[port_index]}")
        else:
            if device_name:
                raise ValueError(f"MIDI device '{device_name}' not found (no output devices available).")
            self.midi_out.open_virtual_port("Video-MIDI-Trigger")
            print("MIDI: Created virtual MIDI port 'Video-MIDI-Trigger'")
    
    def send_note_on(self, note, velocity=100, channel=0):
        """Send a MIDI Note On message."""
        message = [0x90 | channel, note, velocity]
        self.midi_out.send_message(message)
    
    def send_note_off(self, note, channel=0):
        """Send a MIDI Note Off message."""
        message = [0x80 | channel, note, 0]
        self.midi_out.send_message(message)

    def send_cc(self, cc, value, channel=0):
        """Send a MIDI Control Change message."""
        message = [0xB0 | channel, cc, value]
        self.midi_out.send_message(message)
    
    def close(self):
        """Close MIDI connection."""
        del self.midi_out


class Trigger:
    """Represents a visual trigger area and its MIDI mapping."""
    
    # Color constants for visual feedback
    ACTIVE_COLOR = (0, 255, 0)    # Green
    INACTIVE_COLOR = (0, 0, 255)  # Red
    
    def __init__(self, config, global_defaults=None):
        self.name = config.get('name', 'Unnamed Trigger')
        
        # Validate required configuration keys
        required_keys = ['position', 'type', 'midi']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration key '{key}' in trigger '{self.name}'")
        
        self.position = config['position']
        
        # Validate position percentages
        for key in ['x', 'y', 'width', 'height']:
            if key not in self.position:
                raise ValueError(f"Missing '{key}' in position for trigger '{self.name}'")
            value = self.position[key]
            if not (0 <= value <= 100):
                raise ValueError(f"Position '{key}' must be between 0 and 100, got {value} for trigger '{self.name}'")
        
        self.trigger_type = config['type']
        self.threshold = config.get('threshold')
        self.range_min = config.get('min')
        self.range_max = config.get('max')
        self.midi_config = config['midi']
        
        # Load debounce and throttle parameters (per-trigger or global defaults)
        global_defaults = global_defaults or {}
        self.debounce = config.get('debounce', global_defaults.get('debounce', 0.0))
        self.throttle = config.get('throttle', global_defaults.get('throttle', 0.0))
        
        # Validate debounce and throttle
        if self.debounce < 0:
            raise ValueError(f"Debounce must be >= 0, got {self.debounce} for trigger '{self.name}'")
        if self.throttle < 0:
            raise ValueError(f"Throttle must be >= 0, got {self.throttle} for trigger '{self.name}'")
        
        # Validate trigger parameters
        if self.trigger_type in ('brightness', 'darkness', 'motion'):
            if self.threshold is None:
                raise ValueError(f"Missing 'threshold' for trigger '{self.name}'")
            if not (0 <= self.threshold <= 255):
                raise ValueError(f"Threshold must be between 0 and 255 for trigger '{self.name}'")
        elif self.trigger_type == 'range':
            if self.range_min is None or self.range_max is None:
                raise ValueError(f"Missing 'min'/'max' for trigger '{self.name}'")
            if not (0 <= self.range_min <= 255) or not (0 <= self.range_max <= 255):
                raise ValueError(f"Range min/max must be between 0 and 255 for trigger '{self.name}'")
        else:
            raise ValueError(f"Unknown trigger type '{self.trigger_type}' in trigger '{self.name}'")
        
        # Validate MIDI parameters
        channel = self.midi_config.get('channel', 0)
        if not (0 <= channel <= 15):
            raise ValueError(f"MIDI channel must be between 0 and 15, got {channel} for trigger '{self.name}'")
        
        if self.trigger_type in ('brightness', 'darkness', 'motion'):
            note = self.midi_config.get('note')
            velocity_config = self.midi_config.get('velocity', 100)
            if note is None:
                raise ValueError(f"Missing MIDI note for trigger '{self.name}'")
            if not (0 <= note <= 127):
                raise ValueError(f"MIDI note must be between 0 and 127, got {note} for trigger '{self.name}'")
            
            # Validate velocity - can be a number or a dict with min/max
            if isinstance(velocity_config, dict):
                # Variable velocity mode
                if 'min' not in velocity_config or 'max' not in velocity_config:
                    raise ValueError(f"Variable velocity must have 'min' and 'max' for trigger '{self.name}'")
                
                vel_min = velocity_config['min']
                vel_max = velocity_config['max']
                
                if not isinstance(vel_min, (list, tuple)) or len(vel_min) != 2:
                    raise ValueError(f"Velocity min must be [detected_value, velocity] for trigger '{self.name}'")
                if not isinstance(vel_max, (list, tuple)) or len(vel_max) != 2:
                    raise ValueError(f"Velocity max must be [detected_value, velocity] for trigger '{self.name}'")
                
                # Validate velocity values are in range
                if not (0 <= vel_min[1] <= 127):
                    raise ValueError(f"Velocity min value must be between 0 and 127, got {vel_min[1]} for trigger '{self.name}'")
                if not (0 <= vel_max[1] <= 127):
                    raise ValueError(f"Velocity max value must be between 0 and 127, got {vel_max[1]} for trigger '{self.name}'")
                
                # Store variable velocity configuration
                self.velocity_mode = 'variable'
                self.velocity_min_detected = vel_min[0]
                self.velocity_min_value = vel_min[1]
                self.velocity_max_detected = vel_max[0]
                self.velocity_max_value = vel_max[1]
            else:
                # Fixed velocity mode
                if not (0 <= velocity_config <= 127):
                    raise ValueError(f"MIDI velocity must be between 0 and 127, got {velocity_config} for trigger '{self.name}'")
                self.velocity_mode = 'fixed'
                self.velocity_fixed = velocity_config
        elif self.trigger_type == 'range':
            cc = self.midi_config.get('cc')
            if cc is None:
                raise ValueError(f"Missing MIDI CC for trigger '{self.name}'")
            if not (0 <= cc <= 127):
                raise ValueError(f"MIDI CC must be between 0 and 127, got {cc} for trigger '{self.name}'")
        
        self.active = False
        self.last_cc_value = None
        self.range_level = 0.0
        self.roi_coords = None  # Will be set when frame size is known
        self.previous_roi = None  # For motion detection
        self.detected_value = 0.0  # Store the last detected value for variable velocity
        
        # Timing state for debounce and throttle
        self.became_invalid_time = None  # Time when trigger condition became false
        self.last_deactivated_time = None  # Time when trigger was actually deactivated (sent Note OFF)

    def _avg_brightness(self, frame, gray_frame=None):
        x, y, w, h = self.roi_coords
        if gray_frame is not None:
            gray_roi = gray_frame[y:y+h, x:x+w]
        else:
            roi = frame[y:y+h, x:x+w]
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray_roi))
    
    def setup_roi(self, frame_height, frame_width):
        """Calculate the region of interest coordinates based on frame size."""
        x_percent = self.position['x']
        y_percent = self.position['y']
        w_percent = self.position['width']
        h_percent = self.position['height']
        
        # Convert percentages to pixel coordinates
        x = int(frame_width * x_percent / 100)
        y = int(frame_height * y_percent / 100)
        w = int(frame_width * w_percent / 100)
        h = int(frame_height * h_percent / 100)
        
        # Validate ROI bounds
        if w <= 0 or h <= 0:
            raise ValueError(f"Invalid ROI size for trigger '{self.name}': width={w}, height={h}")
        
        # Ensure ROI stays within frame boundaries
        if x + w > frame_width:
            w = frame_width - x
        if y + h > frame_height:
            h = frame_height - y
        
        if x < 0 or y < 0 or x >= frame_width or y >= frame_height:
            raise ValueError(f"Invalid ROI position for trigger '{self.name}': x={x}, y={y}")
        
        self.roi_coords = (x, y, w, h)
    
    def check_trigger(self, frame, gray_frame=None):
        """Check if the trigger condition is met."""
        if self.roi_coords is None:
            return False
        
        x, y, w, h = self.roi_coords
        
        if self.trigger_type == 'brightness':
            # Calculate average brightness in the ROI
            avg_brightness = self._avg_brightness(frame, gray_frame)
            self.detected_value = avg_brightness
            return avg_brightness >= self.threshold
        
        if self.trigger_type == 'darkness':
            # Calculate average brightness in the ROI
            avg_brightness = self._avg_brightness(frame, gray_frame)
            self.detected_value = avg_brightness
            return avg_brightness <= self.threshold
        
        if self.trigger_type == 'motion':
            # Calculate average difference between current and previous frame
            if gray_frame is not None:
                current_roi = gray_frame[y:y+h, x:x+w]
            else:
                roi = frame[y:y+h, x:x+w]
                current_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # If no previous frame, store current and return False
            if self.previous_roi is None:
                self.previous_roi = current_roi.copy()
                self.detected_value = 0.0
                return False
            
            # Calculate average absolute difference
            diff = cv2.absdiff(current_roi, self.previous_roi)
            avg_diff = float(np.mean(diff))
            
            # Update previous frame
            self.previous_roi = current_roi.copy()
            
            self.detected_value = avg_diff
            return avg_diff >= self.threshold
        
        if self.trigger_type == 'range':
            avg_brightness = self._avg_brightness(frame, gray_frame)
            low = min(self.range_min, self.range_max)
            high = max(self.range_min, self.range_max)
            clipped = min(max(avg_brightness, low), high)
            if self.range_min == self.range_max:
                self.range_level = 0.0
            else:
                self.range_level = (clipped - self.range_min) / (self.range_max - self.range_min)
            value = int(round(self.range_level * 127))
            return value
        
        return False
    
    def get_velocity(self):
        """Calculate velocity based on detected value and velocity configuration."""
        if self.velocity_mode == 'fixed':
            return self.velocity_fixed
        
        # Variable velocity mode - interpolate between min and max
        detected = self.detected_value
        
        # Clamp detected value to min/max range
        if detected <= self.velocity_min_detected:
            return self.velocity_min_value
        if detected >= self.velocity_max_detected:
            return self.velocity_max_value
        
        # Linear interpolation
        detected_range = self.velocity_max_detected - self.velocity_min_detected
        velocity_range = self.velocity_max_value - self.velocity_min_value
        
        if detected_range == 0:
            return self.velocity_min_value
        
        ratio = (detected - self.velocity_min_detected) / detected_range
        velocity = self.velocity_min_value + (ratio * velocity_range)
        
        # Clamp to MIDI velocity range and convert to int
        return int(max(0, min(127, round(velocity))))
    
    def draw_on_frame(self, frame):
        """Draw the trigger area on the frame."""
        if self.roi_coords is None:
            return
        
        x, y, w, h = self.roi_coords
        
        # Choose color based on active state
        color = self.ACTIVE_COLOR if self.active else self.INACTIVE_COLOR

        if self.trigger_type == 'range':
            # Filled vertical bar (transparent blue)
            fill_h = int(h * self.range_level)
            if fill_h > 0:
                overlay = frame.copy()
                fill_y = y + (h - fill_h)
                cv2.rectangle(overlay, (x, fill_y), (x + w, y + h), (255, 255, 255), -1)
                cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)
            color = (255, 255, 255)
        
        # Draw rectangle
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        # Draw label
        label = f"{self.name}"
        cv2.putText(frame, label, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, color, 1, cv2.LINE_AA)


class VideoMIDITrigger:
    """Main application class."""
    
    def __init__(self, config_name):
        self.config_path = Path(config_name)
        if not self.config_path.suffix:
            self.config_path = Path(f"{config_name}.yaml")
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        # Load configuration and initialize
        self.config_mtime = None
        self.config = None
        self.triggers = []
        self.target_fps = None
        self.use_camera = False
        self.video_path = None
        
        self._load_config()
        
        # Initialize MIDI controller (device changes require restart)
        device_name = self.config.get('device')
        self.midi = MIDIController(device_name=device_name)
        
        # Initialize video capture
        self._init_capture()
        
        # Setup trigger ROIs
        for trigger in self.triggers:
            trigger.setup_roi(self.frame_height, self.frame_width)
        
        if self.use_camera:
            print("Video: camera")
        else:
            print(f"Video: {self.video_path}")
        print(f"Resolution: {self.frame_width}x{self.frame_height}")
        print(f"FPS: {self.fps}")
        print(f"Triggers: {len(self.triggers)}")

    def _load_config(self):
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.config_mtime = self.config_path.stat().st_mtime
        
        source = self.config['source']
        self.use_camera = isinstance(source, str) and source.lower() == "camera"
        self.video_path = source
        if not self.use_camera and not os.path.exists(self.video_path):
            raise FileNotFoundError(f"Video file not found: {self.video_path}")
        
        # Extract global defaults for triggers
        global_defaults = {
            'debounce': self.config.get('debounce', 0.0),
            'throttle': self.config.get('throttle', 0.0)
        }
        
        # Rebuild triggers
        self.triggers = [Trigger(t, global_defaults=global_defaults) for t in self.config['triggers']]

    def _init_capture(self):
        self.cap = cv2.VideoCapture(0 if self.use_camera else self.video_path)
        if not self.cap.isOpened():
            if self.use_camera:
                raise RuntimeError("Could not open camera.")
            raise RuntimeError(f"Could not open video: {self.video_path}")
        
        # Apply camera settings to improve performance (optional overrides in config)
        self.target_fps = None
        if self.use_camera:
            camera_cfg = self.config.get('camera', {})
            width = camera_cfg.get('width', 640)
            height = camera_cfg.get('height', 480)
            fps = camera_cfg.get('fps', 30)
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            self.target_fps = fps
        
        # Get video properties
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.use_camera and (not self.fps or self.fps <= 0) and self.target_fps:
            self.fps = self.target_fps

    def _reload_if_changed(self):
        try:
            new_mtime = self.config_path.stat().st_mtime
        except FileNotFoundError:
            return
        
        if self.config_mtime is not None and new_mtime <= self.config_mtime:
            return
        
        previous_source = self.config.get('source') if self.config else None
        previous_device = self.config.get('device') if self.config else None
        
        # Save timing state from existing triggers before reload
        timing_state = {}
        for trigger in self.triggers:
            timing_state[trigger.name] = {
                'became_invalid_time': trigger.became_invalid_time,
                'last_deactivated_time': trigger.last_deactivated_time,
                'active': trigger.active
            }
        
        self._load_config()
        
        # Restore timing state to triggers with matching names
        for trigger in self.triggers:
            if trigger.name in timing_state:
                state = timing_state[trigger.name]
                trigger.became_invalid_time = state['became_invalid_time']
                trigger.last_deactivated_time = state['last_deactivated_time']
                trigger.active = state['active']
        
        # Warn if device/source changed (requires restart to take effect)
        if self.config.get('device') != previous_device:
            print("Config reloaded: device change detected (restart required to apply).")
        if self.config.get('source') != previous_source:
            print("Config reloaded: source change detected (restart required to apply).")
        
        # Re-setup trigger ROIs with current frame size
        for trigger in self.triggers:
            trigger.setup_roi(self.frame_height, self.frame_width)
        
        print("Config reloaded.")
    
    def process_frame(self, frame):
        """Process a single frame and check all triggers."""
        current_time = time.time()
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        for trigger in self.triggers:
            if trigger.trigger_type == 'range':
                value = trigger.check_trigger(frame, gray_frame=gray_frame)
                if value != trigger.last_cc_value:
                    trigger.last_cc_value = value
                    cc = trigger.midi_config['cc']
                    channel = trigger.midi_config.get('channel', 0)
                    self.midi.send_cc(cc, value, channel)
                trigger.active = True
            else:
                triggered = trigger.check_trigger(frame, gray_frame=gray_frame)
                
                # Handle state changes with debounce and throttle logic
                if triggered:
                    # Reset "became invalid" time since trigger is valid again
                    trigger.became_invalid_time = None
                    
                    if not trigger.active:
                        # Check throttle: ensure enough time has passed since last deactivation
                        can_activate = True
                        if trigger.throttle > 0 and trigger.last_deactivated_time is not None:
                            time_since_deactivation = current_time - trigger.last_deactivated_time
                            can_activate = time_since_deactivation >= trigger.throttle
                        
                        if can_activate:
                            # Trigger activated
                            trigger.active = True
                            note = trigger.midi_config['note']
                            velocity = trigger.get_velocity()
                            channel = trigger.midi_config['channel']
                            self.midi.send_note_on(note, velocity, channel)
                            print(f"✓ {trigger.name}: Note ON (Note: {note}, Velocity: {velocity})")
                
                else:
                    # Trigger condition is not met
                    # Record when the trigger became invalid (for debounce)
                    if trigger.became_invalid_time is None and trigger.active:
                        trigger.became_invalid_time = current_time
                    
                    if trigger.active:
                        # Check debounce: ensure trigger has been invalid for debounce duration
                        should_deactivate = True
                        if trigger.debounce > 0 and trigger.became_invalid_time is not None:
                            time_since_invalid = current_time - trigger.became_invalid_time
                            should_deactivate = time_since_invalid >= trigger.debounce
                        
                        if should_deactivate:
                            # Trigger deactivated
                            trigger.active = False
                            trigger.last_deactivated_time = current_time
                            note = trigger.midi_config['note']
                            channel = trigger.midi_config['channel']
                            self.midi.send_note_off(note, channel)
                            print(f"✗ {trigger.name}: Note OFF (Note: {note})")
            
            # Draw trigger area on frame
            trigger.draw_on_frame(frame)
    
    def reset_triggers(self):
        """Reset all triggers and send MIDI Note Off messages."""
        for trigger in self.triggers:
            if trigger.active and 'note' in trigger.midi_config:
                trigger.active = False
                note = trigger.midi_config['note']
                channel = trigger.midi_config['channel']
                self.midi.send_note_off(note, channel)
            # Reset motion detection state
            if trigger.trigger_type == 'motion':
                trigger.previous_roi = None
            # Reset timing state for debounce and throttle
            trigger.became_invalid_time = None
            trigger.last_deactivated_time = None
    
    def run(self):
        """Main loop to play video and process triggers."""
        print("\nStarting video playback...")
        print("Press 'q' to quit, 'r' to restart video\n")
        
        # Calculate delay between frames (in milliseconds)
        delay = int(1000 / self.fps) if self.fps > 0 else 1
        
        try:
            while True:
                loop_start = time.perf_counter()
                ret, frame = self.cap.read()
                
                if not ret:
                    # Video ended, reset triggers and restart from beginning
                    print("Video ended, restarting...")
                    self.reset_triggers()
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                if self.use_camera:
                    frame = cv2.flip(frame, 1)
                
                # Process triggers
                self._reload_if_changed()
                self.process_frame(frame)
                
                # Display frame
                cv2.imshow('Video-MIDI Trigger', frame)
                
                # Handle keyboard input
                elapsed_ms = (time.perf_counter() - loop_start) * 1000
                sleep_ms = max(1, int(delay - elapsed_ms))
                key = cv2.waitKey(sleep_ms) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    print("Restarting video...")
                    self.reset_triggers()
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        print("\nCleaning up...")
        
        # Send note off for any active triggers
        for trigger in self.triggers:
            if trigger.active and 'note' in trigger.midi_config:
                note = trigger.midi_config['note']
                channel = trigger.midi_config['channel']
                self.midi.send_note_off(note, channel)
        
        self.cap.release()
        cv2.destroyAllWindows()
        self.midi.close()
        print("Done.")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python video-midi-trigger.py <config_name>")
        print("Example: python video-midi-trigger.py road")
        sys.exit(1)
    
    config_name = sys.argv[1]
    
    try:
        app = VideoMIDITrigger(config_name)
        app.run()
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
