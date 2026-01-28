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
from pathlib import Path


class MIDIController:
    """Handles MIDI output."""
    
    def __init__(self):
        self.midi_out = rtmidi.MidiOut()
        available_ports = self.midi_out.get_ports()
        
        # Try to open a port, create virtual port if none available
        if available_ports:
            self.midi_out.open_port(0)
            print(f"MIDI: Connected to {available_ports[0]}")
        else:
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
    
    def __init__(self, config):
        self.name = config.get('name', 'Unnamed Trigger')
        self.position = config['position']
        self.trigger_type = config['type']
        self.threshold = config['threshold']
        self.midi_config = config['midi']
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
        
        self.roi_coords = (x, y, w, h)
    
    def check_trigger(self, frame):
        """Check if the trigger condition is met."""
        if self.roi_coords is None:
            return False
        
        x, y, w, h = self.roi_coords
        roi = frame[y:y+h, x:x+w]
        
        if self.trigger_type == 'brightness':
            # Calculate average brightness in the ROI
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray_roi)
            return avg_brightness >= self.threshold
        
        return False
    
    def draw_on_frame(self, frame):
        """Draw the trigger area on the frame."""
        if self.roi_coords is None:
            return
        
        x, y, w, h = self.roi_coords
        
        # Choose color based on active state
        color = (0, 255, 0) if self.active else (0, 0, 255)
        
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
        
        self.video_path = self.config['video_path']
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"Video file not found: {self.video_path}")
        
        # Initialize triggers
        self.triggers = [Trigger(t) for t in self.config['triggers']]
        
        # Initialize MIDI controller
        self.midi = MIDIController()
        
        # Initialize video capture
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open video: {self.video_path}")
        
        # Get video properties
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # Setup trigger ROIs
        for trigger in self.triggers:
            trigger.setup_roi(self.frame_height, self.frame_width)
        
        print(f"Video: {self.video_path}")
        print(f"Resolution: {self.frame_width}x{self.frame_height}")
        print(f"FPS: {self.fps}")
        print(f"Triggers: {len(self.triggers)}")
    
    def process_frame(self, frame):
        """Process a single frame and check all triggers."""
        for trigger in self.triggers:
            triggered = trigger.check_trigger(frame)
            
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
    
    def run(self):
        """Main loop to play video and process triggers."""
        print("\nStarting video playback...")
        print("Press 'q' to quit, 'r' to restart video\n")
        
        # Calculate delay between frames (in milliseconds)
        delay = int(1000 / self.fps) if self.fps > 0 else 30
        
        try:
            while True:
                ret, frame = self.cap.read()
                
                if not ret:
                    # Video ended, restart from beginning
                    print("Video ended, restarting...")
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # Process triggers
                self.process_frame(frame)
                
                # Display frame
                cv2.imshow('Video-MIDI Trigger', frame)
                
                # Handle keyboard input
                key = cv2.waitKey(delay) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    print("Restarting video...")
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
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
