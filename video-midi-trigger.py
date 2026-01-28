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
    
    def close(self):
        """Close MIDI connection."""
        del self.midi_out


class Trigger:
    """Represents a visual trigger area and its MIDI mapping."""
    
    # Color constants for visual feedback
    ACTIVE_COLOR = (0, 255, 0)    # Green
    INACTIVE_COLOR = (0, 0, 255)  # Red
    
    def __init__(self, config):
        self.name = config.get('name', 'Unnamed Trigger')
        
        # Validate required configuration keys
        required_keys = ['position', 'type', 'threshold', 'midi']
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
        self.threshold = config['threshold']
        self.midi_config = config['midi']
        
        # Validate MIDI parameters
        note = self.midi_config.get('note')
        velocity = self.midi_config.get('velocity', 100)
        channel = self.midi_config.get('channel', 0)
        
        if not (0 <= note <= 127):
            raise ValueError(f"MIDI note must be between 0 and 127, got {note} for trigger '{self.name}'")
        if not (0 <= velocity <= 127):
            raise ValueError(f"MIDI velocity must be between 0 and 127, got {velocity} for trigger '{self.name}'")
        if not (0 <= channel <= 15):
            raise ValueError(f"MIDI channel must be between 0 and 15, got {channel} for trigger '{self.name}'")
        
        self.active = False
        self.roi_coords = None  # Will be set when frame size is known
    
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
        roi = frame[y:y+h, x:x+w]
        
        if self.trigger_type == 'brightness':
            # Calculate average brightness in the ROI
            if gray_frame is not None:
                gray_roi = gray_frame[y:y+h, x:x+w]
            else:
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray_roi)
            return avg_brightness >= self.threshold
        
        if self.trigger_type == 'darkness':
            # Calculate average brightness in the ROI
            if gray_frame is not None:
                gray_roi = gray_frame[y:y+h, x:x+w]
            else:
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray_roi)
            return avg_brightness <= self.threshold
        
        return False
    
    def draw_on_frame(self, frame):
        """Draw the trigger area on the frame."""
        if self.roi_coords is None:
            return
        
        x, y, w, h = self.roi_coords
        
        # Choose color based on active state
        color = self.ACTIVE_COLOR if self.active else self.INACTIVE_COLOR
        
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
        
        # Load configuration
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        source = self.config['source']
        use_camera = isinstance(source, str) and source.lower() == "camera"
        self.video_path = source
        if not use_camera and not os.path.exists(self.video_path):
            raise FileNotFoundError(f"Video file not found: {self.video_path}")
        
        # Initialize triggers
        self.triggers = [Trigger(t) for t in self.config['triggers']]
        
        # Initialize MIDI controller
        device_name = self.config.get('device')
        self.midi = MIDIController(device_name=device_name)
        
        # Initialize video capture
        self.cap = cv2.VideoCapture(0 if use_camera else self.video_path)
        if not self.cap.isOpened():
            if use_camera:
                raise RuntimeError("Could not open camera.")
            raise RuntimeError(f"Could not open video: {self.video_path}")
        
        # Apply camera settings to improve performance (optional overrides in config)
        self.target_fps = None
        if use_camera:
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
        if use_camera and (not self.fps or self.fps <= 0) and self.target_fps:
            self.fps = self.target_fps
        
        # Setup trigger ROIs
        for trigger in self.triggers:
            trigger.setup_roi(self.frame_height, self.frame_width)
        
        if use_camera:
            print("Video: camera")
        else:
            print(f"Video: {self.video_path}")
        print(f"Resolution: {self.frame_width}x{self.frame_height}")
        print(f"FPS: {self.fps}")
        print(f"Triggers: {len(self.triggers)}")
    
    def process_frame(self, frame):
        """Process a single frame and check all triggers."""
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        for trigger in self.triggers:
            triggered = trigger.check_trigger(frame, gray_frame=gray_frame)
            
            # Handle state changes
            if triggered and not trigger.active:
                # Trigger activated
                trigger.active = True
                note = trigger.midi_config['note']
                velocity = trigger.midi_config['velocity']
                channel = trigger.midi_config['channel']
                self.midi.send_note_on(note, velocity, channel)
                print(f"✓ {trigger.name}: Note ON (Note: {note})")
            
            elif not triggered and trigger.active:
                # Trigger deactivated
                trigger.active = False
                note = trigger.midi_config['note']
                channel = trigger.midi_config['channel']
                self.midi.send_note_off(note, channel)
                print(f"✗ {trigger.name}: Note OFF (Note: {note})")
            
            # Draw trigger area on frame
            trigger.draw_on_frame(frame)
    
    def reset_triggers(self):
        """Reset all triggers and send MIDI Note Off messages."""
        for trigger in self.triggers:
            if trigger.active:
                trigger.active = False
                note = trigger.midi_config['note']
                channel = trigger.midi_config['channel']
                self.midi.send_note_off(note, channel)
    
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
                
                # Process triggers
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
            if trigger.active:
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
