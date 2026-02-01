#!/usr/bin/env python3
"""
Demonstration of the YAML format improvements.
Shows before/after comparison of shape coordinate formatting.
"""

import tempfile
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq


def demonstrate_yaml_format():
    """Demonstrate the improved YAML format for shape coordinates."""
    
    print("=" * 70)
    print("YAML Format Comparison: Before vs After")
    print("=" * 70)
    
    # Sample trigger data
    trigger_data = {
        'source': 'camera',
        'triggers': [
            {
                'name': 'Test Shape Trigger',
                'shape': [
                    [38.2, 60.6],
                    [47.9, 54.1],
                    [61.7, 57.2],
                    [59.6, 68.2],
                    [45.7, 79.0]
                ],
                'type': 'brightness',
                'threshold': 150,
                'midi': {
                    'note': 60,
                    'velocity': 100,
                    'channel': 0
                }
            }
        ]
    }
    
    # Create temp file for BEFORE (without flow style)
    print("\n" + "─" * 70)
    print("BEFORE (Nested List Format - Old Way):")
    print("─" * 70)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path_before = f.name
    
    yaml_before = YAML()
    yaml_before.default_flow_style = False
    
    with open(temp_path_before, 'w') as f:
        yaml_before.dump(trigger_data, f)
    
    with open(temp_path_before, 'r') as f:
        content_before = f.read()
    
    print(content_before)
    
    # Create temp file for AFTER (with flow style)
    print("\n" + "─" * 70)
    print("AFTER (Flow Style Format - New Way):")
    print("─" * 70)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path_after = f.name
    
    yaml_after = YAML()
    yaml_after.default_flow_style = False
    
    # Apply flow style to shape coordinates
    for trigger in trigger_data['triggers']:
        if 'shape' in trigger and trigger['shape']:
            for i, point in enumerate(trigger['shape']):
                if isinstance(point, list):
                    if not isinstance(point, CommentedSeq):
                        point_seq = CommentedSeq(point)
                    else:
                        point_seq = point
                    point_seq.fa.set_flow_style()
                    trigger['shape'][i] = point_seq
    
    with open(temp_path_after, 'w') as f:
        yaml_after.dump(trigger_data, f)
    
    with open(temp_path_after, 'r') as f:
        content_after = f.read()
    
    print(content_after)
    
    # Comparison
    print("\n" + "=" * 70)
    print("KEY DIFFERENCES:")
    print("=" * 70)
    
    print("\n✗ BEFORE (nested format):")
    print("  shape:")
    print("  - - 38.2")
    print("    - 60.6")
    print("  - - 47.9")
    print("    - 54.1")
    
    print("\n✓ AFTER (flow style format):")
    print("  shape:")
    print("  - [38.2, 60.6]")
    print("  - [47.9, 54.1]")
    print("  - [61.7, 57.2]")
    print("  - [59.6, 68.2]")
    print("  - [45.7, 79.0]")
    
    print("\n" + "=" * 70)
    print("Benefits of the new format:")
    print("  • More compact and readable")
    print("  • Easier to edit manually")
    print("  • Clearer representation of [x, y] coordinate pairs")
    print("  • Less vertical space in the YAML file")
    print("=" * 70)
    
    # Cleanup
    import os
    os.unlink(temp_path_before)
    os.unlink(temp_path_after)


if __name__ == '__main__':
    demonstrate_yaml_format()
