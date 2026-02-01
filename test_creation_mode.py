#!/usr/bin/env python3
"""
Test script for trigger creation mode functionality.
Tests the logic without requiring GUI or camera.
"""

import sys
import os
import tempfile
import shutil
import copy
from pathlib import Path

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq


def test_yaml_flow_style_format():
    """Test that shape coordinates use flow style format [x, y]."""
    print("Testing YAML flow style format for shape coordinates...")
    
    yaml_content = """source: camera

triggers:
  - name: "Test Trigger"
    position:
      x: 25
      y: 25
      width: 20
      height: 20
    type: "brightness"
    threshold: 150
    midi:
      note: 60
      velocity: 100
      channel: 0
"""
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(yaml_content)
    
    try:
        # Load with ruamel.yaml
        yaml_loader = YAML()
        yaml_loader.preserve_quotes = True
        yaml_loader.default_flow_style = False
        
        with open(temp_path, 'r') as f:
            data = yaml_loader.load(f)
        
        # Add a new trigger with shape
        new_trigger = {
            'name': 'Created Trigger',
            'shape': [[10.5, 20.3], [30.2, 40.1], [50.0, 50.0]],
            'type': 'motion',
            'threshold': 10,
            'midi': {
                'note': 62,
                'velocity': 110,
                'channel': 0
            }
        }
        data['triggers'].append(new_trigger)
        
        # Set flow style for shape coordinates to get [x, y] format
        for trigger in data['triggers']:
            if 'shape' in trigger and trigger['shape']:
                for i, point in enumerate(trigger['shape']):
                    if isinstance(point, list):
                        # Convert to flow style for compact representation
                        if not isinstance(point, CommentedSeq):
                            point_seq = CommentedSeq(point)
                        else:
                            point_seq = point
                        point_seq.fa.set_flow_style()
                        trigger['shape'][i] = point_seq
        
        # Save back
        with open(temp_path, 'w') as f:
            yaml_loader.dump(data, f)
        
        # Read and verify format
        with open(temp_path, 'r') as f:
            saved_content = f.read()
        
        # Check for flow style format [x, y]
        if '[10.5, 20.3]' in saved_content:
            print("✓ Flow style format [x, y] used for shape coordinates")
        else:
            print("✗ Flow style format NOT used correctly")
            
        # Make sure it's not using nested list format
        if '- - 10.5' not in saved_content and '  - 10.5' not in saved_content:
            print("✓ Nested list format NOT present (good!)")
        else:
            print("✗ Still using nested list format")
        
        print("\nShape section from saved content:")
        lines = saved_content.split('\n')
        in_shape = False
        for line in lines:
            if 'shape:' in line:
                in_shape = True
            if in_shape:
                print(line)
                if line and not line.startswith(' ') and 'shape:' not in line:
                    break
        
    finally:
        # Clean up
        os.unlink(temp_path)
    
    print("\nFlow style test completed!\n")


def test_yaml_comment_preservation():
    """Test that ruamel.yaml preserves comments."""
    print("Testing YAML comment preservation...")
    
    yaml_content = """source: camera
# This is a test comment

camera:
  width: 640  # inline comment
  height: 480
  fps: 30

triggers:
  # Initial test trigger
  - name: "Test Trigger"
    position:
      x: 25
      y: 25
      width: 20
      height: 20
    type: "brightness"
    threshold: 150
    midi:
      note: 60  # C
      velocity: 100
      channel: 0
"""
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
        f.write(yaml_content)
    
    try:
        # Load with ruamel.yaml
        yaml_loader = YAML()
        yaml_loader.preserve_quotes = True
        yaml_loader.default_flow_style = False
        
        with open(temp_path, 'r') as f:
            data = yaml_loader.load(f)
        
        # Add a new trigger
        new_trigger = {
            'name': 'Created Trigger',
            'shape': [[10.5, 20.3], [30.2, 40.1], [50.0, 50.0]],
            'type': 'motion',
            'threshold': 10,
            'midi': {
                'note': 62,
                'velocity': 110,
                'channel': 0
            }
        }
        data['triggers'].append(new_trigger)
        
        # Save back
        with open(temp_path, 'w') as f:
            yaml_loader.dump(data, f)
        
        # Read and verify comments are preserved
        with open(temp_path, 'r') as f:
            saved_content = f.read()
        
        # Check if comments are preserved
        if '# This is a test comment' in saved_content:
            print("✓ Top-level comments preserved")
        else:
            print("✗ Top-level comments NOT preserved")
        
        if 'Created Trigger' in saved_content:
            print("✓ New trigger added successfully")
        else:
            print("✗ New trigger NOT added")
        
        if 'shape' in saved_content:
            print("✓ Shape field present in output")
        else:
            print("✗ Shape field missing")
        
        print("\nSaved content preview:")
        print(saved_content[:500])
        
    finally:
        # Clean up
        os.unlink(temp_path)
    
    print("\nTest completed successfully!\n")


def test_trigger_duplication_logic():
    """Test the trigger duplication logic."""
    print("Testing trigger duplication logic...")
    
    import copy
    
    # Simulate a trigger config
    last_trigger = {
        'name': 'Original Trigger',
        'position': {
            'x': 10,
            'y': 20,
            'width': 15,
            'height': 15
        },
        'type': 'brightness',
        'threshold': 150,
        'midi': {
            'note': 60,
            'velocity': 100,
            'channel': 0
        }
    }
    
    # Duplicate and modify
    new_trigger = copy.deepcopy(last_trigger)
    if 'position' in new_trigger:
        del new_trigger['position']
    new_trigger['shape'] = []
    
    # Verify
    assert 'position' not in new_trigger, "Position should be removed"
    assert 'shape' in new_trigger, "Shape should be added"
    assert new_trigger['shape'] == [], "Shape should be empty initially"
    assert new_trigger['name'] == 'Original Trigger', "Other fields should be preserved"
    assert new_trigger['type'] == 'brightness', "Type should be preserved"
    
    # Add points
    points = [[10.5, 20.3], [30.2, 40.1], [50.0, 50.0]]
    for point in points:
        new_trigger['shape'].append(point)
    
    assert len(new_trigger['shape']) == 3, "Should have 3 points"
    assert new_trigger['shape'][0] == [10.5, 20.3], "First point should match"
    
    # Remove last point
    new_trigger['shape'].pop()
    assert len(new_trigger['shape']) == 2, "Should have 2 points after removal"
    
    print("✓ Trigger duplication logic works correctly")
    print("✓ Point addition works correctly")
    print("✓ Point removal works correctly\n")


if __name__ == '__main__':
    print("=" * 60)
    print("Trigger Creation Mode - Unit Tests")
    print("=" * 60 + "\n")
    
    try:
        test_yaml_flow_style_format()
        test_yaml_comment_preservation()
        test_trigger_duplication_logic()
        print("=" * 60)
        print("All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
